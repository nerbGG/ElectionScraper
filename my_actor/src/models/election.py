from datetime import date

from pydantic import BaseModel, Field

from .candidate import Candidate


class Election(BaseModel):
    year: int
    office: str
    state: str
    state_label: str
    election_date: date | None = None
    primary_date: date | None = None
    runoff_date: date | None = None
    is_special: bool = False
    error: str | None = None
    candidates: list[Candidate] = Field(default_factory=list)
