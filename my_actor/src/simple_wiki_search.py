from .constants.query_modes import QUERY_MODES
from .race_candidates import get_race_candidates


def handle_simple_wiki(
    year: str, office: str, state: str, query_mode="race_candidates"
) -> list[str]:
    """Return a response form either race_candiates, state_all or race_candidates based on the queryMode"""
    # for each mode, ensure the required parameters are passed in
    if query_mode == QUERY_MODES["RACE_CANDIDATES"]:
        if year is None:
            raise ValueError("parameter is missing: year")
        if state is None:
            raise ValueError("parameter is missing: state")
        if office is None:
            raise ValueError("parameter is missing: office")
        if query_mode is None:
            raise ValueError("parameter is missing: query_mode")
        return get_race_candidates(year, office, state)
    # cases for the other modes don't exist yet
    return None
