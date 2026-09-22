import html
from datetime import datetime

_PARTY_COLORS = {
    "Democratic": "#2f5aa8",
    "Republican": "#a3372f",
    "Libertarian Party": "#a67c1e",
    "Green Party": "#2f7a52",
    "Write in": "#5b6472",
}
_DEFAULT_PARTY_COLOR = "#6a4f8c"
_INDEPENDENT_COLOR = "#5b6472"

_STYLE = """<style>
  :root {
    color-scheme: light;
    --ink: #1c2541;
    --paper: #f1f2f1;
    --surface: #ffffff;
    --rule: #d9dce0;
    --muted: #5b6472;
    --seal: #8c2f39;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      color-scheme: dark;
      --ink: #e9eaef;
      --paper: #14171f;
      --surface: #1b1f29;
      --rule: #2c313c;
      --muted: #9aa1ae;
      --seal: #d1707c;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font-family: "Public Sans", -apple-system, "Segoe UI", Roboto, sans-serif;
    font-variant-numeric: tabular-nums;
    padding-block: 2.5rem 4rem;
  }
  main { max-width: 680px; margin: 0 auto; padding-inline: 1.25rem; }
  .eyebrow {
    margin: 0;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--seal);
  }
  h1 {
    font-family: "Fraunces", Georgia, "Times New Roman", serif;
    font-weight: 600;
    font-size: clamp(1.6rem, 4vw, 2.15rem);
    line-height: 1.2;
    margin: 0.3rem 0 0.4rem;
    text-wrap: balance;
  }
  .byline { margin: 0; color: var(--muted); font-size: 0.92rem; }
  .rule-double {
    margin: 1.4rem 0 1.6rem;
    border: none;
    border-top: 3px solid var(--ink);
    border-bottom: 1px solid var(--ink);
    height: 4px;
  }
  .facts {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 1.25rem;
    margin: 0 0 2.2rem;
    padding: 0;
  }
  .fact { margin: 0; }
  .fact dt {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .fact dd {
    margin: 0.2rem 0 0;
    font-size: 1.02rem;
    font-weight: 600;
  }
  .section-label {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 0 0 0.6rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--rule);
  }
  .roster { list-style: none; margin: 0; padding: 0; }
  .roster-item {
    display: flex;
    gap: 0.9rem;
    padding: 0.9rem 0;
    border-bottom: 1px solid var(--rule);
  }
  .flag {
    flex: 0 0 4px;
    border-radius: 2px;
    background: var(--flag-color, var(--muted));
  }
  .roster-body { flex: 1; min-width: 0; }
  .roster-name-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.75rem;
    flex-wrap: wrap;
  }
  .roster-name { font-weight: 600; font-size: 1.02rem; }
  .roster-party {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--flag-color, var(--muted));
    white-space: nowrap;
  }
  .roster-description {
    margin: 0.3rem 0 0;
    color: var(--muted);
    font-size: 0.92rem;
    line-height: 1.45;
  }
  .empty { color: var(--muted); font-style: italic; margin: 0; padding: 0.9rem 0; }
  footer {
    margin-top: 2.5rem;
    color: var(--muted);
    font-size: 0.78rem;
  }
</style>"""


def _format_date(value: str | None) -> str:
    """Convert an ISO date to 'Month D, YYYY'; pass through anything else, or 'Unknown'."""
    if not value:
        return "Unknown"
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")  # noqa: DTZ007
    except ValueError:
        return value
    return f"{parsed:%B} {parsed.day}, {parsed.year}"


def _party_color(party: str | None) -> str:
    if party is None:
        return _INDEPENDENT_COLOR
    return _PARTY_COLORS.get(party, _DEFAULT_PARTY_COLOR)


def _roster_item(candidate: dict) -> str:
    name = html.escape(candidate["name"])
    party_label = html.escape(candidate["party"] or "Independent")
    color = _party_color(candidate["party"])
    description = html.escape(candidate["description"])
    description_html = (
        f'<p class="roster-description">{description}</p>' if description else ""
    )
    return f"""    <li class="roster-item" style="--flag-color:{color}">
      <div class="flag"></div>
      <div class="roster-body">
        <div class="roster-name-row">
          <span class="roster-name">{name}</span>
          <span class="roster-party">{party_label}</span>
        </div>
        {description_html}
      </div>
    </li>"""


def _fact(label: str, value: str) -> str:
    return f"""    <div class="fact">
      <dt>{html.escape(label)}</dt>
      <dd>{html.escape(value)}</dd>
    </div>"""


def render_race_report(result: dict) -> str:
    """Render a race result dict (as returned by get_race_candidates) as a standalone HTML page."""
    office = result.get("office") or ""
    state_label = result.get("state_label") or ""
    year = result.get("year")
    title = f"{year} {office} Election — {state_label}"

    candidates = result.get("candidates", [])
    count = len(candidates)
    roster = "\n".join(_roster_item(c) for c in candidates)
    roster_section = (
        roster
        if candidates
        else '    <p class="empty">No candidates found for this race.</p>'
    )

    facts = [
        _fact("Election Day", _format_date(result.get("election_date"))),
        _fact("Primary", _format_date(result.get("primary_date"))),
        _fact("Runoff", _format_date(result.get("runoff_date"))),
    ]
    if result.get("is_special"):
        facts.append(_fact("Type", "Special election"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
{_STYLE}
</head>
<body>
<main>
  <header>
    <p class="eyebrow">Election Results Report</p>
    <h1>{html.escape(title)}</h1>
    <p class="byline">Sourced from Wikipedia · {count} candidate{"s" if count != 1 else ""} on record</p>
  </header>
  <hr class="rule-double">

  <dl class="facts">
{chr(10).join(facts)}
  </dl>

  <h2 class="section-label">Candidates on the Ballot</h2>
  <ul class="roster">
{roster_section}
  </ul>

  <footer>Generated by the Wikipedia Election Scraper Actor</footer>
</main>
</body>
</html>
"""
