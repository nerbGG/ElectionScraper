from unittest.mock import patch

import pytest

from my_actor.src.simple_wiki_search import handle_simple_wiki


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
        race_result = {
            "year": 2026,
            "candidates": [
                {"name": "Abdul El-Sayed", "description": "", "party": "Democratic"}
            ],
            "office": "Senate",
            "state": "MI",
            "state_label": "Michigan",
            "election_date": "2026-11-03",
            "primary_date": "2026-08-04",
            "runoff_date": None,
            "is_special": False,
        }
        with patch(
            "my_actor.src.simple_wiki_search.get_race_candidates",
            return_value=race_result,
        ) as mock_get:
            result = handle_simple_wiki(2026, "s", "MI", query_mode="race_candidates")
        mock_get.assert_called_once_with(2026, "s", "MI")
        assert result == race_result
        assert result["election_date"] == "2026-11-03"
        assert result["primary_date"] == "2026-08-04"
        assert result["runoff_date"] is None

    def test_unsupported_query_mode_returns_none(self):
        assert (
            handle_simple_wiki(2026, "s", "MI", query_mode="candidate_search") is None
        )
