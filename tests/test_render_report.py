from my_actor.src.render_report import render_race_report

RESULT = {
    "year": 2026,
    "office": "Senate",
    "state": "MI",
    "state_label": "Michigan",
    "election_date": "2026-11-03",
    "primary_date": "2026-08-04",
    "runoff_date": None,
    "is_special": False,
    "candidates": [
        {
            "name": "Abdul El-Sayed",
            "description": "health director",
            "party": "Democratic",
        },
        {"name": "TJ Stephens", "description": "", "party": None},
    ],
}


class TestRenderRaceReport:
    def test_includes_title_with_year_office_state(self):
        html = render_race_report(RESULT)
        assert "2026 Senate Election — Michigan" in html

    def test_includes_each_candidate_name_and_party(self):
        html = render_race_report(RESULT)
        assert "Abdul El-Sayed" in html
        assert "Democratic" in html
        assert "TJ Stephens" in html

    def test_null_party_renders_as_independent(self):
        html = render_race_report(RESULT)
        assert "Independent" in html

    def test_empty_description_omits_description_paragraph(self):
        html = render_race_report(RESULT)
        # TJ Stephens has no description — only one roster-description <p> (El-Sayed's) should exist
        assert html.count('<p class="roster-description">') == 1

    def test_includes_formatted_election_dates(self):
        html = render_race_report(RESULT)
        assert "November 3, 2026" in html
        assert "August 4, 2026" in html

    def test_missing_dates_render_as_unknown(self):
        result = {**RESULT, "election_date": None, "primary_date": None}
        html = render_race_report(result)
        assert "Unknown" in html

    def test_special_election_adds_type_fact(self):
        html = render_race_report({**RESULT, "is_special": True})
        assert "Special election" in html

    def test_non_special_election_omits_type_fact(self):
        html = render_race_report(RESULT)
        assert "Special election" not in html

    def test_no_candidates_shows_empty_state_not_error(self):
        result = {**RESULT, "candidates": []}
        html = render_race_report(result)
        assert "No candidates found" in html

    def test_html_in_candidate_fields_is_escaped(self):
        result = {
            **RESULT,
            "candidates": [
                {
                    "name": "<script>alert(1)</script>",
                    "description": "a & b",
                    "party": "Independent",
                }
            ],
        }
        html = render_race_report(result)
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html
        assert "a &amp; b" in html

    def test_unparseable_date_passes_through_unchanged(self):
        result = {**RESULT, "election_date": "TBD"}
        html = render_race_report(result)
        assert "TBD" in html
