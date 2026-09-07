import requests
from apify import Actor

from .us_state_office import ABB_TO_FULL_OFFICE, ABB_TO_FULL_STATE

IS_SPECIAL = False


def handle_simple_wiki(year, office, state) -> str:

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
    result = ""

    page = data["query"]["pages"]
    if page.get("-1") is not None:
        raise RuntimeError(f"article is missing: {title}")
    page_ids = list(page.keys())
    page_data = page[page_ids[0]]
    global IS_SPECIAL
    IS_SPECIAL = "special" in page_data["title"]
    result += page_data["extract"]
    Actor.log.info(f"is_special: {IS_SPECIAL}, extract: {result[:100]}")
    return result


def get_title(office: str, year: int, state: str) -> str | None:
    state = check_state(state)
    if not state:
        return None
    office = check_office(office)
    if not office:
        return None
    return f"{year}_United_States_{office}_election_in_{state}"


def check_state(state: str | None) -> str | None:
    if not isinstance(state, str):
        return None
    state = state.lower().strip()
    if not state:
        return None
    if len(state) == 2:
        return ABB_TO_FULL_STATE.get(state)
    return next((v for v in ABB_TO_FULL_STATE.values() if v.lower() == state), None)


def check_office(office: str) -> str | None:
    if not isinstance(office, str):
        return None
    office = office.lower().strip()
    if not office:
        return None
    if len(office) == 1:
        return ABB_TO_FULL_OFFICE.get(office)
    return next((v for v in ABB_TO_FULL_OFFICE.values() if v.lower() == office), None)
