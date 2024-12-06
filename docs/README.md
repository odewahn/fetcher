# Fetcher

Fetcher is a tool to fetch content from the O'Reilly Learning platform and store it locally. For experimental use only!

![animation](fetcher.gif)

## Installation

Before you start, create an "Content" API token at https://learning.oreilly.com/account/api-tokens/

Then:

- Install the latest package on the [releases page](https://github.com/odewahn/fetcher/releases). Currently only OSX is supported.
- Run the `auth` command and enter the content auth token you created earlier.
- Open a terminal and run the `fetcher` command.
- Use the `search` command to find and download content you want to experiment with.

## Usage

### `auth`

Authenticate with the O'Reilly Learning platform using a long-lived JWT. This value will be saved in a file in your home directory, so keep it secure.

### `search`

- **Description**: Search for a work.
- **Arguments**:
  - `query`: Search terms to look for.
  - `--name`: (optional) Directory name to use. If you do not provide this argument, the direcotry will be named in the the form `<identifier>-<title slug>` (e.g. `9781492047116-oreilly-saas-architecture`).
  - `--transcript`: (optional) Use this flag to retrieve a raw transcript with timecodes rather than markdown.

### `fetch`

- **Description**: Download content based on its identifier.
- **Arguments**:
  - `identifier`: Identifier to fetch.
  - `--name`: (optional) Directory name to use. If you do not provide this argument, the direcotry will be named in the the form `<identifier>-<title slug>` (e.g. `9781492047116-oreilly-saas-architecture`).
  - `--transcript`: (optional) Use this flag to retrieve a raw transcript with timecodes rather than markdown.

### `cd`

- **Description**: Change the working directory.
- **Arguments**:
  - `dir`: Path to change to.

### `mkdir`

- **Description**: Make a directory.
- **Arguments**:
  - `dir`: Directory name.

### `ls`

- **Description**: List directories in the current directory.

### `pwd`

- **Description**: Print the working directory.

### `version`

- **Description**: Print the version of the program.

### `help`

- **Description**: Print this help message.

### `exit`

- **Description**: Exit the REPL.
