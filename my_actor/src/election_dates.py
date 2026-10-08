import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

from .utils.normalize_inputs import normalize_state

_CONSTANTS_DIR = Path(__file__).parent / "constants"

_STATE_LINK_PATTERN = re.compile(r"\[\[[^|\]]*\|([^\]]+)\]\]")
_DATA_CELL_PATTERN = re.compile(
    r'^\|\s*(?:rowspan="(?P<rowspan>\d+)"\s*)?'
    r'(?:data-sort-value="[^"]*"\s*)?'
    r"(?:\|\s*)?(?P<value>.*)$"
)


def get_election_dates(state: str, cycle: int) -> dict:
    """Return the Senate election dates for one state in a cycle.

    Reads the bundled constants file for that cycle; an existing file is treated
    as a complete snapshot, so a state missing from it raises without touching
    the network. Only a missing or unusable file triggers a live API fetch,
    which also rewrites the file.
    """
    state_name = normalize_state(state)
    if state_name is None:
        raise ValueError(f"invalid state: {state!r}")

    path = _CONSTANTS_DIR / f"election_dates_{cycle}.json"
    data = _load_election_dates_file(path)
    if data is None:
        try:
            data = _fetch_election_dates_from_api(cycle)
        except (requests.RequestException, RuntimeError) as exc:
            raise RuntimeError(
                f"couldn't get the election dates for {state_name} ({cycle}): {exc}"
            ) from exc
        path.write_text(json.dumps(data, indent=4) + "\n")

    if state_name not in data:
        raise RuntimeError(
            f"couldn't get the election dates for {state_name} ({cycle}): "
            f"no Senate race on the ballot that cycle"
        )
    return data[state_name]


def _load_election_dates_file(path: Path) -> dict | None:
    """Load a cycle's election-dates file, or None if missing, corrupt, or old-format."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or "updated_at" not in data:
        return None
    return data


def _fetch_election_dates_from_api(cycle: int) -> dict:
    """Fetch the election-dates table from Wikipedia and parse it into the cycle dict."""
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

    results: dict = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")
    }
    covered: dict[int, tuple[int, str]] = {}
    for row in rows[1:]:
        label = _parse_state_cell(row[0])
        state = normalize_state(label.removesuffix(" (special)"))
        if state is None or state in results:
            raise RuntimeError(f"unrecognized or duplicate state in table: {label!r}")
        aligned = _align_row(label, row[1:], covered)
        results[state] = {
            "senate": {
                "primary_date": _normalize_date(aligned[2]),
                "primary_runoff": _normalize_date(aligned[3]),
                "general_election": _normalize_date(aligned[4]),
            }
        }
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
