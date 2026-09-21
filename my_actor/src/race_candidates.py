import requests
from apify import Actor
from bs4 import BeautifulSoup

from ..constants.us_state_office import ABB_TO_FULL_OFFICE, ABB_TO_FULL_STATE

IS_SPECIAL = False

HEADING_TAGS = ["h2", "h3", "h4", "h5", "h6"]
KEEP_HEADINGS = {"Nominee", "Declared", "Advanced to runoff", "Advanced to general"}
# Matches both "Third-parties and independents" (Michigan) and "Other third-party and
# independent candidates" (Ohio) — exact wording for this section varies by state.
THIRD_PARTY_SECTION_HINT = "third-part"


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


def split_name_description(text: str) -> tuple[str, str]:
    """Split on the first comma, or — if there's none — the first period not preceded by a
    capital letter, so middle-initial-style abbreviations ("Dan S. Sullivan") aren't split on."""
    if "," in text:
        name, _, description = text.partition(",")
        return name.strip(), description.strip()
    for i, char in enumerate(text):
        if char == "." and (i == 0 or not text[i - 1].isupper()):
            return text[:i].strip(), text[i + 1 :].strip()
    return text.strip(), ""


def append_candidates(candiates_list_elem, candidates: list[object], party: str):
    """Append each <li> in candiates_list_elem as a {name, description, party} dict."""
    for li in candiates_list_elem.find_all("li", recursive=False):
        name, description = split_name_description(li.get_text())
        if name:
            candidates.append(
                {"name": name, "description": description, "party": party}
            )


def parse_candidates(extract: str) -> list[object]:
    """Extract candidates (name, description, party) from Declared/Advanced to runoff/Nominee headings, dropping the rest."""
    soup = BeautifulSoup(extract, "html.parser")
    candidates = []
    for headerElem in soup.find_all(HEADING_TAGS):
        header = headerElem.get_text(strip=True)
        if headerElem.name == "h2":
            # Some states (e.g. Oklahoma) give Independents their own top-level h2, structured
            # just like a major party's "X primary" section, instead of nesting it as an h3
            # under a third-party wrapper section (e.g. Michigan's "Third-parties and independents").
            if header.endswith(" primary") or header == "Independents":
                party = (
                    None
                    if header == "Independents"
                    else header.removesuffix(" primary")
                )
                sub_header = headerElem.find_next_sibling(HEADING_TAGS)
                while sub_header.get_text(strip=True) not in KEEP_HEADINGS:
                    sub_header = sub_header.find_next_sibling(HEADING_TAGS)
                    continue
                candiates_list_elem = sub_header.find_next_sibling()
                append_candidates(candiates_list_elem, candidates, party)
            elif THIRD_PARTY_SECTION_HINT in header.lower() or header == "Candidates":
                # "Candidates" as a bare h2 covers Alaska's top-four blanket-primary format,
                # where every party (not just minor ones) is an h3 under one shared heading.
                for third_party_header_elem in headerElem.find_next_siblings(
                    HEADING_TAGS
                ):
                    third_party_header = third_party_header_elem.get_text(strip=True)
                    if (
                        third_party_header == "Independents"
                        or third_party_header.endswith(" Party")
                    ):
                        party = (
                            None
                            if third_party_header == "Independents"
                            else third_party_header
                        )
                        sub_header = third_party_header_elem.find_next_sibling(
                            HEADING_TAGS
                        )
                        # Stop at the next h2/h3 — that's a different section, meaning this
                        # party has no Nominee/Declared/Advanced to runoff heading of its own.
                        while (
                            sub_header is not None
                            and sub_header.name not in ("h2", "h3")
                            and sub_header.get_text(strip=True) not in KEEP_HEADINGS
                        ):
                            sub_header = sub_header.find_next_sibling(HEADING_TAGS)
                            continue
                        if sub_header is None or sub_header.name in ("h2", "h3"):
                            continue
                        candiates_list_elem = sub_header.find_next_sibling()
                        append_candidates(candiates_list_elem, candidates, party)
            elif header == "Write-in Candidates":
                # No Nominee/Declared h4 here — "Candidates" h3 is followed directly by the
                # <ul>, unlike every other section (confirmed live on West Virginia's page).
                sub_header = headerElem.find_next_sibling(HEADING_TAGS)
                if sub_header is not None:
                    candiates_list_elem = sub_header.find_next_sibling()
                    if (
                        candiates_list_elem is not None
                        and candiates_list_elem.name == "ul"
                    ):
                        append_candidates(candiates_list_elem, candidates, "Write in")
    return candidates


def get_race_candidates(year: str, office: str, state: str) -> list[str]:
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
