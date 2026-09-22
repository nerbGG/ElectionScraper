import requests
from apify import Actor
from bs4 import BeautifulSoup

from .get_election_dates import get_election_dates
from .utils.normalize_inputs import (
    check_office,
    check_state,
    state_abb_to_full,
    state_full_to_abb,
)

IS_SPECIAL = False

HEADING_TAGS = ["h2", "h3", "h4", "h5", "h6"]
KEEP_HEADINGS = {"Nominee", "Declared", "Advanced to runoff"}


def get_title(office: str, year: int, state: str) -> tuple[str, str, str] | None:
    """Build the Wikipedia article title for a race, or None if office/state is invalid."""
    state = check_state(state)
    if not state:
        return None
    office = check_office(office)
    if not office:
        return None
    return f"{year}_United_States_{office}_election_in_{state}", state, office


def parse_candidates(extract: str) -> list[str]:
    """Extract candidate names from Declared/Advanced to runoff/Nominee headings, dropping the rest."""
    soup = BeautifulSoup(extract, "html.parser")
    candidates = []
    for heading in soup.find_all(HEADING_TAGS):
        if heading.get_text(strip=True) not in KEEP_HEADINGS:
            continue
        sibling = heading.find_next_sibling()
        # Only the immediately-following <ul> counts — an unmarked status change (e.g. a bolded
        # "Disqualified" paragraph with no proper heading) starts a new <ul>, ending this list.
        if sibling is None or sibling.name != "ul":
            continue
        for li in sibling.find_all("li", recursive=False):
            name = li.get_text().split(",")[0].strip()
            if name:
                candidates.append(name)
    return candidates


def handle_simple_wiki(year, office, state) -> dict:
    """Fetch a race's Wikipedia article and return the structured result.

    The result carries the parsed candidates, the state's election dates, the
    normalized state/office, and whether the race is a special election. If the
    dates lookup fails, the date fields are null and the candidates are still
    returned.
    """
    result = {}
    title_result = get_title(office, year, state)
    if title_result is None:
        raise ValueError(f"invalid state or office: state={state!r}, office={office!r}")
    title, clean_state, clean_office = title_result

    dates = None
    try:
        dates = get_election_dates(clean_state, year)
    except (ValueError, RuntimeError) as e:
        Actor.log.warning(f"couldn't get election dates: {e}")

    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "redirects": "1",
        "titles": title,
    }

    url = "https://en.wikipedia.org/w/api.php"
    headers = {"User-Agent": "ElectionScraper/0.1 (local dev script)"}
    res = requests.get(url, params, headers=headers)
    res.raise_for_status()
    data = res.json()

    page = data["query"]["pages"]
    if page.get("-1") is not None:
        raise RuntimeError(f"article is missing: {title}")
    page_ids = list(page.keys())
    page_data = page[page_ids[0]]

    global IS_SPECIAL
    IS_SPECIAL = "special" in page_data["title"]

    text = page_data["extract"]
    candidates = parse_candidates(text)

    result["year"] = year
    result["candidates"] = candidates
    result["office"] = clean_office
    if len(state) == 2:
        result["state"] = state.upper()
        result["state_label"] = state_abb_to_full(state)
    else:
        result["state"] = state_full_to_abb(clean_state)
        result["state_label"] = clean_state

    result["election_date"] = dates["senate"]["general_election"] if dates else None
    result["primary_date"] = dates["senate"]["primary_date"] if dates else None
    result["runoff_date"] = dates["senate"]["primary_runoff"] if dates else None
    result["is_special"] = IS_SPECIAL

    return result
