import argparse
from rich.console import Console
from rich import print
from rich.table import Table
from dotenv import load_dotenv, find_dotenv
from ebooklib import epub
from bs4 import BeautifulSoup
import sqlite3
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

# from transformations import *
import os
from pathlib import Path
from faker import Faker
import yaml

console = Console()
log = logging.getLogger("rich")
ENV_FILENAME = ".orm-content-grabber"

VERSION = "0.1.0"


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
    return ", ".join(out)


def save_file(fn, data):
    with open(fn, "w") as f:
        f.write(data)


# *****************************************************************************************
# General functions
# *****************************************************************************************


def cleaned_metadata(data):
    # pull out fields of interest
    out = {}
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


def fetch_url(url):
    console.log("[bold]Fetching... [/]: [italic]" + url + "[/]")
    headers = {"Authorization": f"Bearer {os.getenv('ORM_JWT')}"}
    r = requests.get(url, headers=headers)
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


def action_load_transcript():

    # Get the metadata for the work
    metadata = fetch_metadata(args.work)
    metadata = cleaned_metadata(metadata)
    # Convert the metadata to yaml
    save_file("metadata.yaml", yaml.dump(metadata))
    # print(yaml.dump(metadata))

    # Fetch the work's table of contents
    toc_url = fetch_toc_url(args.work)
    toc = fetch_url(toc_url)

    flattened_toc = flatten_toc(toc)
    for idx, t in enumerate(flattened_toc):
        url = fetch_transcript_url(args.work, t["metadata"]["full_path"])
        transcript = fetch_transcript_by_url(url)

        fn = f"{idx:05d}-{slugify(t['title'])}.md"
        level = "#"
        if t["metadata"]["depth"] > 1:
            level = "##"
        md = f"{level} {t['title']}\n\n{transcript}"
        save_file(fn, md)


# *****************************************************************************************
# Code related to the command line interface
# *****************************************************************************************


def define_arguments(argString=None):

    parser = argparse.ArgumentParser(
        description="Fetch O'Reilly Content",
        exit_on_error=False,
    )

    ACTIONS = [
        "auth",
        "transcript",
    ]

    parser.add_argument(
        "action",
        choices=ACTIONS,
        help="The action to perform ",
    )

    parser.add_argument(
        "--work", help="Work to use", required=False, default="9781098115302"
    )

    if argString:
        return parser.parse_args(shlex_split(argString))
    else:
        return parser.parse_args()


def process_command():

    if args.action == "auth":
        action_set_credentials()

    if args.action == "transcript":
        if args.work is None:
            raise Exception("You must provide a --work argument for the work to load")
        action_load_transcript()


# *****************************************************************************************
# Main
# *****************************************************************************************
if __name__ == "__main__":

    if len(sys.argv) > 1:
        args = define_arguments()
        process_command()
        # try:
        #    process_command()
        # except Exception as e:
        #    console.log("[red]An error occurred on this request[/red]")
        #    console.log(" ".join(sys.argv))
        #    console.log(f"\nThe following error occurred:\n\n[red]{e}[/red]\n")
        #    sys.exit(1)
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
