# A trimmed but structurally real HTML extract covering: two-party primary with a Nominee, an
# eliminated candidate, a withdrawn candidate; a true independent (party should be None); a
# third-party Nominee nested under "Third-parties and independents"; a malformed
# "Disqualified" status (bolded paragraph, not a proper heading) interrupting a candidate
# list — the real bug found on the 2026 Ohio Senate special election page, where the
# disqualified candidate's <li> sits in a second, separate <ul> after the bad paragraph; and a
# primary whose original nominee withdrew, replaced via a nominating convention — the real
# pattern confirmed live on the 2026 Maine Senate race (Graham Platner withdrew after winning
# the Democratic primary; Troy Jackson was chosen at a later convention instead). The
# convention section's own "Campaign and convention" sub-heading is a deliberate decoy: it
# coincidentally ends in " convention" too, but isn't itself a section boundary.
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
<h3 data-mw-anchor="Independents">Independents</h3>
<h4 data-mw-anchor="Declared">Declared</h4>
<ul><li>TJ Stephens, business executive</li></ul>
<h3 data-mw-anchor="Libertarian_Party">Libertarian Party</h3>
<h4 data-mw-anchor="Nominee_3">Nominee</h4>
<ul><li>Lydia Christensen, CEO</li></ul>
<p><b>Disqualified</b></p>
<ul><li>Jeffrey Kanter, healthcare consultant</li></ul>
<h2 data-mw-anchor="Green_primary">Green primary</h2>
<h3 data-mw-anchor="Candidates_3">Candidates</h3>
<h4 data-mw-anchor="Withdrawn_3">Withdrawn</h4>
<ul><li>Pat Rivera, former city council member</li></ul>
<h2 data-mw-anchor="Rivera's_withdrawal">Rivera's withdrawal</h2>
<h2 data-mw-anchor="Green_nominating_convention">Green nominating convention</h2>
<h3 data-mw-anchor="Campaign_and_convention">Campaign and convention</h3>
<h3 data-mw-anchor="Candidates_4">Candidates</h3>
<h4 data-mw-anchor="Nominee_4">Nominee</h4>
<ul><li>Sam Okafor, state senator</li></ul>
"""
