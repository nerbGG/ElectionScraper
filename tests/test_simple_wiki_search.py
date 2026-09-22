from unittest.mock import MagicMock, patch

import pytest

from my_actor.simple_wiki_search import (
    check_office,
    check_state,
    get_title,
    handle_simple_wiki,
    parse_candidates,
)
from tests.constants.extract_example import SAMPLE_EXTRACT


class TestCheckState:
    def test_valid_abbreviation(self):
        assert check_state("MI") == "Michigan"

    def test_valid_full_name_any_case(self):
        assert check_state("michigan") == "Michigan"

    def test_unknown_abbreviation_returns_none(self):
        assert check_state("ZZ") is None

    def test_unknown_name_returns_none(self):
        assert check_state("Atlantis") is None

    def test_non_string_returns_none(self):
        assert check_state(123) is None
        assert check_state(None) is None

    def test_blank_returns_none(self):
        assert check_state("") is None
        assert check_state("   ") is None


class TestCheckOffice:
    def test_valid_abbreviation(self):
        assert check_office("s") == "Senate"

    def test_valid_full_name_any_case(self):
        assert check_office("Senate") == "Senate"

    def test_unknown_returns_none(self):
        assert check_office("x") is None

    def test_non_string_returns_none(self):
        assert check_office(123) is None


class TestGetTitle:
    def test_builds_correctly_cased_title(self):
        assert get_title("s", 2026, "MI") == (
            "2026_United_States_Senate_election_in_Michigan",
            "Michigan",
            "Senate",
        )

    def test_invalid_state_returns_none(self):
        assert get_title("s", 2026, "ZZ") is None

    def test_invalid_office_returns_none(self):
        assert get_title("x", 2026, "MI") is None


class TestParseCandidates:
    def test_keeps_only_nominees_across_all_parties(self):
        candidates = parse_candidates(SAMPLE_EXTRACT)
        assert candidates == ["Abdul El-Sayed", "Mike Rogers", "Lydia Christensen"]

    def test_drops_eliminated_and_withdrawn(self):
        candidates = parse_candidates(SAMPLE_EXTRACT)
        assert "Haley Stevens" not in candidates
        assert "Mallory McMorrow" not in candidates

    def test_no_matching_headings_returns_empty_list(self):
        assert parse_candidates("No headings here at all.") == []

    def test_drops_candidate_after_unmarked_status_change(self):
        # Regression test for the 2026 Ohio Senate special election page: "Disqualified" was
        # a bolded paragraph, not a proper heading, so Jeffrey Kanter's <li> ends up in a
        # second <ul> after it rather than the Nominee heading's own list.
        candidates = parse_candidates(SAMPLE_EXTRACT)
        assert "Jeffrey Kanter" not in candidates
        assert "Disqualified" not in candidates


class TestHandleSimpleWiki:
    def test_invalid_state_raises_before_any_request(self):
        with (
            patch("my_actor.simple_wiki_search.requests.get") as mock_get,
            pytest.raises(ValueError, match="invalid state or office"),
        ):
            handle_simple_wiki(2026, "s", "ZZ")
        mock_get.assert_not_called()

    def test_missing_article_raises_runtime_error(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"query": {"pages": {"-1": {"missing": ""}}}}
        with (
            patch(
                "my_actor.simple_wiki_search.requests.get", return_value=mock_response
            ),
            pytest.raises(RuntimeError, match="article is missing"),
        ):
            handle_simple_wiki(2026, "s", "MI")

    def test_success_returns_structured_result(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "65822720": {
                        "pageid": 65822720,
                        "title": "2026 United States Senate election in Michigan",
                        "extract": SAMPLE_EXTRACT,
                    }
                }
            }
        }
        with (
            patch(
                "my_actor.simple_wiki_search.requests.get",
                return_value=mock_response,
            ),
            patch(
                "my_actor.simple_wiki_search.get_election_dates",
                return_value={
                    "senate": {
                        "primary_date": "2026-08-04",
                        "primary_runoff": None,
                        "general_election": "2026-11-03",
                    }
                },
            ),
        ):
            result = handle_simple_wiki(2026, "s", "MI")
        assert result == {
            "year": 2026,
            "candidates": ["Abdul El-Sayed", "Mike Rogers", "Lydia Christensen"],
            "office": "Senate",
            "state": "MI",
            "state_label": "Michigan",
            "election_date": "2026-11-03",
            "primary_date": "2026-08-04",
            "runoff_date": None,
            "is_special": False,
        }

    def test_dates_failure_returns_null_dates_with_candidates(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "65822720": {
                        "pageid": 65822720,
                        "title": "2026 United States Senate election in Michigan",
                        "extract": SAMPLE_EXTRACT,
                    }
                }
            }
        }
        with (
            patch(
                "my_actor.simple_wiki_search.requests.get",
                return_value=mock_response,
            ),
            patch(
                "my_actor.simple_wiki_search.get_election_dates",
                side_effect=RuntimeError(
                    "couldn't get the election dates for Michigan (2026): "
                    "simulated outage"
                ),
            ),
        ):
            result = handle_simple_wiki(2026, "s", "MI")
        assert result["candidates"] == [
            "Abdul El-Sayed",
            "Mike Rogers",
            "Lydia Christensen",
        ]
        assert result["election_date"] is None
        assert result["primary_date"] is None
        assert result["runoff_date"] is None

    def test_full_name_state_input_uppercase_abbreviation(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "65822720": {
                        "pageid": 65822720,
                        "title": "2026 United States Senate election in Michigan",
                        "extract": SAMPLE_EXTRACT,
                    }
                }
            }
        }
        with (
            patch(
                "my_actor.simple_wiki_search.requests.get",
                return_value=mock_response,
            ),
            patch(
                "my_actor.simple_wiki_search.get_election_dates",
                return_value={
                    "senate": {
                        "primary_date": "2026-08-04",
                        "primary_runoff": None,
                        "general_election": "2026-11-03",
                    }
                },
            ),
        ):
            result = handle_simple_wiki(2026, "s", "michigan")
        assert result["state"] == "MI"
        assert result["state_label"] == "Michigan"
