from pydantic import BaseModel


class Candidate(BaseModel):
    name: str
    description: str = ""
    party: str | None = None
