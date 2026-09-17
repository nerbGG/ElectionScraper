# A trimmed but structurally real HTML extract: two-party primary with a Nominee, an
# eliminated candidate, a withdrawn candidate, a third-party Nominee, and a malformed
# "Disqualified" status (bolded paragraph, not a proper heading) interrupting a candidate
# list — the real bug found on the 2026 Ohio Senate special election page, where the
# disqualified candidate's <li> sits in a second, separate <ul> after the bad paragraph.
SAMPLE_EXTRACT = """<p>The <b>2026 United States Senate election in Michigan</b> will be held.</p>
<h2 data-mw-anchor="Democratic_primary">Democratic primary</h2>
<h3 data-mw-anchor="Candidates">Candidates</h3>
<h4 data-mw-anchor="Nominee">Nominee</h4>
<ul><li>Abdul El-Sayed, former Wayne County health director (2023-2025)</li></ul>
<h4 data-mw-anchor="Eliminated_in_primary">Eliminated in primary</h4>
<ul><li>Haley Stevens, U.S. representative from Michigan's 11th congressional district</li></ul>
<h4 data-mw-anchor="Withdrawn">Withdrawn</h4>
<ul><li>Mallory McMorrow, state senator from the 8th district (remained on ballot)</li></ul>
<h2 data-mw-anchor="Republican_primary">Republican primary</h2>
<h3 data-mw-anchor="Candidates_2">Candidates</h3>
<h4 data-mw-anchor="Nominee_2">Nominee</h4>
<ul><li>Mike Rogers, former U.S. representative from Michigan's 8th congressional district</li></ul>
<h2 data-mw-anchor="Third-parties_and_independents">Third-parties and independents</h2>
<h3 data-mw-anchor="Libertarian_Party">Libertarian Party</h3>
<h4 data-mw-anchor="Nominee_3">Nominee</h4>
<ul><li>Lydia Christensen, CEO</li></ul>
<p><b>Disqualified</b></p>
<ul><li>Jeffrey Kanter, healthcare consultant</li></ul>
"""
