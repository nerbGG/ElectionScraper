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
