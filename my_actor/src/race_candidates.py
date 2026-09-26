from datetime import date

import requests
from apify import Actor

from .candidates import get_title, parse_candidates
from .election_dates import get_election_dates
from .models.candidate import Candidate
from .models.election import Election
from .utils.normalize_inputs import (
    state_abb_to_full,
    state_full_to_abb,
)

IS_SPECIAL = False


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def get_race(year: str, office: str, state: str) -> Election:
    """Fetch a race's Wikipedia article and return the structured result.

    The result carries the parsed candidates, the state's election dates, the
    normalized state/office, and whether the race is a special election. If the
    dates lookup fails, the date fields are null and the candidates are still
    returned. If no such race exists on Wikipedia at all (e.g. a state with no
    Senate seat up that cycle), the result carries an `error` message and empty
    candidates instead of raising — this is a normal, expected outcome, not a
    failure of the scrape itself.
    """
    title_result = get_title(office, year, state)
    if title_result is None:
        raise ValueError(f"invalid state or office: state={state!r}, office={office!r}")
    title, clean_state, clean_office = title_result

    state_code = ""
    state_label = ""

    if len(state) == 2:
        state_code = state.upper()
        state_label = state_abb_to_full(state)
    else:
        state_code = state_full_to_abb(clean_state)
        state_label = clean_state

    election = Election(
        year=year, office=clean_office, state=state_code, state_label=state_label
    )

    dates = None
    try:
        dates = get_election_dates(clean_state, year)
    except (ValueError, RuntimeError) as e:
        Actor.log.warning(f"couldn't get election dates: {e}")

    election.election_date = (
        _parse_date(dates["senate"]["general_election"]) if dates else None
    )
    election.primary_date = (
        _parse_date(dates["senate"]["primary_date"]) if dates else None
    )
    election.runoff_date = (
        _parse_date(dates["senate"]["primary_runoff"]) if dates else None
    )

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
        Actor.log.warning(f"no Wikipedia article for this race: {title}")
        election.error = f"No race found for {clean_office} in {state_label} ({year})"
        election.is_special = False
        return election

    page_ids = list(page.keys())
    page_data = page[page_ids[0]]

    text = page_data["extract"]
    candidates = parse_candidates(text)

    election.is_special = "special" in page_data["title"]
    election.candidates = [Candidate(**c) for c in candidates]

    return election
