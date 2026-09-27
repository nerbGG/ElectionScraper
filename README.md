# Wiki Election Api

Wikipedia publishes the full candidate lineup for every U.S. Senate race, but each state's page
is laid out a little differently — two-party primaries, third-party and independent sections,
write-in candidates, blanket-primary states — so reading it by hand means checking dozens of
page structures one state at a time. This Actor takes a state and returns one structured record
for that state's Senate race: the candidates on the ballot (name, party, short bio), the
election/primary/runoff dates, and whether it's a special election — sourced live from
Wikipedia.

## What it does

- Returns one record per Senate race, with the full candidate roster — name, party, and short
  bio — parsed out of Wikipedia's own article text
- Detects candidates and party affiliation across every layout Wikipedia currently uses for a
  2026 Senate race page: two-party primaries, third-party/independent sections, write-in
  candidates, and blanket-primary (top-four) states
- Resolves the real election, primary, and runoff dates for the race from Wikipedia's own
  election-dates table
- Flags special elections (`is_special`)
- Handles a state with no Senate race on the ballot that cycle gracefully — the run succeeds
  with an `error` field and an empty candidate list, instead of failing
- Also renders a standalone HTML report of the result, saved alongside the JSON dataset

## Use cases

| You need to                                            | How this Actor does it                                                      |
|---------------------------------------------------------|-------------------------------------------------------------------------------|
| Track who's running in your state's Senate race         | Pass your state and read `candidates`                                        |
| Know exactly when to vote                                | Read `election_date`, `primary_date`, `runoff_date`                          |
| Build a voter-info tool without parsing Wikipedia yourself | Get structured `name`/`party`/`description` per candidate instead of raw wikitext |
| Watch for late-entry or withdrawn candidates             | Schedule the run and diff `candidates` between runs                          |
| Summarize a race for a newsletter or report              | Feed `candidates` and the dates to a model over MCP                          |
| Handle a state with no Senate race that cycle            | Check the `error` field instead of the run failing                           |

## Quick start

1. Click **Try for free**.
2. Set **State** to the two-letter US state code (e.g. `MI`, `OH`, `TX`).
3. Click **Start**. The result appears within seconds.
4. Export as JSON, CSV, Excel, or XML, or read the dataset over the API.

This version is fixed to the 2026 U.S. Senate general election cycle — configurable year/office
inputs and additional query modes are on the roadmap (see [getting-started.md](getting-started.md)).

## Input

| Field   | Type                     | Default | What it controls                              |
|---------|--------------------------|---------|-------------------------------------------------|
| `state` | string (one of 50 US states) | `MI` | The state whose 2026 Senate race to look up |

```json
{
    "state": "MI"
}
```

## Output

One dataset item per run.

| Field group | Fields                                                        |
|-------------|----------------------------------------------------------------|
| Identity    | `year`, `office`, `state`, `state_label`, `query_mode`          |
| Candidates  | `candidates` (each: `name`, `description`, `party`)             |
| Dates       | `election_date`, `primary_date`, `runoff_date`                  |
| Status      | `is_special`, `error`                                           |

```json
{
    "year": 2026,
    "office": "Senate",
    "state": "MI",
    "state_label": "Michigan",
    "election_date": "2026-11-03",
    "primary_date": "2026-08-04",
    "runoff_date": null,
    "is_special": false,
    "error": null,
    "candidates": [
        {
            "name": "Abdul El-Sayed",
            "description": "former Wayne County health director (2023–2025) and candidate for governor in 2018",
            "party": "Democratic"
        },
        {
            "name": "Mike Rogers",
            "description": "former U.S. representative from Michigan's 8th congressional district (2001–2015) and nominee for U.S. Senate in 2024",
            "party": "Republican"
        }
    ],
    "query_mode": "race_candidates"
}
```

A standalone HTML report of the same result is also saved to the run's key-value store
(`OUTPUT`), linked from the Output tab.

For a state with no Senate race on the ballot that cycle (e.g. New York in 2026), the run still
succeeds — `candidates` comes back empty and `error` explains why, instead of the run failing:

```json
{
    "year": 2026,
    "office": "Senate",
    "state": "NY",
    "state_label": "New York",
    "election_date": null,
    "primary_date": null,
    "runoff_date": null,
    "is_special": false,
    "error": "No race found for Senate in New York (2026)",
    "candidates": [],
    "query_mode": "race_candidates"
}
```

## Integrations

Run it over the API and get the rows back in one call:

```bash
curl -X POST "https://api.apify.com/v2/acts/YOUR_USERNAME~wiki-elections-api/run-sync-get-dataset-items?token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"state": "MI"}'
```

From Python:

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_TOKEN")
run = client.actor("YOUR_USERNAME/wiki-elections-api").call(
    run_input={"state": "MI"}
)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["candidates"])
```

Give an AI agent the Actor over MCP:

```json
{
    "mcpServers": {
        "apify": {
            "url": "https://mcp.apify.com/?actors=YOUR_USERNAME/wiki-elections-api"
        }
    }
}
```

Schedules run it on any cron, webhooks fire when a run finishes, and platform integrations push
the dataset to Google Sheets, Slack, Airtable, Zapier, or your own endpoint.

## Cost

Pricing for this Actor hasn't been finalized in Apify Console yet — check the **Pricing** tab on
the Store listing for the current model (pay-per-result, pay-per-event, or a free/rental tier).

## Troubleshooting

| Issue                                                  | Solution                                                                                     |
|----------------------------------------------------------|------------------------------------------------------------------------------------------------|
| `error` is set / `candidates` is empty                   | That state has no Senate race in the 2026 cycle — not every state votes for Senate every cycle. Check which states are actually up in 2026. |
| Party or description looks off for one candidate         | Wikipedia's page layout varies by state — most known variants (primaries, third parties, write-ins, blanket primaries) are handled, but an unusual layout can still slip through. Open an issue with the state. |
| The run fails outright (not a graceful `error` field)     | Likely an unexpected Wikipedia API issue (page renamed, API outage) rather than "no race" — check the run log. |
| I need more than one state                                | Today the Actor takes a single `state` per run — schedule it per state, or call it once per state, to cover a portfolio of states. |

## FAQ

**Does Wikipedia have a public API?**
Yes. This Actor isn't selling API access — it gives you structured, per-candidate records
(name, party, short bio) instead of raw wikitext, handles the page-layout differences between
states for you, resolves the real election dates, and adds Apify's scheduling/integrations
around it.

**What states are covered?**
All 50, but only for a cycle where that state actually has a Senate race on the ballot — a
state with none returns a graceful `error` result rather than data.

**Why don't I see a different year or office?**
Today the Actor is fixed to the 2026 U.S. Senate general election. Configurable year/office
inputs and additional query modes (all races in a state, candidate name search) are on the
roadmap — see [getting-started.md](getting-started.md).

**Can I get this data in Python?**
Yes, with the `apify-client` package as shown above. It returns parsed JSON.

**Can I get the data into Excel or Google Sheets?**
Yes. Export the dataset as XLSX or CSV, or connect the Google Sheets integration so each run
appends to a sheet.

**Can an AI agent call this Actor?**
Yes. Add it to an MCP client with the config above.

**Is it legal to scrape Wikipedia?**
Wikipedia's content is openly licensed (CC BY-SA) and its API is built for exactly this kind of
reuse. This Actor reads only public candidate and election information already published there.

## Changelog

- **1.2** — Added a standalone HTML report per run, alongside the JSON dataset.
- **1.1** — Actor metadata cleanup (title, description, input schema description).
- **1.0** — First public-ready release: full 50-state coverage, candidate name/party/description
  parsing across every known Wikipedia page layout (primaries, third parties/independents,
  write-ins, blanket primaries), real election/primary/runoff dates, and graceful handling of
  states with no race that cycle.
- **0.x** — Internal development builds.

## Feedback

Found a state whose Wikipedia layout parses incorrectly, or a race that's missing data? Open an
issue on the issues with the state and what you expected.
