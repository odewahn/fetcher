# Fetcher Documentation

Fetcher is a tool to fetch content from the O'Reilly Learning platform and store it locally.

## Command-Line Interface

The following commands are available in the Fetcher CLI:

### `search`

- **Description**: Search for a work.
- **Arguments**:
  - `query`: Search terms to look for.
  - `--name`: Directory name to use.
  - `--transcript`: Fetch the transcript.

### `fetch`

- **Description**: Change the working directory.
- **Arguments**:
  - `identifier`: Identifier to fetch.
  - `--name`: Directory name to use.
  - `--transcript`: Fetch the transcript.

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

## Usage

### `auth`

Authenticate with the O'Reilly Learning platform using a long-lived JWT. This value will be saved in a file in your home directory, so keep it secure.

#### Example

```bash
auth
```

### `init`

Create a new project by pulling it from the O'Reilly Learning platform.

#### Arguments

- `--identifier` (required): The identifier of the project you want to pull.
- `--project` (optional): The project will be created in a subdirectory with the specified name.
- `--dir` (optional): The directory where you want to create the project.
- `--transcript` (optional): Convert the HTML transcript to an SRT formatted transcript.

#### Example

```bash
init --identifier=9781491973882 --directory=~/Desktop/content
```

Pull a course and save the transcript as an SRT file:

```bash
init --identifier=0642572031428 --transcript
```

## Development

### Install the requirements

```bash
pip install -r requirements.txt
```

### Build

```bash
pyinstaller --noconfirm --clean fetcher.spec
```

### Package, Sign, and Notarize

Use the `pycodesign` tool to package, sign, and notarize the application.

```bash
cd dist
pycodesign ../pycodesign.ini
```

### Build Standalone Executable

```bash
pyinstaller \
 --name=fetcher \
 --add-data="project_template:project_template" \
 --hidden-import=cookiecutter \
 --hidden-import=cookiecutter.main \
 --hidden-import=cookiecutter.extensions \
 --hidden-import=prompt_toolkit \
 --hidden-import=slugify \
 --noconfirm \
 --clean \
 main.py
```

## Notes

For more information on using cookiecutter, refer to the [Cookiecutter Documentation](https://cookiecutter.readthedocs.io/en/1.7.0/advanced/calling_from_python.html).

When testing cookiecutter:

```bash
init --identifier=9781491973882 --dir=~/Desktop/content
```
