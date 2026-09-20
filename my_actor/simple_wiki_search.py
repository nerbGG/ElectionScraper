import json

import requests
from apify import Actor
from bs4 import BeautifulSoup

from .constants.us_state_office import check_office, check_state
from .get_election_dates import get_election_dates

IS_SPECIAL = False

HEADING_TAGS = ["h2", "h3", "h4", "h5", "h6"]
KEEP_HEADINGS = {"Nominee", "Declared", "Advanced to runoff"}


def get_title(office: str, year: int, state: str) -> str | None:
    """Build the Wikipedia article title for a race, or None if office/state is invalid."""
    state = check_state(state)
    if not state:
        return None
    office = check_office(office)
    if not office:
        return None
    return f"{year}_United_States_{office}_election_in_{state}"


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


def handle_simple_wiki(year, office, state) -> str:
    """Fetch and return the Wikipedia HTML extract for a given election race."""
    title = get_title(office, year, state)
    if title is None:
        raise ValueError(f"invalid state or office: state={state!r}, office={office!r}")

    try:
        dates = get_election_dates(state, year)
        Actor.log.info(f"{year} Senate election dates for {state}: {json.dumps(dates)}")
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
    result = parse_candidates(text)

    Actor.log.info(f"is_special: {IS_SPECIAL}")
    return result
