from bs4 import BeautifulSoup

from .constants.us_state_office import ALL_OFFICES_SUPPORTED
from .utils.normalize_inputs import (
    normalize_office,
    normalize_state,
)

HEADING_TAGS = ["h2", "h3", "h4", "h5", "h6"]
KEEP_HEADINGS = {"Nominee", "Declared", "Advanced to runoff", "Advanced to general"}
# Matches both "Third-parties and independents" (Michigan) and "Other third-party and
# independent candidates" (Ohio) — exact wording for this section varies by state.
THIRD_PARTY_SECTION_HINT = "third-part"


def get_title(office: str, year: int, state: str) -> tuple[str, str, str] | None:
    """Build the Wikipedia article title for a race, or None if office/state is invalid."""
    state_name = normalize_state(state)
    if not state_name:
        return None
    office_name = normalize_office(office)
    if not office_name:
        return None
    title_string = ""

    if office == ALL_OFFICES_SUPPORTED["GOVERNOR"]:
        title_string = f"{year}_{state_name}_gubernatorial_election"
    else:
        title_string = f"{year}_United_States_{office_name}_election_in_{state_name}"
    return title_string, state_name, office_name


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


def reached_another_party(tag) -> bool:
    """True if `tag` marks a real party-section boundary we've wandered into.
    h4+ status headings (e.g. "Eliminated in primary", "Withdrew after nomination") can
    coincidentally contain boundary-like wording and must not count — only h2/h3 can be a
    boundary. The suffix checked is level-specific: "... primary"/"... convention" boundaries
    only ever appear at h2 in practice, while "... Party"/"Independents" boundaries (the
    third-party wrapper's own sub-headings) only ever appear at h3 — a sub-heading like
    "Campaign and convention" (h3, nested under a "... convention" h2) must not be mistaken
    for another h2-level boundary.
    """
    header_text = tag.get_text(strip=True)
    if tag.name == "h2":
        return (
            header_text.endswith((" primary", " convention"))
            or header_text == "Independents"
        )
    if tag.name == "h3":
        return header_text.endswith(" Party") or header_text == "Independents"
    return False


def normalize_party(raw_label: str) -> str:
    """Clean up a party label parsed from heading text. Republican/Democratic headings can
    carry extra qualifier words (e.g. "Special Republican primary", "Democratic nominating
    convention") that aren't part of the party name — normalize those two to their canonical
    name. Leave any other party's label as-is (the "text before party/primary/convention" the
    heading actually used)."""
    lowered = raw_label.lower()
    if "republican" in lowered:
        return "Republican"
    if "democratic" in lowered:
        return "Democrat"
    return raw_label


def find_candidates_list_elem(header_elem):
    """Walk forward through header_elem's sibling headings looking for a Nominee/Declared/etc.
    heading, returning the <ul> right after it, or None if we hit another party's section first."""
    candidates_list_elem = None
    for sub_header in header_elem.find_next_siblings(HEADING_TAGS):
        if reached_another_party(sub_header):
            break
        sub_header_text = sub_header.get_text(strip=True)
        if sub_header_text in KEEP_HEADINGS:
            next_sibling = sub_header.find_next_sibling()
            if next_sibling.name == "ul":
                candidates_list_elem = next_sibling
            break
    return candidates_list_elem


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

            if header.endswith((" primary", " convention")) or header == "Independents":
                if header == "Independents":
                    party = None
                else:
                    raw_label = header.removesuffix(" primary").removesuffix(
                        " convention"
                    )
                    party = normalize_party(raw_label)
                candidates_list_elem = find_candidates_list_elem(headerElem)
                if (
                    candidates_list_elem is not None
                    and candidates_list_elem.name == "ul"
                ):
                    append_candidates(candidates_list_elem, candidates, party)

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
                            else normalize_party(third_party_header)
                        )
                        candidates_list_elem = find_candidates_list_elem(
                            third_party_header_elem
                        )
                        if (
                            candidates_list_elem is not None
                            and candidates_list_elem.name == "ul"
                        ):
                            append_candidates(candidates_list_elem, candidates, party)
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
