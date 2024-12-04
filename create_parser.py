# For pyinstaller, we want to show something as quickly as possible
print("Initializing parser...")
from rich.console import Console

console = Console()

# Set up a loading message as the libraries are loaded
with console.status(f"[bold green]Loading required libraries...") as status:
    import argparse
    from shlex import split as shlex_split


class ArgumentParserError(Exception):
    pass


# This class is used to throw an exception when an error occurs
# in the argument parser. It is used to prevent the program from
# exiting when an error occurs in the argument parser.
class ThrowingArgumentParser(argparse.ArgumentParser):

    def exit(self, status=0, message=None):
        if message:
            raise ArgumentParserError(message)

    def error(self, message):
        raise ArgumentParserError(message)


def create_parser(argString=None):

    parser = ThrowingArgumentParser(exit_on_error=False)

    subparsers = parser.add_subparsers(dest="command")

    def add_subparser(name, help_text, arguments):
        subparser = subparsers.add_parser(name, help=help_text)
        for arg, kwargs in arguments:
            subparser.add_argument(arg, **kwargs)
        return subparser

    add_subparser(
        "search",
        "Search for a work",
        [
            ("query", {"nargs": "+", "help": "Search terms to look for"}),
        ],
    )

    add_subparser(
        "fetch",
        "Change the working directory",
        [
            ("identifier", {"type": str, "help": "Identifier to fetch"}),
            ("--dir", {type: str, "help": "Directory name to use"}),
            ("--transcript", {"action": "store_true", "help": "Fetch the transcript"}),
        ],
    )

    add_subparser(
        "cd",
        "Change the working directory",
        [
            ("dir", {"type": str, "help": "Path to change to"}),
        ],
    )

    add_subparser("ls", "List directories in the current directory", [])

    if argString:
        return parser.parse_args(shlex_split(argString))
    else:
        return parser.parse_args()
