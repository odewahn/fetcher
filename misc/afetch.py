import aiohttp
import asyncio
import json
import requests
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from rich.console import Console
import logging
from slugify import slugify


console = Console()
log = logging.getLogger("rich")


ENV_FILENAME = ".fetcher"

VERSION = "0.3.0"


# Check if the .fetcher file exists in the home directory
def load_env():
    home = str(Path.home())
    if not os.path.isfile(home + "/" + ENV_FILENAME):
        return False
    load_dotenv(home + "/" + ENV_FILENAME)
    console.log(f"Loaded API key from {home}/{ENV_FILENAME}")
    return True


async def fetch_url(session, url, format="json"):
    console.log("[bold]Fetching... [/]: [italic]" + url + "[/]")
    headers = {"Authorization": f"Bearer {os.getenv('ORM_JWT')}"}
    async with session.get(url, headers=headers) as r:
        if format == "html":
            return await r.text()
        else:
            return await r.json()


async def main(id):
    async with aiohttp.ClientSession() as session:
        # Fetch book metadata
        metadata = await fetch_url(
            session, f"https://learning.oreilly.com/api/v1/book/{id}/"
        )
        # Fetch metadata asynchronously for all chapters
        chapter_metadata = await asyncio.gather(
            *[fetch_url(session, url) for url in metadata["chapters"]]
        )
        # Get a list filenames and content urls for all chapters that start with "ch"
        chapters = [
            {
                "filename": f"{id}-{slugify(c['title'][:40])}.html",
                "content": c["content"],
            }
            for c in chapter_metadata
            if c["filename"].startswith("ch")
        ]
        # Get only the content URLs so we can gather them asynchronously
        chapter_urls = [c["content"] for c in chapters]
        chapter_content = await asyncio.gather(
            *[fetch_url(session, url, "html") for url in chapter_urls]
        )
        # Write the chapter content out to the filename it's associated with
        for idx, chapter in enumerate(chapters):
            with open(f"data/{chapter['filename']}.html", "w") as f:
                f.write(chapter_content[idx])


if __name__ == "__main__":
    asyncio.run(main("9781098153427"))
