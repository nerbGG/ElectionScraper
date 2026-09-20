# A trimmed but structurally real slice of the "Election dates" wikitext table from
# https://en.wikipedia.org/wiki/2026_United_States_Senate_elections (fetched live
# 2026-09). Every rowspan variant from the real table is preserved:
#   - Alabama carries the single rowspan general-election cell (scaled from the
#     real table's rowspan="35" to this fixture's 11 data rows, so exhaustion is
#     exercised by the last row).
#   - Colorado's rowspan="3" N/A runoff covers Delaware and Florida (special).
#   - Maine's rowspan="4" N/A runoff covers Massachusetts, Michigan, and Minnesota.
#   - Ohio (special) has an explicit N/A runoff and the real table's missing-space
#     cell forms ("|May 5, 2026", "|N/A").
#   - Wyoming carries its own explicit N/A cell so the final row stays aligned.
# <ref> tags from the real header were trimmed; everything else is verbatim.

SAMPLE_ELECTION_WIKITEXT = """==Election dates ==

{| class="wikitable sortable"
|-
! State
! Filing deadline for<br />major party candidates
! Primary<br />election
! Primary<br />runoff<br />{{Small|(if necessary)}}
! General<br />election
!Poll closing<br/>{{Small|(Eastern Time)}}
|-
! [[2026 United States Senate election in Alabama|Alabama]]
| data-sort-value="January 23, 2026" | January 23, 2026
| data-sort-value="May 19, 2026" | May 19, 2026
| data-sort-value="June 16, 2026" | June 16, 2026
| rowspan="11" data-sort-value="November 3, 2026" | November 3, 2026
|8pm
|-
! [[2026 United States Senate election in Alaska|Alaska]]
| data-sort-value="June 1, 2026" | June 1, 2026
| data-sort-value="August 18, 2026" | August 18, 2026
| data-sort-value="November 31, 2026" | N/A
|12am and 1am
|-
! [[2026 United States Senate election in Colorado|Colorado]]
| data-sort-value="March 18, 2026" | March 18, 2026
| data-sort-value="June 30, 2026" | June 30, 2026
| rowspan="3" data-sort-value="November 31, 2026" | N/A
|9pm
|-
! [[2026 United States Senate election in Delaware|Delaware]]
| data-sort-value="July 14, 2026" | July 14, 2026
| data-sort-value="September 15, 2026" | September 15, 2026
|8pm
|-
! [[2026 United States Senate special election in Florida|Florida (special)]]
| data-sort-value="April 24, 2026" | April 24, 2026
| data-sort-value="August 18, 2026" |August 18, 2026
|7pm
|-
! [[2026 United States Senate election in Maine|Maine]]
| data-sort-value="March 15, 2026" | March 15, 2026
| data-sort-value="June 9, 2026" | June 9, 2026
| rowspan="4" data-sort-value="November 31, 2026" | N/A
|8pm
|-
! [[2026 United States Senate election in Massachusetts|Massachusetts]]
| data-sort-value="June 2, 2026" | June 2, 2026
| data-sort-value="September 1, 2026" | September 1, 2026
|8pm
|-
! [[2026 United States Senate election in Michigan|Michigan]]
| data-sort-value="April 21, 2026" | April 21, 2026
| data-sort-value="August 4, 2026" | August 4, 2026
|8pm and 9pm
|-
! [[2026 United States Senate election in Minnesota|Minnesota]]
| data-sort-value="June 2, 2026" | June 2, 2026
| data-sort-value="August 11, 2026" | August 11, 2026
|9pm
|-
! [[2026 United States Senate special election in Ohio|Ohio (special)]]
| data-sort-value="February 4, 2026" |February 4, 2026
| data-sort-value="May 5, 2026" |May 5, 2026
| data-sort-value="November 31, 2026" |N/A
|7:30pm
|-
! [[2026 United States Senate election in Wyoming|Wyoming]]
| data-sort-value="May 29, 2026" | May 29, 2026
| data-sort-value="August 18, 2026" | August 18, 2026
| data-sort-value="November 31, 2026" | N/A
|9pm
|}"""

SAMPLE_TOC_RESPONSE = {
    "parse": {
        "title": "2026 United States Senate elections",
        "pageid": 65785708,
        "tocdata": {
            "sections": [
                {
                    "tocLevel": 1,
                    "hLevel": 2,
                    "line": "Predictions",
                    "number": "5",
                    "index": "10",
                },
                {
                    "tocLevel": 1,
                    "hLevel": 2,
                    "line": "Election dates",
                    "number": "8",
                    "index": "15",
                },
                {
                    "tocLevel": 1,
                    "hLevel": 2,
                    "line": "Race summary",
                    "number": "9",
                    "index": "16",
                },
            ]
        },
    }
}

SAMPLE_WIKITEXT_RESPONSE = {
    "parse": {
        "title": "2026 United States Senate elections",
        "pageid": 65785708,
        "wikitext": {"*": SAMPLE_ELECTION_WIKITEXT},
    }
}
