"""Module defines the main entry point for the Apify Actor.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

from __future__ import annotations

import asyncio

from apify import Actor, Event
from crawlee.crawlers import BeautifulSoupCrawler

from .routes import router


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
        
        year = actor_input.get('year', 2026)
        office = actor_input.get('office', 's')
        state = actor_input.get('state', 'MI')
    
        data = {
            "year":year,
            "office":office,
            "state":state,
        }

         # Store the extracted data to the default dataset.
        await Actor.push_data(data)

        # await Actor.push_data({year,office,state})
        await Actor.exit()
        # start_urls = [
        #     url.get('url')
        #     for url in actor_input.get(
        #         'start_urls',
        #         [{'url': 'https://apify.com'}],
        #     )
        # ]

        # Exit if no start URLs are provided.
        # if not start_urls:
        #     Actor.log.info('No start URLs specified in Actor input, exiting...')
        #     await Actor.exit()

        # Create a crawler.
        # crawler = BeautifulSoupCrawler(
        #     # Limit the crawl to max requests. Remove or increase it for crawling all links.
        #     max_requests_per_crawl=10,
        #     # Set the request handler to the request router defined in routes.py.
            # request_handler=router,
        # )

        # Run the crawler with the starting requests.
        # await crawler.run(start_urls)
        
# def check_state(state: str)-> str | None:
#     all_states = [
#         "alabama","alaska","arizona","arkansas","california","colorado","connecticut",
#         "delaware","florida","georgia","hawaii","idaho","illinois","indiana","iowa","kansas",
#         "kentucky","louisiana","maine","maryland","massachusetts","michigan","minnesota","mississippi",
#         "missouri","montana","nebraska","nevada","new hampshire","new jersey","new mexico","new york",
#         "north carolina","north dakota","ohio","oklahoma","oregon","pennsylvania","rhode island",
#         "south carolina","south dakota","tennessee","texas","utah","vermont","virginia","washington",
#         "west virginia","wisconsin","wyoming"
#     ]
#     abb_states = ["ak","al","ar","az","ca","co","ct","de","fl","ga","hi","ia","id","il","in","ks","ky",
#     "la","ma","md","me","mi","mn","mo","ms","mt","nc","nd","ne","nh","nj","nm","nv","ny","oh","ok","or",
#     "pa","ri","sc","sd","tn","tx","ut","va","vt","wa","wi","wv","wy"]

#     state = state.lower()
#     if len(state) == 2:
#         try:
#             index = abb_states.index(state)
#         except ValueError:
#             return None
#         return all_states[index]

#     if state in all_states:
#         return state
#     return None
