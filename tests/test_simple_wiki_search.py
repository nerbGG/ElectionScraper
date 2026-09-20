from unittest.mock import patch

import pytest

from my_actor.simple_wiki_search import handle_simple_wiki


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
        with patch(
            "my_actor.simple_wiki_search.get_race_candidates",
            return_value=[
                {"name": "Abdul El-Sayed", "description": "", "party": "Democratic"}
            ],
        ) as mock_get:
            result = handle_simple_wiki(2026, "s", "MI", query_mode="race_candidates")
        mock_get.assert_called_once_with(2026, "s", "MI")
        assert result == [
            {"name": "Abdul El-Sayed", "description": "", "party": "Democratic"}
        ]

    def test_unsupported_query_mode_returns_none(self):
        assert (
            handle_simple_wiki(2026, "s", "MI", query_mode="candidate_search") is None
        )
