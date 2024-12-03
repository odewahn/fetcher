# For pyinstaller, we want to show something as quickly as possible
print("Starting.  This may take a minute, so please be patient...")
from rich.console import Console


console = Console()

# Set up a loading message as the libraries are loaded
with console.status(f"[bold green]Loading required libraries...") as status:

    from argparse import ArgumentParser, BooleanOptionalAction
    from rich.console import Console
    from textual.app import App
    from textual.widgets import ListView, ListItem
    from textual.reactive import Reactive
    from textual.events import Key
    from rich import print
    from rich.table import Table
    from dotenv import load_dotenv, find_dotenv
    from ebooklib import epub
    from bs4 import BeautifulSoup
    from jinja2 import Template
    import sys
    import logging
    import requests
    import glob
    from slugify import slugify
    from shlex import split as shlex_split
    from art import text2art
    from prompt_toolkit import PromptSession
    from markdownify import markdownify as md
    import os
    from pathlib import Path
    import yaml
    from os import system, chdir
    import traceback
    from cookiecutter.main import cookiecutter
    import aiohttp
    import asyncio
    import json

log = logging.getLogger("rich")
ENV_FILENAME = ".fetcher"

VERSION = "0.3.3"

global args


# Check if the .fetcher file exists in the home directory
def load_env():
    home = str(Path.home())
    if not os.path.isfile(home + "/" + ENV_FILENAME):
        return False
    load_dotenv(home + "/" + ENV_FILENAME)
    console.log(f"Loaded API key from {home}/{ENV_FILENAME}")
    return True


# Write the API key to the .promptlab file in the home directory
def action_set_credentials():
    home = str(Path.home())
    # get user input for api key
    jwt = input("Enter your JWT> ")
    # write the key to the .promptlab file
    console.log(f"Missing credentials in file {home}/{ENV_FILENAME}.")
    with open(home + "/" + ENV_FILENAME, "w") as f:
        f.write(f"ORM_JWT={jwt}")
    console.log(f"JWT saved in {home}/{ENV_FILENAME}")


# Returns a ; delimited string based on a key extracted from an array of dictionaries
# Mostly used when processing product metadata
def coalesce_on_key(data, key):
    out = [d[key] for d in data if key in d]
    return "; ".join(out)


def save_file(fn, data):
    with open(fn, "w") as f:
        f.write(data)


def directory_name_from_metadata(idx, identifier, metadata):
    # splif filename into filename and extension, handling case where extension is missing
    filename, extension = os.path.splitext(metadata["filename"])
    # split the title by "-" and put it back together so that it is < 40 characters long
    title = ""
    for word in slugify(metadata["title"]).split("-"):
        if len(title) + len(word) < 40:
            title += word + "-"
    return f"{identifier}-{idx:03d}-{filename}-{title[:-1]}{extension}"


def project_name_from_metadata(metadata):
    title = ""
    for word in slugify(metadata["title"]).split("-"):
        if len(title) + len(word) < 40:
            title += word + "-"
    return f"{metadata['identifier']}-{title[:-1]}"


# *****************************************************************************************
# General functions
# *****************************************************************************************


def cleaned_metadata(data):
    # pull out fields of interest
    out = {}
    out["identifier"] = data["identifier"]
    out["title"] = data["title"]
    out["authors"] = data["orderable_author"]
    out["topics"] = coalesce_on_key(data["topics"], "name")
    out["publishers"] = coalesce_on_key(data["publishers"], "name")
    out["format"] = data["format"]
    out["content_format"] = data["content_format"]
    out["description"] = md(data["description"])
    out["issued"] = data["issued"]
    out["virtual_pages"] = data["virtual_pages"]
    out["duration_seconds"] = data["duration_seconds"]
    return out


def fetch_metadata(work):
    url = f"https://learning.oreilly.com/api/v1/book/{work}/"
    console.log("[bold]Fetching in fetch_metadata... [/]: [italic]" + url + "[/]")
    return fetch_url(url)


# *****************************************************************************************
# Functions related to fetching a transcript
# *****************************************************************************************


def fetch_url(url, format="json"):
    console.log("[bold]Fetching in fetch_url... [/]: [italic]" + url + "[/]")
    headers = {"Authorization": f"Bearer {os.getenv('ORM_JWT')}"}
    r = requests.get(url, headers=headers)
    if format == "html":
        return r.text
    else:
        return r.json()


async def async_fetch_url(session, url, format="json"):
    console.log("[bold]Fetching in async_fetch_url ... [/]: [italic]" + url + "[/]")
    headers = {"Authorization": f"Bearer {os.getenv('ORM_JWT')}"}
    async with session.get(url, headers=headers) as r:
        if format == "html":
            return await r.text()
        else:
            return await r.json()


# Fetch the table of contents given a work
def fetch_toc_url(work):
    url = f"https://learning.oreilly.com/api/v1/book/{work}/toc/"
    return url


# Fetch the transcript given a work and a fragment
def fetch_transcript_url(work, fragment):
    url = f"https://learning.oreilly.com/api/v1/book/{work}/chapter-content/{fragment}"
    return url


# Reads in a table of contents and flattens it into a list
def flatten_toc(toc, out=[], depth=0):
    for child in toc:
        # deep Copy the cild into a new variable
        rec = {
            "id": child["id"],
            "title": child["label"],
            "url": child["url"],
            "metadata": {
                "full_path": child["full_path"],
                "depth": child["depth"] + depth,
            },
        }
        out.append(rec)
        if "children" in child:
            flatten_toc(child["children"], out, depth + 1)
    return out


# Fetch the transcript given a URL and return just the text
def fetch_transcript_by_url(url):
    console.log("[bold]Parsing... [/]: [italic]" + url + "[/]")
    r = requests.get(url)
    return r.text


def convert_to_markdown(html):
    soup = BeautifulSoup(html, "html.parser")
    md = ""
    for p in soup.select(".transcript p"):
        text = p.select_one(".text").get_text()
        md += text + " "
    return md


def convert_to_transcript(html):
    soup = BeautifulSoup(html, "html.parser")
    transcript = ""
    idx = 1
    for p in soup.select(".transcript p"):
        begin_time = p.select_one(".begin")["title"]
        end_time = p.select_one(".end")["title"]
        text = p.select_one(".text").get_text()
        transcript += str(idx) + "\n"
        transcript += f"{begin_time} --> {end_time}\n"
        transcript += text + "\n\n"
        idx += 1
    return transcript


def action_fetch_transcript(metadata):

    # Get the metadata for the work
    metadata = cleaned_metadata(metadata)
    # Convert the metadata to yaml
    save_file("metadata.yaml", yaml.dump(metadata))
    # print(yaml.dump(metadata))

    # Fetch the work's table of contents
    toc_url = fetch_toc_url(args.identifier)
    toc = fetch_url(toc_url)
    flattened_toc = flatten_toc(toc)
    for idx, t in enumerate(flattened_toc):
        url = fetch_transcript_url(args.identifier, t["metadata"]["full_path"])
        transcript = fetch_transcript_by_url(url)

        if args.transcript:
            transcript = convert_to_transcript(transcript)
            save_file(f"{idx:05d}-{slugify(t['title'])}.txt", transcript)
        else:
            transcript = convert_to_markdown(transcript)
            fn = f"{idx:05d}-{slugify(t['title'])}.md"
            level = "#"
            if t["metadata"]["depth"] > 1:
                level = "##"
            md = f"{level} {t['title']}\n\n{transcript}"
            save_file(fn, md)


async def action_fetch_book(metadata):
    headers = {"Authorization": f"Bearer {os.getenv('ORM_JWT')}"}
    async with aiohttp.ClientSession() as session:
        # Fetch the metadata about each chapter
        chapters_metadata = await asyncio.gather(
            *[async_fetch_url(session, url) for url in metadata["chapters"]]
        )
        # Fetch content of each chapter based on the medata file.  This maps 1:1 to the metadata
        chapters_content = await asyncio.gather(
            *[
                async_fetch_url(session, chapter["content"], "html")
                for chapter in chapters_metadata
            ]
        )
        # Save the metadata to disk
        # Conver metadata array into a hash keyed on the filename from the filename field
        chapters_metadata_out = {
            chapter["filename"]: chapter for chapter in chapters_metadata
        }
        save_file("chapter-metadata.yaml", json.dumps(chapters_metadata_out, indent=4))
        # Save individual chapters to disk
        for idx, chapter in enumerate(chapters_content):
            fn = directory_name_from_metadata(
                idx, metadata["identifier"], chapters_metadata[idx]
            )
            # fn = f"{idx:05d}-{slugify(chapters_metadata[idx]['title'])}-{chapters_metadata[idx]['filename']}"
            save_file(fn, chapter)


async def action_fetch():
    # Grab and save the metadata
    metadata = fetch_metadata(args.identifier)
    if metadata["content_format"] == "book":
        console.log(f"Fetching contents of book {metadata['title']}")
        await action_fetch_book(metadata)
    # Get the content, which depends on the format
    elif metadata["content_format"] == "video":
        console.log(f"Fetching contents of video {metadata['title']}")
        action_fetch_transcript(metadata)
    # Get the content, which depends on the format
    else:
        print(f"Can't get content format {metadata['content_format']}")


async def action_fetch_from_file():
    with open(args.file) as f:
        identifiers = f.readlines()
    # Remove whitespace characters like `\n` at the end of each line
    identifiers = [x.strip() for x in identifiers]
    for identifier in identifiers:
        print(f"Fetching {identifier}")
        # set the globals args identifier to the current identifier
        globals()["args"].identifier = identifier
        if load_env() is False:
            action_set_api_key()
            load_env()
        metadata = fetch_metadata(args.identifier)
        metadata = cleaned_metadata(metadata)
        full_path = init_cookiecutter(metadata)
        # write metadata yml file file to the project
        save_file(f"{full_path}/metadata.yaml", yaml.dump(metadata))
        # Change to the source directory in the new project
        # get the current directory
        current = os.getcwd()
        chdir(full_path + "/source")
        await action_fetch()
        # Change back to the original directory
        chdir(current)

    globals()["args"].identifier = None
    return


def init_cookiecutter(metadata):
    project_name = (
        project_name_from_metadata(metadata) if args.project is None else args.project
    )
    script_path = os.path.dirname(os.path.realpath(__file__))
    # Join the filename with the script path
    fn = os.path.join(script_path, "project_template/")
    cookiecutter(
        fn,
        no_input=True,
        extra_context={"project_name": project_name, **metadata},
        output_dir=os.path.expanduser(args.dir),
        overwrite_if_exists=True,
    )
    return os.path.expanduser(args.dir) + "/" + project_name


# *****************************************************************************************
# Code related to the command line interface
# *****************************************************************************************


def define_arguments(argString=None):

    parser = ArgumentParser(description="Fetch O'Reilly Content", exit_on_error=False)

    ACTIONS = [
        "auth",
        "transcript",
        "fetch",
        "ls",
        "cd",
        "mkdir",
        "pwd",
        "version",
        "metadata",
        "init",
        "search",
    ]

    parser.add_argument(
        "action",
        choices=ACTIONS,
        help="The action to perform ",
    )

    parser.add_argument("--identifier", help="Identifier to use", required=False)

    parser.add_argument("--dir", help="Directory name", required=False, default=".")

    parser.add_argument("--project", help="Project name", required=False)

    parser.add_argument("--file", help="File of works to fetch from", required=False)

    parser.add_argument("--q", help="Search term", required=False)

    parser.add_argument(
        "--transcript",
        help="Don't do any content conversions on download (e.g., for a course just get raw transcript)",
        required=False,
        default=False,
        action=BooleanOptionalAction,
    )

    if argString:
        return parser.parse_args(shlex_split(argString))
    else:
        return parser.parse_args()


async def process_command():

    if args.action == "version":
        print(f"Version: {VERSION}")
        return

    if args.action == "auth":
        action_set_credentials()

    if args.action == "fetch":
        # If both a file and an identifier are provided, raise an error
        if args.file and args.identifier:
            raise Exception("You can't provide both a file and an identifier")
        # If neither a file nor an identifier are provided, raise an error
        if args.file is None and args.identifier is None:
            raise Exception("You must provide either a file or an identifier")
        # Check that they have a JWT
        if load_env() is False:
            action_set_api_key()
            load_env()
        # Fetch the content.  If there is an identifier, then fetch that.  If there is a file, then fetch from the file
        if args.identifier:
            await action_fetch()
        else:
            action_fetch_from_file()
        return

    if args.action == "ls":
        num_files = len(glob.glob("*"))
        if num_files > 15:
            system("ls -l | more")
        else:
            system("ls -l")
        return

    if args.action == "cd":
        if not args.dir:
            raise Exception("You must provide a --dir=<directory>")
        path = os.path.expanduser(args.dir)
        chdir(path)
        return

    if args.action == "mkdir":
        if not args.dir:
            raise Exception("You must provide a --dir=<directory>")
        os.mkdir(args.dir)
        return

    if args.action == "pwd":
        print(os.getcwd())
        return

    if args.action == "metadata":
        metadata = fetch_metadata(args.identifier)
        print(yaml.dump(cleaned_metadata(metadata)))
        print(project_name_from_metadata(cleaned_metadata(metadata)))
        return

    if args.action == "init":
        if args.identifier is None:
            raise Exception("You must provide an --identifier=<identifier>")
        if args.dir is None:
            raise Exception("You must provide a --dir=<directory>")
        if load_env() is False:
            action_set_api_key()
            load_env()
        metadata = fetch_metadata(args.identifier)
        metadata = cleaned_metadata(metadata)
        full_path = init_cookiecutter(metadata)
        # write metadata yml file file to the project
        save_file(f"{full_path}/metadata.yaml", yaml.dump(metadata))
        # Change to the source directory in the new project
        # get the current directory
        current = os.getcwd()
        chdir(full_path + "/source")
        await action_fetch()
        # Change back to the original directory
        chdir(current)
        return

    if args.action == "search":
        if args.q is None:
            raise Exception("You must provide a --q=<search term>")
        url = f"https://learning.oreilly.com/api/v2/search/?query={args.q}&sort=popularity"
        headers = {"Authorization": f"Bearer {os.getenv('ORM_JWT')}"}
        r = requests.get(url, headers=headers)
        data = r.json()
        class SearchApp(App):
            selected_id: Reactive[str] = Reactive("")

            async def on_mount(self):
                items = [
                    ListItem(f"{d['archive_id']} - {d['title']}") for d in data["results"][:10]
                ]
                self.list_view = ListView(*items)
                await self.view.dock(self.list_view)

            async def on_key(self, event: Key):
                if event.key == "enter":
                    self.selected_id = self.list_view.get_selected().text.split(" - ")[0]
                    self.exit()
                elif event.key == "escape":
                    self.exit()

        app = SearchApp()
        await app.run_async()

        if app.selected_id:
            args.identifier = app.selected_id
            await process_command()


async def main():
    global args
    if len(sys.argv) > 1:
        args = define_arguments()
        await process_command()
        try:
            await process_command()
        except Exception as e:
            console.log("[red]An error occurred on this request[/red]")
            console.log(" ".join(sys.argv))
            console.log(f"\nThe following error occurred:\n\n[red]{e}[/red]\n")
            print(traceback.format_exc())
            sys.exit(1)
    else:
        Art = text2art("fetcher")
        print(f"[green]{Art}")
        session = PromptSession()
        while True:
            argString = await session.prompt_async("fetcher> ")
            # If the user just hits enter, skip parsing because it will exit the program
            if len(argString) == 0:
                continue
            if argString == "exit":
                break
            try:
                args = define_arguments(argString)
                await process_command()
            except Exception as e:
                console.log("[red]An error occurred on this request[/red]")
                console.log(" ".join(sys.argv))
                console.log(f"\nThe following error occurred:\n\n[red]{e}[/red]\n")
                print(traceback.format_exc())


# *****************************************************************************************
# Main
# *****************************************************************************************
if __name__ == "__main__":
    os.chdir("/Users/odewahn/Desktop/tmp/content")
    # init --identifier=9781098153427 --project=test2
    asyncio.run(main())
