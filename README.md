# Wikipedia Election Scraper (Apify Actor)

An [Apify Actor](https://apify.com/actors) that looks up a U.S. Senate race by state, office,
and election cycle, and returns the current candidate list (name, party, status, short bio)
sourced live from Wikipedia. It's built to eventually be sold on the Apify Store to developers
and researchers who need normalized election-candidate data without building their own
Wikipedia-parsing pipeline.

The current build target is the `race_candidates` query mode only (U.S. Senate, 2026 cycle).
Two additional query modes — an all-elections-in-a-state lookup and a candidate-name search —
are fully designed but intentionally deferred. See [wiki-tech-spec.md](wiki-tech-spec.md) for
the full spec, data-source notes, and known risks/limitations.

## Prerequisites

- **Node.js** (18+) and npm — needed to install the Apify CLI
- **Python** 3.11+ — needed to run the Actor itself

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/nerbGG/ElectionScraper.git
cd ElectionScraper
```

### 2. Install Node.js

The Apify CLI's npm install method (step 3) needs Node.js and npm on your machine first.
Download and run the installer from [nodejs.org](https://nodejs.org) (LTS version), or use a
version manager — [nvm](https://github.com/nvm-sh/nvm) on macOS/Linux,
[nvm-windows](https://github.com/coreybutler/nvm-windows) on Windows. Verify it installed
correctly:

```bash
node --version
npm --version
```

If you'd rather skip Node.js entirely, the Apify CLI also has a standalone install script
(macOS/Linux/Windows) and a Homebrew formula — see step 3.

### 3. Install the Apify CLI

```bash
npm install -g apify-cli
```

Other install methods (Homebrew, a standalone install script with no Node.js required) are
listed in the [Apify CLI installation docs](https://docs.apify.com/cli/docs/installation).
Verify it installed correctly:

```bash
apify --version
```

### 4. Log in to Apify

```bash
apify login
```

This opens an interactive flow to authenticate your Apify account and stores the credentials
locally (`~/.apify/auth.json`) for use by every other `apify` command below. To log in
non-interactively instead (e.g. in CI), pass a token: `apify login --token <your-api-token>`.

### 5. Pull the Actor

Syncs your local copy with whatever's currently deployed on the Apify platform, in case the
platform version is ahead of what's in this repo (e.g. edited via the Apify Console UI):

```bash
apify pull nerb1x/wiki-elections-scraper
```

### 6. Create a Python virtual environment

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 7. Install dependencies

```bash
pip install -r requirements.txt
```

### 8. Run the Actor locally

```bash
apify run --input '{"year": 2026, "office": "s", "state": "MI"}'
```

Input fields (defined in [.actor/input_schema.json](.actor/input_schema.json)):

| Field    | Type    | Notes                                                              |
|----------|---------|----------------------------------------------------------------------|
| `year`   | integer | Election cycle. Defaults to `2026`.                                 |
| `office` | string  | `"s"` (Senate), `"p"` (Presidential), or `"h"` (House).              |
| `state`  | string  | Currently limited to `"MA"`, `"MI"`, `"OK"` — full 50-state support is pending the state-code crosswalk described in the spec. |

Useful flags:
- `apify run` (no `--input`) — reuses whatever's already saved in `storage/key_value_stores/default/INPUT.json`
- `apify run --purge --input '{...}'` — wipes local storage (dataset/key-value store/request queue) before the run, so output from a previous run doesn't linger
    - ex: `apify run --input '{"year": 2026, "office": "s", "state": "MI"}'`
- `apify run --input-file ./some-input.json` — read input from a file instead of inline JSON

### 9. Push to Apify

Once your changes are ready, deploy the current code to the Apify platform:

```bash
apify push
```

This uploads the Actor per the settings in [.actor/actor.json](.actor/actor.json) and kicks off
a build. Pass `--no-wait-for-finish` to return immediately instead of waiting for the build to
complete.

## Project structure

```text
.actor/
├── actor.json          # Actor config: name, version, storage/schema references, Dockerfile path
├── input_schema.json   # Defines the Actor's input fields, types, and defaults — also renders
│                        #   the input form in the Apify Console
├── dataset_schema.json # Defines how output items are displayed as a table in the Console's
│                        #   "Output" tab (which fields show as columns, their format)
└── output_schema.json  # Points the Console's Output tab at the dataset API endpoint
my_actor/
├── __main__.py          # Entry point invoked by `python -m my_actor` (see Dockerfile)
├── main.py               # Actor logic: reads input, will run the Wikipedia fetch/parse
│                          #   pipeline, and calls Actor.push_data()
└── routes.py             # Crawlee request routing (scaffolded, not yet wired up)
storage/                  # Local-only storage emulating the Apify platform, created by
│                          #   `apify run`. NOT synced to the cloud — each `apify run` reads/writes
│                          #   here instead of hitting real Apify storage.
├── datasets/default/     # Every item passed to `Actor.push_data()` lands here as JSON —
│                          #   this is the Actor's actual output
├── key_value_stores/default/ # Holds INPUT.json (the input for the next `apify run`) plus any
│                          #   other files/config the Actor reads or writes via Actor.set_value()
└── request_queues/       # Pending crawl requests (used once the Crawlee pipeline is wired up)
Dockerfile                # Container image definition used when the Actor runs on Apify
requirements.txt          # Python dependencies
wiki-tech-spec.md         # Source-of-truth spec: schema, pipeline, data source, known risks
```

**Note:** `main.py` currently just echoes the input straight back to the dataset — the actual
Wikipedia-fetch/parse pipeline described in the spec isn't implemented yet, so a local run right
now only confirms your input was received, not real candidate data.

## Resources

- [wiki-tech-spec.md](wiki-tech-spec.md) — full spec for this Actor
- [Apify CLI reference](https://docs.apify.com/cli/docs/reference)
- [Apify Python SDK documentation](https://docs.apify.com/sdk/python)
- [Crawlee for Python documentation](https://crawlee.dev/python/docs/quick-start)
