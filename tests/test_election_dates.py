import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from my_actor.get_election_dates import (
    _align_row,
    _load_election_dates_file,
    _normalize_date,
    _parse_data_cell,
    _parse_state_cell,
    _split_table_rows,
    get_election_dates,
)
from tests.constants.election_dates_example import (
    SAMPLE_ELECTION_WIKITEXT,
    SAMPLE_TOC_RESPONSE,
    SAMPLE_WIKITEXT_RESPONSE,
)

SNAPSHOT = {
    "updated_at": "2026-09-20T19:50:22+00:00",
    "Michigan": {
        "senate": {
            "primary_date": "2026-08-04",
            "primary_runoff": None,
            "general_election": "2026-11-03",
        }
    },
    "Florida": {
        "senate": {
            "primary_date": "2026-08-18",
            "primary_runoff": None,
            "general_election": "2026-11-03",
        }
    },
}

ALL_VARIANT_STATES = [
    "Alabama",
    "Alaska",
    "Colorado",
    "Delaware",
    "Florida",
    "Maine",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Ohio",
    "Wyoming",
]


def _mock_api_responses():
    toc_response = MagicMock()
    toc_response.json.return_value = SAMPLE_TOC_RESPONSE
    wikitext_response = MagicMock()
    wikitext_response.json.return_value = SAMPLE_WIKITEXT_RESPONSE
    return [toc_response, wikitext_response]


@pytest.fixture
def constants_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("my_actor.get_election_dates._CONSTANTS_DIR", tmp_path)
    return tmp_path


def _write_snapshot(constants_dir, snapshot=SNAPSHOT, cycle=2026):
    constants_dir.joinpath(f"election_dates_{cycle}.json").write_text(
        json.dumps(snapshot)
    )


class TestSplitTableRows:
    def test_splits_header_and_data_rows(self):
        rows = _split_table_rows(SAMPLE_ELECTION_WIKITEXT)
        assert len(rows) == 12
        assert rows[0][0] == "! State"
        assert (
            rows[1][0] == "! [[2026 United States Senate election in Alabama|Alabama]]"
        )

    def test_captures_trailing_row_without_separator(self):
        rows = _split_table_rows(SAMPLE_ELECTION_WIKITEXT)
        assert (
            rows[-1][0] == "! [[2026 United States Senate election in Wyoming|Wyoming]]"
        )

    def test_ignores_heading_and_delimiter_lines(self):
        rows = _split_table_rows(
            '==Some section ==\n\n{| class="wikitable"\n|-\n! A\n| b\n|}'
        )
        assert rows == [["! A", "| b"]]


class TestParseStateCell:
    def test_link_label_is_extracted(self):
        cell = "! [[2026 United States Senate election in Alabama|Alabama]]"
        assert _parse_state_cell(cell) == "Alabama"

    def test_special_link_label_is_preserved(self):
        cell = (
            "! [[2026 United States Senate special election in Florida|"
            "Florida (special)]]"
        )
        assert _parse_state_cell(cell) == "Florida (special)"

    def test_plain_cell_falls_back_to_text(self):
        assert _parse_state_cell("! Alabama") == "Alabama"


class TestParseDataCell:
    def test_full_form_with_rowspan_and_sort_value(self):
        cell = '| rowspan="35" data-sort-value="November 3, 2026" | November 3, 2026'
        assert _parse_data_cell(cell) == (35, "November 3, 2026")

    def test_sort_value_without_rowspan(self):
        cell = '| data-sort-value="January 23, 2026" | January 23, 2026'
        assert _parse_data_cell(cell) == (1, "January 23, 2026")

    def test_rowspan_na_cell(self):
        cell = '| rowspan="3" data-sort-value="November 31, 2026" | N/A'
        assert _parse_data_cell(cell) == (3, "N/A")

    def test_missing_space_after_separator_is_tolerated(self):
        assert _parse_data_cell('| data-sort-value="May 5, 2026" |May 5, 2026') == (
            1,
            "May 5, 2026",
        )
        assert _parse_data_cell("|N/A") == (1, "N/A")

    def test_bare_value_cell(self):
        assert _parse_data_cell("|8pm") == (1, "8pm")
        assert _parse_data_cell("|12am and 1am") == (1, "12am and 1am")

    def test_non_pipe_line_raises(self):
        with pytest.raises(RuntimeError, match="unparseable table cell"):
            _parse_data_cell("! Not a data cell")


class TestAlignRow:
    def test_fills_rowspan_covered_columns(self):
        covered = {4: (2, "November 3, 2026")}
        aligned = _align_row(
            "Alaska",
            ["|June 1, 2026", "|August 18, 2026", "| N/A", "|12am and 1am"],
            covered,
        )
        assert aligned == [
            "Alaska",
            "June 1, 2026",
            "August 18, 2026",
            "N/A",
            "November 3, 2026",
            "12am and 1am",
        ]
        assert covered == {4: (1, "November 3, 2026")}

    def test_registers_new_rowspan(self):
        covered = {}
        aligned = _align_row(
            "Alabama",
            [
                '| data-sort-value="January 23, 2026" | January 23, 2026',
                '| data-sort-value="May 19, 2026" | May 19, 2026',
                '| data-sort-value="June 16, 2026" | June 16, 2026',
                '| rowspan="35" data-sort-value="November 3, 2026" | November 3, 2026',
                "|8pm",
            ],
            covered,
        )
        assert aligned[4] == "November 3, 2026"
        assert covered == {4: (34, "November 3, 2026")}

    def test_too_few_cells_raises(self):
        with pytest.raises(RuntimeError, match="does not align to 6 columns"):
            _align_row("Michigan", ["|8pm"], {})

    def test_leftover_cells_raise(self):
        with pytest.raises(RuntimeError, match="has leftover cells"):
            _align_row("Michigan", ["|a", "|b", "|c", "|d", "|e", "|f"], {})


class TestNormalizeDate:
    def test_converts_month_day_year_to_iso(self):
        assert _normalize_date("May 19, 2026") == "2026-05-19"
        assert _normalize_date("November 3, 2026") == "2026-11-03"
        assert _normalize_date("May 5, 2026") == "2026-05-05"

    def test_na_and_blank_become_none(self):
        assert _normalize_date("N/A") is None
        assert _normalize_date(" n/a ") is None
        assert _normalize_date("") is None

    def test_unparseable_date_raises(self):
        with pytest.raises(RuntimeError, match="unparseable date"):
            _normalize_date("Novtember 31, 2026")


class TestLoadElectionDatesFile:
    def test_missing_file_returns_none(self, tmp_path):
        assert _load_election_dates_file(tmp_path / "nope.json") is None

    def test_corrupt_json_returns_none(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json{")
        assert _load_election_dates_file(path) is None

    def test_old_array_format_returns_none(self, tmp_path):
        path = tmp_path / "old.json"
        path.write_text(json.dumps([{"state": "Alabama"}]))
        assert _load_election_dates_file(path) is None

    def test_dict_without_updated_at_returns_none(self, tmp_path):
        path = tmp_path / "no-meta.json"
        path.write_text(json.dumps({"Michigan": {}}))
        assert _load_election_dates_file(path) is None

    def test_valid_snapshot_returns_dict(self, tmp_path):
        path = tmp_path / "good.json"
        path.write_text(json.dumps(SNAPSHOT))
        assert _load_election_dates_file(path) == SNAPSHOT


class TestGetElectionDates:
    def test_invalid_state_raises_before_any_request(self, constants_dir):
        with (
            patch("my_actor.get_election_dates.requests.get") as mock_get,
            pytest.raises(ValueError, match="invalid state"),
        ):
            get_election_dates("ZZ", 2026)
        mock_get.assert_not_called()

    def test_serves_state_from_file_without_network(self, constants_dir):
        _write_snapshot(constants_dir)
        with patch(
            "my_actor.get_election_dates.requests.get",
            side_effect=AssertionError("network call attempted"),
        ):
            result = get_election_dates("MI", 2026)
        assert result == SNAPSHOT["Michigan"]

    def test_normalizes_state_input(self, constants_dir):
        _write_snapshot(constants_dir)
        with patch(
            "my_actor.get_election_dates.requests.get",
            side_effect=AssertionError("network call attempted"),
        ):
            for state in ("MI", "mi", "michigan", "MICHIGAN"):
                assert get_election_dates(state, 2026) == SNAPSHOT["Michigan"]

    def test_state_not_on_ballot_raises_without_network(self, constants_dir):
        _write_snapshot(constants_dir)
        with (
            patch(
                "my_actor.get_election_dates.requests.get",
                side_effect=AssertionError("network call attempted"),
            ) as mock_get,
            pytest.raises(RuntimeError, match="no Senate race on the ballot"),
        ):
            get_election_dates("NY", 2026)
        mock_get.assert_not_called()

    def test_missing_file_fetches_api_and_writes_file(self, constants_dir):
        with patch(
            "my_actor.get_election_dates.requests.get",
            side_effect=_mock_api_responses(),
        ) as mock_get:
            result = get_election_dates("MI", 2026)
        assert mock_get.call_count == 2
        assert result["senate"]["primary_date"] == "2026-08-04"

        saved = json.loads(
            constants_dir.joinpath("election_dates_2026.json").read_text()
        )
        assert isinstance(saved, dict) and "updated_at" in saved
        assert saved["Michigan"]["senate"]["primary_date"] == "2026-08-04"

        with patch(
            "my_actor.get_election_dates.requests.get",
            side_effect=AssertionError("network call attempted"),
        ):
            assert get_election_dates("MI", 2026) == result

    def test_fetch_parses_all_rowspan_variants(self, constants_dir):
        with patch(
            "my_actor.get_election_dates.requests.get",
            side_effect=_mock_api_responses(),
        ):
            get_election_dates("MI", 2026)

        saved = json.loads(
            constants_dir.joinpath("election_dates_2026.json").read_text()
        )
        assert len(saved) == len(ALL_VARIANT_STATES) + 1
        assert saved["updated_at"]
        assert saved["Alabama"]["senate"]["primary_runoff"] == "2026-06-16"
        assert saved["Michigan"]["senate"]["primary_date"] == "2026-08-04"
        assert saved["Ohio"]["senate"]["primary_date"] == "2026-05-05"
        for state in ALL_VARIANT_STATES:
            assert saved[state]["senate"]["general_election"] == "2026-11-03", state
        for state in ALL_VARIANT_STATES:
            if state != "Alabama":
                assert saved[state]["senate"]["primary_runoff"] is None, state

    def test_old_format_file_triggers_refetch(self, constants_dir):
        constants_dir.joinpath("election_dates_2026.json").write_text(
            json.dumps([{"state": "Alabama"}])
        )
        with patch(
            "my_actor.get_election_dates.requests.get",
            side_effect=_mock_api_responses(),
        ):
            result = get_election_dates("MI", 2026)
        saved = json.loads(
            constants_dir.joinpath("election_dates_2026.json").read_text()
        )
        assert isinstance(saved, dict) and "updated_at" in saved
        assert result["senate"]["primary_date"] == "2026-08-04"

    def test_corrupt_file_triggers_refetch(self, constants_dir):
        constants_dir.joinpath("election_dates_2026.json").write_text("garbage{")
        with patch(
            "my_actor.get_election_dates.requests.get",
            side_effect=_mock_api_responses(),
        ):
            result = get_election_dates("MI", 2026)
        assert result["senate"]["primary_date"] == "2026-08-04"

    def test_api_failure_raises_with_state_in_message(self, constants_dir):
        with (
            patch(
                "my_actor.get_election_dates.requests.get",
                side_effect=requests.ConnectionError("simulated outage"),
            ),
            pytest.raises(
                RuntimeError,
                match=r"couldn't get the election dates for Michigan \(2026\)",
            ),
        ):
            get_election_dates("MI", 2026)
        assert not constants_dir.joinpath("election_dates_2026.json").exists()

    def test_missing_section_raises_with_state_in_message(self, constants_dir):
        toc_response = MagicMock()
        toc_response.json.return_value = {
            "parse": {"tocdata": {"sections": [{"line": "Predictions", "index": "10"}]}}
        }
        with (
            patch(
                "my_actor.get_election_dates.requests.get",
                return_value=toc_response,
            ),
            pytest.raises(RuntimeError, match="couldn't get the election dates"),
        ):
            get_election_dates("MI", 2026)

    def test_fetched_table_without_state_raises_but_saves_file(self, constants_dir):
        with (
            patch(
                "my_actor.get_election_dates.requests.get",
                side_effect=_mock_api_responses(),
            ),
            pytest.raises(RuntimeError, match="no Senate race on the ballot"),
        ):
            get_election_dates("NY", 2026)
        assert constants_dir.joinpath("election_dates_2026.json").is_file()

        with patch(
            "my_actor.get_election_dates.requests.get",
            side_effect=AssertionError("network call attempted"),
        ):
            result = get_election_dates("MI", 2026)
        assert result["senate"]["primary_date"] == "2026-08-04"
