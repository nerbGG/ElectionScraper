from typing import Literal

from pydantic import BaseModel

from .constants.query_modes import QUERY_MODES
from .models.candidate import Candidate
from .models.election import Election
from .race_candidates import get_race


class RaceCandidatesResult(BaseModel):
    query_mode: Literal["race_candidates"] = "race_candidates"
    election: Election


class AllRacesStateResult(BaseModel):
    query_mode: Literal["all_races_state"] = "all_races_state"
    elections: list[Election]


class CandidateSearchResult(BaseModel):
    query_mode: Literal["candidate_search"] = "candidate_search"
    candidates: list[Candidate]


QueryResult = RaceCandidatesResult | AllRacesStateResult | CandidateSearchResult


def handle_simple_wiki(
    year: str, office: str, state: str, query_mode="race_candidates"
) -> QueryResult:
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
        return RaceCandidatesResult(election=get_race(year, office, state))
    # cases for the other modes don't exist yet
    return None
