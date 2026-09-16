import re

import requests
from apify import Actor

from .constants.us_state_office import ABB_TO_FULL_OFFICE, ABB_TO_FULL_STATE

IS_SPECIAL = False

HEADING_RE = re.compile(r"^(=+)\s*(.+?)\s*\1\s*$", re.MULTILINE)
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


def check_state(state: str | None) -> str | None:
    """Normalize a state abbreviation or name to its canonical form, or None if unrecognized."""
    if not isinstance(state, str):
        return None
    state = state.lower().strip()
    if not state:
        return None
    if len(state) == 2:
        return ABB_TO_FULL_STATE.get(state)
    return next((v for v in ABB_TO_FULL_STATE.values() if v.lower() == state), None)


def check_office(office: str) -> str | None:
    """Normalize an office abbreviation or name to its canonical form, or None if unrecognized."""
    if not isinstance(office, str):
        return None
    office = office.lower().strip()
    if not office:
        return None
    if len(office) == 1:
        return ABB_TO_FULL_OFFICE.get(office)
    return next((v for v in ABB_TO_FULL_OFFICE.values() if v.lower() == office), None)


def parse_candidates(extract: str) -> list[str]:
    """Extract candidate names from Declared/Advanced to runoff/Nominee headings, dropping the rest."""
    headings = list(HEADING_RE.finditer(extract))
    candidates = []
    for i, m in enumerate(headings):
        name = m.group(2).strip()
        if name not in KEEP_HEADINGS:
            continue
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(extract)
        for line in extract[start:end].strip().splitlines():
            line = line.strip()
            if line:
                candidates.append(line.split(",")[0].strip())
    return candidates


def handle_simple_wiki(year, office, state) -> str:
    """Fetch and return the Wikipedia plaintext extract for a given election race."""
    title = get_title(office, year, state)
    if title is None:
        raise ValueError(f"invalid state or office: state={state!r}, office={office!r}")
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": "1",
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
