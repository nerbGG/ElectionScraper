import requests

ABB_TO_FULL_STATE = {
    "al": "alabama",
    "ak": "alaska",
    "az": "arizona",
    "ar": "arkansas",
    "ca": "california",
    "co": "colorado",
    "ct": "connecticut",
    "de": "delaware",
    "fl": "florida",
    "ga": "georgia",
    "hi": "hawaii",
    "id": "idaho",
    "il": "illinois",
    "in": "indiana",
    "ia": "iowa",
    "ks": "kansas",
    "ky": "kentucky",
    "la": "louisiana",
    "me": "maine",
    "md": "maryland",
    "ma": "massachusetts",
    "mi": "michigan",
    "mn": "minnesota",
    "ms": "mississippi",
    "mo": "missouri",
    "mt": "montana",
    "ne": "nebraska",
    "nv": "nevada",
    "nh": "new hampshire",
    "nj": "new jersey",
    "nm": "new mexico",
    "ny": "new york",
    "nc": "north carolina",
    "nd": "north dakota",
    "oh": "ohio",
    "ok": "oklahoma",
    "or": "oregon",
    "pa": "pennsylvania",
    "ri": "rhode island",
    "sc": "south carolina",
    "sd": "south dakota",
    "tn": "tennessee",
    "tx": "texas",
    "ut": "utah",
    "vt": "vermont",
    "va": "virginia",
    "wa": "washington",
    "wv": "west virginia",
    "wi": "wisconsin",
    "wy": "wyoming",
}
ABB_TO_FULL_OFFICE = {"s": "senate", "h": "house", "p": "presidential"}


def simple_wiki(year, office, state) -> str:
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
    if res.status_code >= 400:
        raise RuntimeError(f"Wikipedia API error {res.status_code}: {res.text[:500]}")
    data = res.json()
    result = ""
    for key in data["query"]["pages"]:
        if key == "-1":
            raise RuntimeError(f"article is missing: {title}")
        if "special" in data["query"]["pages"][key]["title"]:
            print("============== IS SPECIAL ==============")
        result += data["query"]["pages"][key]["extract"]
    return result


def get_title(office: str, year: int, state: str) -> str | None:
    state = check_state(state)
    if not state:
        return None
    office = check_office(office)
    if not office:
        return None
    title_state = state[0].upper() + state[1:]
    title_office = office[0].upper() + office[1:]

    return f"{year}_United_States_{title_office}_election_in_{title_state}"


def check_state(state: str | None) -> str | None:
    if not isinstance(state, str):
        return None
    state = state.lower().strip()
    if not state:
        return None
    if len(state) == 2:
        return ABB_TO_FULL_STATE.get(state)
    return state if state in ABB_TO_FULL_STATE.values() else None


def check_office(office: str) -> str | None:
    if not isinstance(office, str):
        return None
    office = office.lower().strip()
    if not office:
        return None
    if len(office) == 1:
        return ABB_TO_FULL_OFFICE.get(office)
    return office if office in ABB_TO_FULL_OFFICE.values() else None
