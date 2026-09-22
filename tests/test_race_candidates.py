from unittest.mock import MagicMock, patch

import pytest

from my_actor.src.candidates import get_title, parse_candidates
from my_actor.src.race_candidates import get_race_candidates
from my_actor.src.utils.normalize_inputs import check_office, check_state
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
    def test_keeps_only_nominees_and_declared_across_all_parties(self):
        names = [c["name"] for c in parse_candidates(SAMPLE_EXTRACT)]
        assert names == [
            "Abdul El-Sayed",
            "Mike Rogers",
            "TJ Stephens",
            "Lydia Christensen",
        ]

    def test_drops_eliminated_and_withdrawn(self):
        names = [c["name"] for c in parse_candidates(SAMPLE_EXTRACT)]
        assert "Haley Stevens" not in names
        assert "Mallory McMorrow" not in names

    def test_no_matching_headings_returns_empty_list(self):
        assert parse_candidates("No headings here at all.") == []

    def test_drops_candidate_after_unmarked_status_change(self):
        # Regression test for the 2026 Ohio Senate special election page: "Disqualified" was
        # a bolded paragraph, not a proper heading, so Jeffrey Kanter's <li> ends up in a
        # second <ul> after it rather than the Nominee heading's own list.
        names = [c["name"] for c in parse_candidates(SAMPLE_EXTRACT)]
        assert "Jeffrey Kanter" not in names
        assert "Disqualified" not in names

    def test_assigns_major_party_from_h2_primary_heading(self):
        candidates = {c["name"]: c["party"] for c in parse_candidates(SAMPLE_EXTRACT)}
        assert candidates["Abdul El-Sayed"] == "Democratic"
        assert candidates["Mike Rogers"] == "Republican"

    def test_assigns_third_party_from_h3_heading(self):
        candidates = {c["name"]: c["party"] for c in parse_candidates(SAMPLE_EXTRACT)}
        assert candidates["Lydia Christensen"] == "Libertarian Party"

    def test_true_independent_has_null_party(self):
        candidates = {c["name"]: c["party"] for c in parse_candidates(SAMPLE_EXTRACT)}
        assert candidates["TJ Stephens"] is None

    def test_captures_description_after_first_comma(self):
        candidates = {
            c["name"]: c["description"] for c in parse_candidates(SAMPLE_EXTRACT)
        }
        assert candidates["Lydia Christensen"] == "CEO"


class TestGetRaceCandidates:
    def test_invalid_state_raises_before_any_request(self):
        with (
            patch("my_actor.src.race_candidates.requests.get") as mock_get,
            pytest.raises(ValueError, match="invalid state or office"),
        ):
            get_race_candidates(2026, "s", "ZZ")
        mock_get.assert_not_called()

    def test_missing_article_returns_graceful_error_result(self):
        # e.g. a state with no Senate seat up that cycle (no Wikipedia article exists at all) —
        # this is an expected outcome, not a scrape failure, so it must not raise.
        mock_response = MagicMock()
        mock_response.json.return_value = {"query": {"pages": {"-1": {"missing": ""}}}}
        with patch(
            "my_actor.src.race_candidates.requests.get", return_value=mock_response
        ):
            result = get_race_candidates(2026, "s", "MI")
        assert result["candidates"] == []
        assert result["is_special"] is False
        assert "error" in result
        assert result["year"] == 2026
        assert result["state"] == "MI"
        assert result["state_label"] == "Michigan"

    def test_success_returns_parsed_candidates(self):
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
        mock_dates = {
            "senate": {
                "primary_date": "2026-08-04",
                "primary_runoff": None,
                "general_election": "2026-11-03",
            }
        }
        with (
            patch(
                "my_actor.src.race_candidates.requests.get",
                return_value=mock_response,
            ),
            patch(
                "my_actor.src.race_candidates.get_election_dates",
                return_value=mock_dates,
            ),
        ):
            result = get_race_candidates(2026, "s", "MI")
        names = [c["name"] for c in result["candidates"]]
        assert names == [
            "Abdul El-Sayed",
            "Mike Rogers",
            "TJ Stephens",
            "Lydia Christensen",
        ]
        assert result["election_date"] == "2026-11-03"
        assert result["primary_date"] == "2026-08-04"
        assert result["runoff_date"] is None
