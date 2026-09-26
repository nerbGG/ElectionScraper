"""Module defines the main entry point for the Apify Actor.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

from __future__ import annotations

import asyncio

from apify import Actor, Event

from .src.render_report import render_race_report
from .src.simple_wiki_search import RaceCandidatesResult, handle_simple_wiki


async def main() -> None:
    """Define a main entry point for the Apify Actor.
    This coroutine is executed using `asyncio.run()`, so it must remain an asynchronous function for proper execution.
    Asynchronous execution is required for communication with Apify platform, and it also enhances performance in
    the field of web scraping significantly.
    """
    # Enter the context of the Actor.
    async with Actor:
        # Handle graceful abort - Actor is being stopped by user or platform
        async def on_aborting() -> None:
            """Persist state and exit promptly when the Actor is stopped."""
            # Persist any state, do any cleanup you need, and terminate the Actor using
            # `await Actor.exit()` explicitly as soon as possible. This will help ensure that
            # the Actor is doing best effort to honor any potential limits on costs of a
            # single run set by the user.
            # Wait 1 second to allow Crawlee/SDK state persistence operations to complete
            # This is a temporary workaround until SDK implements proper state persistence in the aborting event
            await asyncio.sleep(1)
            await Actor.exit()

        Actor.on(Event.ABORTING, on_aborting)

        # Retrieve the Actor input, and use default values if not provided.
        actor_input = await Actor.get_input() or {}

        year = actor_input.get("year", 2026)
        office = actor_input.get("office", "s")
        state = actor_input["state"]

        try:
            result = await asyncio.to_thread(handle_simple_wiki, year, office, state)
            Actor.log.info("--------RESULT------------------:")
            Actor.log.info(result)
            Actor.log.info("--------------------------------\n")

        except Exception as e:  # noqa: BLE001 — top-level entry point; log and exit(1) on any failure mode
            Actor.log.error(f"Wikipedia lookup failed, exiting...: {e}")
            await Actor.exit(exit_code=1)
            return

        if result is None:
            Actor.log.error(
                "handle_simple_wiki returned no result (unimplemented query mode)"
            )
            await Actor.exit(exit_code=1)
            return

        if isinstance(result, RaceCandidatesResult):
            election_data = result.election.model_dump(mode="json")
            # Store the extracted data to the default dataset.
            await Actor.push_data({**election_data, "query_mode": result.query_mode})
            html_report = render_race_report(result.election)
            await Actor.set_value("OUTPUT", html_report, content_type="text/html")
