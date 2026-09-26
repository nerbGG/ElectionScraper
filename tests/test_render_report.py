from datetime import date

from my_actor.src.models.candidate import Candidate
from my_actor.src.models.election import Election
from my_actor.src.render_report import render_race_report


def _election(**overrides) -> Election:
    defaults = {
        "year": 2026,
        "office": "Senate",
        "state": "MI",
        "state_label": "Michigan",
        "election_date": date(2026, 11, 3),
        "primary_date": date(2026, 8, 4),
        "runoff_date": None,
        "is_special": False,
        "error": None,
        "candidates": [
            Candidate(
                name="Abdul El-Sayed", description="health director", party="Democratic"
            ),
            Candidate(name="TJ Stephens", description="", party=None),
        ],
    }
    defaults.update(overrides)
    return Election(**defaults)


class TestRenderRaceReport:
    def test_includes_title_with_year_office_state(self):
        html = render_race_report(_election())
        assert "2026 Senate Election — Michigan" in html

    def test_includes_each_candidate_name_and_party(self):
        html = render_race_report(_election())
        assert "Abdul El-Sayed" in html
        assert "Democratic" in html
        assert "TJ Stephens" in html

    def test_null_party_renders_as_independent(self):
        html = render_race_report(_election())
        assert "Independent" in html

    def test_empty_description_omits_description_paragraph(self):
        html = render_race_report(_election())
        # TJ Stephens has no description — only one roster-description <p> (El-Sayed's) should exist
        assert html.count('<p class="roster-description">') == 1

    def test_includes_formatted_election_dates(self):
        html = render_race_report(_election())
        assert "November 3, 2026" in html
        assert "August 4, 2026" in html

    def test_missing_dates_render_as_unknown(self):
        html = render_race_report(_election(election_date=None, primary_date=None))
        assert "Unknown" in html

    def test_special_election_adds_type_fact(self):
        html = render_race_report(_election(is_special=True))
        assert "Special election" in html

    def test_non_special_election_omits_type_fact(self):
        html = render_race_report(_election())
        assert "Special election" not in html

    def test_no_candidates_shows_empty_state_not_error(self):
        html = render_race_report(_election(candidates=[]))
        assert "No candidates found" in html

    def test_no_candidates_with_error_shows_error_message_instead(self):
        html = render_race_report(
            _election(
                candidates=[],
                error="No race found for Senate in New York (2026)",
            )
        )
        assert "No race found for Senate in New York (2026)" in html
        assert "No candidates found" not in html

    def test_html_in_candidate_fields_is_escaped(self):
        html = render_race_report(
            _election(
                candidates=[
                    Candidate(
                        name="<script>alert(1)</script>",
                        description="a & b",
                        party="Independent",
                    )
                ]
            )
        )
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html
        assert "a &amp; b" in html
