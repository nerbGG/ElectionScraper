from datetime import date
from unittest.mock import patch

import pytest

from my_actor.src.models.election import Election
from my_actor.src.simple_wiki_search import RaceCandidatesResult, handle_simple_wiki


class TestHandleSimpleWiki:
    def test_missing_year_raises(self):
        with pytest.raises(ValueError, match="parameter is missing: year"):
            handle_simple_wiki(None, "s", "MI")

    def test_missing_state_raises(self):
        with pytest.raises(ValueError, match="parameter is missing: state"):
            handle_simple_wiki(2026, "s", None)

    def test_missing_office_raises(self):
        with pytest.raises(ValueError, match="parameter is missing: office"):
            handle_simple_wiki(2026, None, "MI")

    def test_race_candidates_mode_delegates_and_returns_result(self):
        election = Election(
            year=2026,
            office="Senate",
            state="MI",
            state_label="Michigan",
            election_date=date(2026, 11, 3),
            primary_date=date(2026, 8, 4),
            runoff_date=None,
            is_special=False,
            candidates=[],
        )
        with patch(
            "my_actor.src.simple_wiki_search.get_race",
            return_value=election,
        ) as mock_get:
            result = handle_simple_wiki(2026, "s", "MI", query_mode="race_candidates")
        mock_get.assert_called_once_with(2026, "s", "MI")
        assert isinstance(result, RaceCandidatesResult)
        assert result.query_mode == "race_candidates"
        assert result.election is election
        assert result.election.election_date == date(2026, 11, 3)
        assert result.election.primary_date == date(2026, 8, 4)
        assert result.election.runoff_date is None

    def test_unsupported_query_mode_returns_none(self):
        assert (
            handle_simple_wiki(2026, "s", "MI", query_mode="candidate_search") is None
        )
