# Tech Spec: Wikipedia Election Scraper (Apify Actor)

**Version:** 0.3
**Creator:** Nel Barthelemy
**Status:** Draft — four-phase roadmap (v1–v4, see §1). v1 build scope is `race_candidates`,
Senate only. v3/v4 (`state_all`/`candidate_search`) are fully designed below; v2 (`race_candidates`
expanded to non-Senate offices) is scoped but not yet designed.
**Last Updated:** 2026-08-19

## 1. Overview

A standalone Apify Actor with three structured query modes, all sourced live from Wikipedia,
built out across four phases:

| Phase | Mode | Scope | Status |
|---|---|---|---|
| **v1** | `race_candidates` | U.S. Senate only | **Build target** |
| **v2** | `race_candidates` | Expanded to other offices (House, Governor, etc.) | Scoped, not designed |
| **v3** | `state_all` | All elections in a state | Designed, deferred |
| **v4** | `candidate_search` | Candidate name → race + bio | Designed, deferred |

v3 and v4 were designed in full this session (explored and verified live against real Wikipedia
data) so they're a known quantity when their turn comes, not a redesign — but nothing beyond v1
is being built yet.

The three modes themselves:

1. **`race_candidates`** — given a state + office + cycle, return the current candidate list
   (name, party, status, short bio) for that specific race. This was the original v0.1 scope.
   Senate-only in v1; other offices added in v2.
2. **`state_all`** — given a state (+ cycle), return every election happening in that state. v3.
3. **`candidate_search`** — given a candidate name, return which race they're running in plus
   basic bio info. v4.

Sold on the Apify Store as a paid scraper, targeting developers, researchers, and other
applications that need normalized election data without building their own Wikipedia-parsing
pipeline.

**Query modes are explicit, not free-text.** The caller passes a `mode` field plus the params
that mode needs (see §5). No natural-language prompt parsing — that was considered and
rejected: it would add a whole parsing/disambiguation layer for no real benefit, since API
consumers can trivially pass structured fields.

**Relationship to the Political Transparency App:** this reuses the Wikipedia heading-parse
pipeline designed and live-tested for that project's Phase 1 nominee-resolution feature (see
`tech-spec.md` §3, §6), but is a **separate, standalone product** — no shared database, no FEC
cross-referencing, no shared deployment. It can ship before that app's Phase 1 is finished.

**Key divergence from the Political Transparency App:** that app permanently excludes party
affiliation from all UI and payloads as a core product principle. This scraper does **not**
carry that constraint — its customers are developers who may have legitimate reasons to want
party data, and Wikipedia's own structure (party-labeled headings) makes it nearly free to
include. `party` is a first-class output field here. This is a deliberate, explicit divergence,
not an oversight — worth remembering if code or docs are ever shared between the two projects.

## 2. Goals

**v1 (build now):**
- Given a state, office, and election cycle, return the current candidate list for that race
  (`race_candidates`) — **U.S. Senate only**
- Source data live from Wikipedia (MediaWiki Action API), not a static/stale copy
- Distinguish real, current candidates (`declared`/`runoff_pending`/`nominee`) from primary
  losers, withdrawals, and other dropped statuses — same filtering logic as the main app
- Include `party` per candidate (see divergence note above), with true independents
  represented as `party: null`, not a fabricated value
- Cheap enough per-query (via caching) to be viable at Apify's pay-per-event pricing

**v2 (scoped, not designed):**
- Same `race_candidates` mode, expanded to non-Senate offices (House, Governor, state
  legislature, local) — new title-template patterns and per-office testing required, not
  designed yet (§3, §8).

**v3 (designed, deferred):**
- Given a state (+ cycle), return every election taking place in that state (`state_all`)

**v4 (designed, deferred):**
- Given a candidate name, return which race they're running in plus basic bio info
  (`candidate_search`)

## 3. Scope

**In scope for v1:**
- Single query mode: `race_candidates` (§5, §6.1, §7.1). Explicit `mode` field is still part
  of the input shape even with one mode, so later versions can rely on it without a breaking
  change (§5).
- **U.S. Senate only.** Revisit non-Senate offices (v2, below) once Senate coverage is proven
  across more than the ~4 races spot-checked so far (§8).
- Current election cycle only (2026) — title pattern is unverified for past cycles.
- Regular and special elections (confirmed live for the 2026 FL/OH specials)
- Runoff handling (`runoff_pending` status, `runoff_date` field)

**v2 — scoped, not yet designed:**
- Non-Senate offices for `race_candidates` (House, Governor, state legislature, local) —
  requires new title-template patterns and testing per office type that don't exist yet. Same
  `mode: "race_candidates"` input shape, just a wider `office` enum — not a new mode.

**v3/v4 — designed but explicitly deferred** (not being built now — see §6.2/§7.2 for
`state_all` and §6.3/§7.3 for `candidate_search`, kept in full here so these versions don't
require re-deriving the design when their turn comes):
- v3: `state_all` — all-offices-in-a-state lookup.
- v4: `candidate_search` — candidate-name lookup. As designed (§6.3), its category-membership
  check is Senate-specific, matching v1's scope — broadening it to match v2's office range
  would be a natural follow-on but isn't designed here.

**Explicitly out of scope, no version targeted:**
- FEC cross-referencing / candidate ID matching — this product is Wikipedia-only by design.
- Historical (pre-2026) cycles.

## 4. Data Source

**MediaWiki Action API** (`en.wikipedia.org/w/api.php`) — free, public, no API key. Same two
endpoints already live-verified against real 2026 Senate race data this session:

- `action=query&prop=extracts&explaintext=1&titles={title}` — primary lookup. Article text is
  heading-structured (`== {Party} primary ==` → `=== Candidates ===` →
  `==== Nominee/Declared/Advanced to runoff/... ====`) and machine-parseable.
- `action=query&list=search&srsearch={query}` — fallback when the constructed title doesn't
  resolve directly (confirmed necessary for some title variants); also the primary lookup path
  for `candidate_search` (§6.3), where the title isn't known in advance.
- `action=query&prop=categories&cllimit=500` — used by `candidate_search` to confirm a found
  page is actually a `{cycle} United States Senate` candidate (via
  `Category:Candidates in the {cycle} United States Senate elections`) before trusting the
  page as a match. **Confirmed live**: this category exists and is *cycle-wide*, not
  per-state — it cannot tell you *which* state's race a candidate is in, only that they're in
  one somewhere. State must come from intro-text extraction instead (§6.3).
- `action=parse&prop=wikitext&section=0` — used by `candidate_search` to pull the infobox for
  `party` (`political_party` field). **Confirmed live** the infobox does *not* expose the race/
  state/office — only the article's prose does (see §6.3).

**Licensing:** CC BY-SA 4.0. Commercial use is permitted. Extracted *facts* (candidate name,
status, party) can be sold freely; if any raw article text is ever returned verbatim (e.g. a
bio sentence), the output must carry attribution (`source_url`, `source_license`) — already
built into the output schema below, not an afterthought.

**Etiquette:** requests must set a descriptive `User-Agent` identifying this product, per
Wikipedia's API usage expectations — same practice used throughout this session's testing.

## 5. Input Schema

Discriminated on `mode`. Only `race_candidates` (Senate-only `office` values) is implemented in
v1; `state_all` and `candidate_search` are shown for their v3/v4 designs and should not be
built/exposed yet. v2 doesn't add a new mode — it just widens `race_candidates`'s `office` enum.

```json
{ "mode": "race_candidates", "state": "Michigan", "office": "senate", "cycle": 2026 }
```
```json
// v3 — designed, not built
{ "mode": "state_all", "state": "Michigan", "cycle": 2026 }
```
```json
// v4 — designed, not built
{ "mode": "candidate_search", "name": "Abdul El-Sayed", "cycle": 2026 }
```

`state` accepts full names or 2-letter codes, normalized via a state-code ↔ full-name
crosswalk (same lookup already flagged as needed infrastructure in the main app's spec, §12).
`cycle` on `candidate_search` scopes which "Candidates in the {cycle} ..." category to check
(§6.3) — without it there's no way to confirm the match is current vs. a past cycle.

## 6. Pipelines

### 6.1 `race_candidates` — **v1 build target** (v2 expands office scope)

*(This is the original v0.1 pipeline — Senate-only. v2 will need to generalize the title
templates in steps 2–3 per office type; not designed yet, see §3.)*

1. Normalize `state` to its full name.
2. Check a maintained per-cycle config (e.g. `{ 2026: ["FL", "OH"] }`) to determine whether
   this state's race is a special election, which changes the title template.
3. Construct the Wikipedia title deterministically:
   - Regular: `"{cycle} United States Senate election in {state}"`
   - Special: `"{cycle} United States Senate special election in {state}"`
4. Fetch via `prop=extracts`. If the title 404s, fall back to `list=search` and flag the
   result as `title_matched_via: "search_fallback"` so a low-confidence match is distinguishable
   from a direct hit.
5. Heading-parse the article text: split on `==`/`===`/`====` boundaries, walk into each
   party's `=== Candidates ===` subsection, and classify each listed candidate by their status
   heading.
6. Keep only candidates under `Declared`, `Advanced to runoff`, or `Nominee` headings. Drop
   everyone else (`Declined`, `Withdrawn`, `Did not file`, `Not on ballot`, `Disqualified`,
   `Eliminated in primary`, `Ineligible`) — same rule as the main app.
7. Record each kept candidate's party from the heading it was found under. For the
   `Independents` subsection specifically, set `party: null` rather than inventing one.
8. Extract `primary_date` (and `runoff_date`, if applicable) from the intro/background text.
   Two known sentence patterns exist — a single clean sentence for non-runoff states, a longer
   compound sentence for runoff states (confirmed live for Oklahoma) — extraction must handle
   both, not just the simpler one.
9. Cache the parsed result, keyed on `(state, office, cycle)`, with a TTL that expires once
   that race's own recorded primary/runoff date has passed. This keeps Wikipedia request volume
   reasonable and keeps marginal cost per paid Apify run close to zero.
10. Return the structured result (§7.1).

---

### 6.2 `state_all` — **v3, designed/deferred**

1. Normalize `state` to its full name.
2. Construct the Wikipedia title: `"{cycle} {state} elections"` (confirmed live for Michigan —
   pageid 74607542, clean `==`-level headings: Federal → US Senate / US House, Executive →
   Governor / Secretary of State / Attorney General, Legislature → State Senate / State House,
   Judiciary → Supreme Court, plus local boards and ballot initiatives).
3. Fetch via `prop=extracts`. If the title 404s, fall back to `list=search`, same
   `title_matched_via` flagging as §6.1 step 4. **Not yet verified whether this title pattern
   holds for every state** — only Michigan spot-checked (§8).
4. Heading-parse into a flat list of `{ office, race_title, source_url }` entries — one per
   race/section found (Senate, House, Governor, etc.), not full candidate lists.
5. For any entry where `office == "senate"`, additionally set `resolvable_via:
   "race_candidates"` so callers know that race can be queried in full via the `race_candidates`
   mode. Non-Senate entries are resolvable too once v2 ships — return title/link only until then.
6. Cache keyed on `(state, cycle)`.
7. Return the structured result (§7.2).

---

### 6.3 `candidate_search` — **v4, designed/deferred**

1. Attempt a direct title fetch on `name` via `prop=extracts`. If it 404s or disambiguates,
   fall back to `list=search&srsearch={name}` and take the top hit, flagging
   `title_matched_via: "search_fallback"`.
2. Fetch `prop=categories` on the resolved page. Confirm membership in
   `Category:Candidates in the {cycle} United States Senate elections`. **If absent, return a
   `not_found`/`no_match` result rather than guessing** — this category check is what keeps the
   mode Senate-only per §3 and prevents returning a stale/irrelevant person page. (Widening this
   to non-Senate offices, once v2 exists, would mean checking additional office-specific
   categories — not designed here.)
3. Extract the race from intro prose via regex, matching the same two title patterns as §6.1
   step 3 (regular and special): `"{cycle} United States Senate (special )?election in
   ({state})"`. **Confirmed live**: this sentence pattern is present and reliable (verified on
   Abdul El-Sayed's page: "...the Democratic nominee in the 2026 United States Senate election
   in Michigan"). If no match is found in the intro, scan the full extract before failing.
4. Once `state` is resolved, optionally re-run §6.1 to get the candidate's current `status`
   within that race (the candidate's own page doesn't reliably state their status — e.g.
   "nominee" vs. "declared" — as cleanly as the race page does).
5. Pull `party` from the infobox (`political_party` field via `action=parse&prop=wikitext`),
   normalized the same way as §6.1's heading-derived party values for consistency.
6. Cache keyed on `(name, cycle)`.
7. Return the structured result (§7.3).

## 7. Output Schema

Each mode returns `source_license` (`"CC BY-SA 4.0"`), `title_matched_via`
(`"direct"` | `"search_fallback"`), `parse_confidence` (`"high"` | `"needs_review"`), and
`last_updated`, in addition to the mode-specific fields below. `parse_confidence` is `high`
for a direct title match with cleanly-headed/parseable content, `needs_review` when the search
fallback was used or the expected structure didn't match cleanly.

### 7.1 `race_candidates` — **v1 build target** (v2 expands office scope)

```json
{
  "query": { "state": "Michigan", "office": "senate", "cycle": 2026 },
  "source_url": "https://en.wikipedia.org/wiki/2026_United_States_Senate_election_in_Michigan",
  "title_matched_via": "direct",
  "primary_date": "2026-08-04",
  "runoff_date": null,
  "candidates": [
    { "name": "Abdul El-Sayed", "party": "Democratic", "status": "nominee", "bio": "Former Wayne County health director..." },
    { "name": "Mike Rogers", "party": "Republican", "status": "nominee", "bio": "Former U.S. Representative..." }
  ]
}
```

`status` values: `declared` | `runoff_pending` | `nominee`.

---

### 7.2 `state_all` — **v3, designed/deferred**

```json
{
  "query": { "state": "Michigan", "cycle": 2026 },
  "source_url": "https://en.wikipedia.org/wiki/2026_Michigan_elections",
  "races": [
    { "office": "senate", "race_title": "United States Senate", "resolvable_via": "race_candidates" },
    { "office": "house", "race_title": "United States House of Representatives", "resolvable_via": null },
    { "office": "governor", "race_title": "Governor and lieutenant governor", "resolvable_via": null }
  ]
}
```

### 7.3 `candidate_search` — **v4, designed/deferred**

```json
{
  "query": { "name": "Abdul El-Sayed", "cycle": 2026 },
  "source_url": "https://en.wikipedia.org/wiki/Abdul_El-Sayed",
  "race": { "office": "senate", "state": "Michigan", "election_type": "regular" },
  "party": "Democratic",
  "status": "nominee",
  "bio": "Former Wayne County health director...",
  "not_found": false
}
```

`race` is `null` and `not_found: true` when the category check (§6.3 step 2) fails to confirm
the person as a current-cycle Senate candidate.

## 8. Known Risks & Limitations

Carried over from the main app's research, but with a higher bar here since a parsing failure
is now a paying customer's broken result, not an internal admin-reviewed data point:

- **Heading structure and status vocabulary aren't perfectly consistent across articles.**
  Confirmed live: New Hampshire's Republican section had a "Did not file" subsection missing
  its `====` markup entirely (appeared as bare text). The parser needs a fallback for
  malformed/missing headings, not pure heading-boundary parsing.
- **Party names parsed from heading text can carry non-party qualifier words.** Confirmed live:
  South Carolina's original Republican nominee died after being nominated, triggering a second
  "Special Republican primary" section. `party = header.removesuffix(" primary")` takes the
  whole heading as the party name, so the candidate's `party` comes back as `"Special
  Republican"` instead of `"Republican"`. Not yet fixed — needs a qualifier-prefix strip (e.g.
  "Special "/"Initial ") before trusting heading text as a clean party name.
- **A party's nominee can be replaced by a secondary process (convention, re-vote) nested under
  unrelated-looking headings.** Confirmed live: Maine's original Democratic primary winner
  withdrew after nomination; the real nominee was chosen later under a separate "Democratic
  nominating convention" heading, with narrative headings ("Platner's withdrawal") in between.
  `find_candidates_list_elem`'s forward search only stops at `h2`/`h3` headings whose *text*
  also matches a party-boundary pattern (ends with "primary"/"Party", or is "Independents") —
  since neither intervening heading matches that pattern, the search correctly continues
  through them and finds the real nominee. This works today, but it's incidental rather than a
  principled "this is a replacement-nominee section" detection — a differently-worded
  convention/withdrawal page could use heading text that happens to match the boundary pattern
  and stop the search early again.
- **Disambiguation risk**: `"{state} Senate election"` (state legislature) vs `"United States
  Senate election in {state}"` (federal) are different pages with similar names — confirmed
  live for Michigan and Florida. Title construction must always use the precise federal
  phrasing.
- **Runoff-state date sentences use different, less predictable phrasing** than non-runoff
  states — only spot-checked against one example (Oklahoma) so far. Needs testing against a
  couple more runoff states (Texas, Louisiana) before this is trusted broadly.
- **Special-election detection is manually maintained**, not automatic — the per-cycle config
  (§6, step 2) needs a human to update it each cycle, since Wikipedia's data doesn't expose
  "this is a special election" as a queryable flag on its own.
- **Only spot-checked, not exhaustively tested** — three regular-election articles and one
  runoff article were verified this session. Before charging money per query, worth testing
  against a wider sample of the full candidate set (all 35 2026 Senate races) to catch parser
  edge cases before customers do.
- **`state_all` title pattern only verified for one state.** `"{cycle} {state} elections"`
  worked cleanly for Michigan, but the alternate title guessed first
  (`"{cycle} United States elections in {state}"`) does **not** exist (confirmed 404). Needs
  spot-checking across a few more states before trusting the pattern broadly — naming
  conventions for this kind of umbrella page aren't guaranteed uniform.
- **`state_all` heading structure will vary in office count/order per state** — Michigan had
  university boards and a ballot proposal that many states won't have. The parser needs to key
  off known office-name headings (Senate, House, Governor, etc.) rather than assuming a fixed
  section count/order.
- **No per-state candidate category exists for `candidate_search`.** Confirmed live: Wikipedia
  only has a cycle-wide `Category:Candidates in the {cycle} United States Senate elections`,
  not one per state. State must come from regex-matching intro prose (§6.3 step 3), which is a
  softer signal than a category membership check — a candidate whose intro doesn't follow the
  standard "nominee in the {cycle} ... election in {state}" phrasing will fail to resolve and
  needs a `needs_review`/`not_found` path rather than a wrong guess.
- **Name collisions/disambiguation** for `candidate_search` are unhandled — a common name could
  resolve to the wrong Wikipedia page entirely, and the category check (§6.3 step 2) only
  catches this if the wrong page also happens to not be a 2026 Senate candidate. Worth testing
  against at least one deliberately ambiguous name before trusting this mode broadly.

## 9. Monetization

Sold via the Apify Store. Two pricing models are available to Actor creators:

- **Pay-per-event** — a fixed price for a defined event (e.g. "one race returned").
- **Pay-per-usage** — no creator-set price; users pay Apify directly for compute/proxy/storage.

Pay-per-event is the better fit here, given the low marginal compute cost once caching (§6,
step 9) is in place. **Apify's exact revenue-share cut was not found in their public pricing
docs as of this session** — needs direct confirmation from Apify before finalizing a price
point.

## 10. Open Questions

- Exact per-query price point — blocked on confirming Apify's revenue-share cut. Different
  phases may warrant different per-event pricing (`state_all` is a lighter payload than
  `race_candidates`/`candidate_search`).
- v2 design: what new title-template patterns and per-office parsing rules non-Senate offices
  need — not designed yet, just scoped (§3).
- Whether historical-cycle support (pre-2026) is worth adding, and whether any of the title
  construction patterns even hold for older cycles — untested.
- Whether `state_all` (v3) should attempt to resolve non-Senate races too once v2 ships, or
  stay link-only for those permanently.
- Whether `candidate_search` (v4) should widen its category check to non-Senate offices once
  v2 ships, matching `race_candidates`'s scope at that point (§3, §6.3 step 2).
