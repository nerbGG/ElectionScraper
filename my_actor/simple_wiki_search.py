import json
import re
from datetime import datetime
from pathlib import Path

import requests
from apify import Actor
from bs4 import BeautifulSoup

from .constants.us_state_office import ABB_TO_FULL_OFFICE, ABB_TO_FULL_STATE

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


_STATE_LINK_PATTERN = re.compile(r"\[\[[^|\]]*\|([^\]]+)\]\]")
_DATA_CELL_PATTERN = re.compile(
    r'^\|\s*(?:rowspan="(?P<rowspan>\d+)"\s*)?'
    r'(?:data-sort-value="[^"]*"\s*)?'
    r"(?:\|\s*)?(?P<value>.*)$"
)


def get_election_dates(cycle: int = 2026, refresh: bool = False) -> list[dict]:
    """Return primary/runoff/general dates for all Senate races in a cycle.

    By default reads the bundled constants file for that cycle and never touches
    the network; with refresh=True it fetches live from Wikipedia and rewrites
    the file.
    """
    path = Path(__file__).parent / "constants" / f"election_dates_{cycle}.json"
    if not refresh:
        if not path.is_file():
            raise RuntimeError(
                f"no cached election dates for cycle {cycle} ({path}); "
                f"run get_election_dates(cycle={cycle}, refresh=True) to fetch and save them"
            )
        rows = json.loads(path.read_text())
        if not isinstance(rows, list):
            raise RuntimeError(f"malformed election dates file: {path}")
        return rows

    rows = _fetch_election_dates_from_api(cycle)
    path.write_text(json.dumps(rows, indent=4) + "\n")
    return rows


def _fetch_election_dates_from_api(cycle: int) -> list[dict]:
    """Fetch the election-dates table from Wikipedia and parse it into rows."""
    headers = {"User-Agent": "ElectionScraper/0.1 (local dev script)"}
    url = "https://en.wikipedia.org/w/api.php"
    page = f"{cycle}_United_States_Senate_elections"

    res = requests.get(
        url,
        {"action": "parse", "format": "json", "prop": "tocdata", "page": page},
        headers=headers,
        timeout=30,
    )
    res.raise_for_status()
    sections = res.json().get("parse", {}).get("tocdata", {}).get("sections")
    if not sections:
        raise RuntimeError(f"unexpected API response for page {page!r}")
    section_index = next(
        (s["index"] for s in sections if s["line"] == "Election dates"), None
    )
    if section_index is None:
        raise RuntimeError(f"'Election dates' section not found on page {page!r}")

    res = requests.get(
        url,
        {
            "action": "parse",
            "format": "json",
            "prop": "wikitext",
            "page": page,
            "section": section_index,
        },
        headers=headers,
        timeout=30,
    )
    res.raise_for_status()
    wikitext = (res.json().get("parse", {}).get("wikitext") or {}).get("*")
    if wikitext is None:
        raise RuntimeError(
            f"unexpected API response for section {section_index} of {page}"
        )

    rows = _split_table_rows(wikitext)
    if len(rows) < 2:
        raise RuntimeError("no state rows found in election dates table")

    results = []
    covered: dict[int, tuple[int, str]] = {}
    for row in rows[1:]:
        state = _parse_state_cell(row[0])
        aligned = _align_row(state, row[1:], covered)
        results.append(
            {
                "state": state,
                "primary_date": _normalize_date(aligned[2]),
                "primary_runoff": _normalize_date(aligned[3]),
                "general_election": _normalize_date(aligned[4]),
            }
        )
    return results


def _split_table_rows(wikitext: str) -> list[list[str]]:
    """Split election-dates wikitext into rows of raw cell lines, dropping the table markup itself."""
    rows: list[list[str]] = []
    current: list[str] = []
    for line in wikitext.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("{|", "|}")):
            continue
        if stripped.startswith("|-"):
            if current:
                rows.append(current)
                current = []
            continue
        if stripped.startswith(("!", "|")):
            current.append(stripped)
    if current:
        rows.append(current)
    return rows


def _parse_state_cell(line: str) -> str:
    """Extract the state label from a `! [[link|Label]]` header cell."""
    match = _STATE_LINK_PATTERN.search(line)
    if match:
        return match.group(1).strip()
    return line.lstrip("!").strip()


def _parse_data_cell(line: str) -> tuple[int, str]:
    """Parse a `| data cell` line into (rowspan, value), tolerating missing spaces."""
    match = _DATA_CELL_PATTERN.match(line)
    if not match:
        raise RuntimeError(f"unparseable table cell: {line!r}")
    rowspan = int(match.group("rowspan") or 1)
    return rowspan, match.group("value").strip()


def _align_row(
    state: str, data_cells: list[str], covered: dict[int, tuple[int, str]]
) -> list[str]:
    """Place a row's visible cells into 6 columns, filling gaps left by rowspan cells above."""
    aligned = [state]
    cell_index = 0
    for col in range(1, 6):
        if col in covered:
            remaining, value = covered.pop(col)
            aligned.append(value)
            if remaining > 1:
                covered[col] = (remaining - 1, value)
        else:
            if cell_index >= len(data_cells):
                raise RuntimeError(f"table row {state!r} does not align to 6 columns")
            rowspan, value = _parse_data_cell(data_cells[cell_index])
            cell_index += 1
            aligned.append(value)
            if rowspan > 1:
                covered[col] = (rowspan - 1, value)
    if cell_index != len(data_cells):
        raise RuntimeError(f"table row {state!r} has leftover cells")
    return aligned


def _normalize_date(value: str) -> str | None:
    """Convert 'Month D, YYYY' to ISO format; 'N/A' or empty becomes None."""
    value = value.strip()
    if not value or value.upper() == "N/A":
        return None
    try:
        return datetime.strptime(value, "%B %d, %Y").strftime("%Y-%m-%d")  # noqa: DTZ007
    except ValueError as exc:
        raise RuntimeError(f"unparseable date: {value!r}") from exc
