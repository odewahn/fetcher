from argparse import ArgumentParser, BooleanOptionalAction
from rich.console import Console
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

console = Console()
log = logging.getLogger("rich")
ENV_FILENAME = ".orm-content-grabber"

VERSION = "0.1.1"

global args


# Check if the .promptlab file exists in the home directory
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


def coalesce_on_key(data, key):
    out = [d[key] for d in data if key in d]
    return "; ".join(out)


def save_file(fn, data):
    with open(fn, "w") as f:
        f.write(data)


def directory_name_from_metadata(metadata):
    return f"{metadata['identifier']}-{slugify(metadata['title'][:40])}"


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
    console.log("[bold]Fetching... [/]: [italic]" + url + "[/]")
    return fetch_url(url)


# *****************************************************************************************
# Functions related to fetching a transcript
# *****************************************************************************************


def fetch_url(url, format="json"):
    console.log("[bold]Fetching... [/]: [italic]" + url + "[/]")
    headers = {"Authorization": f"Bearer {os.getenv('ORM_JWT')}"}
    r = requests.get(url, headers=headers)
    if format == "html":
        return r.text
    else:
        return r.json()


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
    raw = r.text
    soup = BeautifulSoup(raw, "html.parser")
    transcript = ""
    for p in soup.select(".transcript p"):
        text = p.select_one(".text").get_text()
        transcript += text + " "
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

        fn = f"{idx:05d}-{slugify(t['title'])}.md"
        level = "#"
        if t["metadata"]["depth"] > 1:
            level = "##"
        md = f"{level} {t['title']}\n\n{transcript}"
        save_file(fn, md)


def action_fetch_book(metadata):
    for idx, url in enumerate(metadata["chapters"]):
        print(f"Fetching chapter {idx} from {url}")
        chapter_metadata = fetch_url(url)
        try:
            chapter_fn = chapter_metadata["filename"].split(".")[0]
        except:
            chapter_fn = ""
        fn = f"{idx:05d}-{chapter_fn}-{slugify(chapter_metadata['title'])}.html"
        console.log(f"Fetching content from {chapter_metadata['content']}")
        content = fetch_url(chapter_metadata["content"], format="html")
        save_file(fn, content)


def action_fetch():
    # Grab and save the metadata
    metadata = fetch_metadata(args.identifier)
    if metadata["content_format"] == "book":
        console.log(f"Fetching contents of book {metadata['title']}")
        action_fetch_book(metadata)
    # Get the content, which depends on the format
    elif metadata["content_format"] == "video":
        console.log(f"Fetching contents of video {metadata['title']}")
        action_fetch_transcript(metadata)
    # Get the content, which depends on the format
    else:
        print(f"Can't get content format {metadata['content_format']}")


def action_fetch_from_file():
    with open(args.file) as f:
        identifiers = f.readlines()
    # Remove whitespace characters like `\n` at the end of each line
    identifiers = [x.strip() for x in identifiers]
    for identifier in identifiers:
        print(f"Fetching {identifier}")
        # set the globals args identifier to the current identifier
        globals()["args"].identifier = identifier
        action_fetch()
    globals()["args"].identifier = None
    return


def init_cookiecutter(project_name, metadata):
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
    ]

    parser.add_argument(
        "action",
        choices=ACTIONS,
        help="The action to perform ",
    )

    parser.add_argument("--identifier", help="Identifier to use", required=False)

    parser.add_argument("--dir", help="Directory name", required=False)

    parser.add_argument("--file", help="File of works to fetch from", required=False)

    if argString:
        return parser.parse_args(shlex_split(argString))
    else:
        return parser.parse_args()


def process_command():

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
            action_fetch()
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
        print(directory_name_from_metadata(cleaned_metadata(metadata)))
        return

    if args.action == "init":
        if args.identifier is None:
            raise Exception("You must provide an --identifier=<identifier>")
        if args.dir is None:
            raise Exception("You must provide a --dir=<directory>")
        metadata = fetch_metadata(args.identifier)
        metadata = cleaned_metadata(metadata)
        project_name = directory_name_from_metadata(metadata)
        full_path = os.path.expanduser(args.dir) + "/" + project_name
        init_cookiecutter(project_name, metadata)
        # write metadata yml file file to the project
        save_file(f"{full_path}/metadata.yaml", yaml.dump(metadata))
        # Change to the source directory in the new project
        chdir(full_path + "/source")
        action_fetch()
        return


# *****************************************************************************************
# Main
# *****************************************************************************************
if __name__ == "__main__":

    if len(sys.argv) > 1:
        args = define_arguments()
        process_command()
        try:
            process_command()
        except Exception as e:
            console.log("[red]An error occurred on this request[/red]")
            console.log(" ".join(sys.argv))
            console.log(f"\nThe following error occurred:\n\n[red]{e}[/red]\n")
            print(traceback.format_exc())
            sys.exit(1)
    else:
        Art = text2art("Grabbah")
        print(f"[green]{Art}")
        session = PromptSession()
        while True:
            argString = session.prompt("grabbah> ")
            # If the user just hits enter, skip parsing because it will exit the program
            if len(argString) == 0:
                continue
            if argString == "exit":
                break
            try:
                args = define_arguments(argString)
                process_command()
            except Exception as e:
                console.log("[red]An error occurred on this request[/red]")
                console.log(" ".join(sys.argv))
                console.log(f"\nThe following error occurred:\n\n[red]{e}[/red]\n")
                print(traceback.format_exc())
