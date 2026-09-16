from unittest.mock import MagicMock, patch

import pytest

from my_actor.simple_wiki_search import (
    check_office,
    check_state,
    get_title,
    handle_simple_wiki,
    parse_candidates,
)

# A trimmed but structurally real extract: two-party primary with a Nominee,
# an eliminated candidate, a withdrawn candidate, and a third-party Nominee —
# covers the "same heading text repeats across sections" case that broke an
# earlier version of the heading regex.
SAMPLE_EXTRACT = """The 2026 United States Senate election in Michigan will be held.


== Democratic primary ==


=== Candidates ===


==== Nominee ====
Abdul El-Sayed, former Wayne County health director (2023-2025)


==== Eliminated in primary ====
Haley Stevens, U.S. representative from Michigan's 11th congressional district


==== Withdrawn ====
Mallory McMorrow, state senator from the 8th district (remained on ballot)


== Republican primary ==


=== Candidates ===


==== Nominee ====
Mike Rogers, former U.S. representative from Michigan's 8th congressional district


== Third-parties and independents ==


=== Libertarian Party ===


==== Nominee ====
Lydia Christensen, CEO
"""


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
        assert (
            get_title("s", 2026, "MI")
            == "2026_United_States_Senate_election_in_Michigan"
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
        with patch(
            "my_actor.simple_wiki_search.requests.get", return_value=mock_response
        ):
            result = handle_simple_wiki(2026, "s", "MI")
        assert result == ["Abdul El-Sayed", "Mike Rogers", "Lydia Christensen"]
