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

### 5. Create a Python virtual environment

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

### 6. Install dependencies

```bash
pip install -r requirements.txt
```

### 7. Install the pre-commit git hook

```bash
pre-commit install
```

This wires up the hooks in [.pre-commit-config.yaml](.pre-commit-config.yaml) to run
automatically on `git commit` (Ruff lint/format, whitespace/EOF checks, secret scanning). It's a
one-time, per-clone setup step — installing the `pre-commit` package via step 6 does not do this
on its own. The same checks also run in CI on every push/PR
([.github/workflows/pre-commit.yml](.github/workflows/pre-commit.yml)), so skipping this step
just means you'll find out about failures from CI instead of locally.

### 8. Install the Ruff extension (recommended)

Install the [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
(`charliermarsh.ruff`) in VS Code. It lints and formats Python using the same tool as the
`ruff-check`/`ruff-format` pre-commit hooks (§ [.pre-commit-config.yaml](.pre-commit-config.yaml)),
so what you see in the editor matches what runs at commit time. Format-on-save for `.py` files
is already configured in this repo's [.vscode/settings.json](.vscode/settings.json) — no
further setup needed once the extension is installed.

### 9. Run the Actor locally

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

### 10. Push to Apify

Once your changes are ready, deploy the current code to the Apify platform:

```bash
apify push
```

This uploads the Actor per the settings in [.actor/actor.json](.actor/actor.json) and kicks off
a build. Pass `--no-wait-for-finish` to return immediately instead of waiting for the build to
complete. See [Managing Apify versions](#managing-apify-versions) below for choosing which
version/tag a push goes to.

## Managing Apify versions

This section covers how the **Apify platform** tracks this Actor's versions and builds when you
`apify push`/`apify pull` — a separate concept from this repo's own git history.

> **Not the same as the spec's v1–v4.** Apify's `version` field (`.actor/actor.json`, format
> `MAJOR.MINOR`, e.g. `0.1`) tracks *deployment/build history on the platform*.
> [wiki-tech-spec.md](wiki-tech-spec.md)'s `v1`–`v4` track *feature scope* (Senate-only → all
> offices → `state_all` → `candidate_search`). These two numbering schemes are independent and
> won't stay in sync — shipping the spec's "v2" feature set does **not** mean the Apify version
> should become `2.0` (that jump is reserved for a breaking change, see below, not a feature
> addition).

**Version format:** `version` in `.actor/actor.json` is `MAJOR.MINOR` only — there's no patch
slot at that level (e.g. `"0.1"`, `"1.0"`, not `"0.1.2"`). Every build gets its own
auto-incrementing `MAJOR.MINOR.BUILD` number (e.g. `1.2.345`), and multiple versions (`0.1`,
`0.2`, ...) can exist on the platform at the same time, each with its own independent sequence
of builds.

**Pushing/pulling a specific version:**
- `apify push` reads `version` from `.actor/actor.json` by default. Override it per-push with
  `-v`/`--version=<value>` without editing the file.
- `-f`/`--force` overrides a newer remote version if you need to push backwards or sideways.
- `-b`/`--build-tag=<value>` tags the resulting build (see next section).
- `apify pull -v <value>` fetches a specific version's code from the platform; without `-v`, it
  pulls the highest version.

**Build tags:** the default tag is `latest`, and each push under the same version
auto-increments the build number (e.g. `0.1.1`, `0.1.2`, ...). Note that a tag is assigned when
a build is *created* — Apify's docs don't document a way to retroactively move `latest` onto a
build that was pushed earlier without a tag.

**The workflow used in this project:** push intermediate builds freely while iterating, and once a batch of changes is actually ready, do one final `apify push` to update the version number (either Major or minor). In the apify console, run options let you pick which build/tag to run, and the Actor's Settings tab lets you update its default version.

**When to bump the version:** for non-breaking, iterative changes, keep the same `MAJOR.MINOR`
and let the build number auto-increment on each push. Bump `MAJOR` for a breaking change (e.g.
`1.0` → `2.0`). Apify's own guidance on exactly when to bump `MINOR` specifically is thin —
treat it as a judgment call, not a hard rule.

```bash
# Push the current code as version 0.1 (first real candidate build — the "0.1" here is
# unrelated to the spec's "v1", see disambiguation note above)
apify push --version 0.1

# Pull the code for a specific platform version
apify pull --version 0.1

# Force-push over a newer remote version (use sparingly)
apify push --version 0.1 --force
```

**Note:** `.actor/actor.json` still has template placeholder values from the original
`python-crawlee-beautifulsoup` Actor template (`name: "my-actor"`, plus `title`/`description`) —
worth updating before the first real Store-facing push.

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
