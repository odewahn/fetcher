# Fetcher

Fetch content from the O'Reilly Learning platform to store it locally.

# Before you start -- Get a long-lived JWT

Ask U&A to to generate a long-lived jwt for me against prod as described in devdocs:

```
../manage.py generate_jwt odewahn+admin@oreilly.com --expiration-minutes=525600
```

# Usage

## `auth`

Authenticate with the O'Reilly Learning platform. Use the long running JWT you obtained from U&A. Note that this value will be saved in a file in your home directory, so be sure to keep it secure.

### Example

```
auth
```

## `init`

Create a new project by pulling it from the O'Reilly Learning platform.

### Arguments

- `--identifier` (required): The identifier of the project you want to pull. You'll typically find this in the URL of the project on the O'Reilly Learning platform.
- `--project` (optional): If specified, the project will be created in a subdirectory of the current directory with the name of the project.
- `--dir` (optional): The directory where you want to create the project. If not specified, the project will be created in the current directory.
- `--transcript` (optional): If specified, the html for a transcript will be converted to a srt formatted transcript.

### Example

```
init --identifier=9781491973882 --directory=~/Desktop/content
```

Pull a course and save the trnscript as a srt file:

```
init --identifier=0642572031428 --transcript
```

# Development

## Install the requirements

```
pip install -r requirements.txt
```

I've noticed that sometimes `pyinstaller` doesn't pick up these packages unless you also run them in the global environment where Python is installed, rather than in the virtual environment. I'm not sure why this is, but it's something to keep in mind.

## Building standalone executable

First, be sure you're set up to run pyinstaller by reading [Build an executable with pyinstaller](http://www.gregreda.com/2023/05/18/notes-on-using-pyinstaller-poetry-and-pyenv/). This is another good [tutorial on pyinstaller](https://www.devdungeon.com/content/pyinstaller-tutorial). It took a bit of finagling to make this work, so YMMV.

From the root directory, run the following command:

```

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

# This line is necessary because cookiecutter wants to read this file

mkdir -p dist/fetcher/_internal/cookiecutter
echo "2.6.0" > dist/fetcher/_internal/cookiecutter/VERSION.txt
```

To view the sizes of the included files, cd into the `dist/_internal` directory and run:

```
du -hs *
```

Originally, I compiled this using `--onefile` but found that it became incredibly slow to start up. Ths seems to be a common complaint about pyinstaller. I think it also has to do with a virus scanner, which has to scan each file in the package as it's unzipped every time. So, I started just directibuting the dist folder. It's less convenient and clear, but gives an acceptable startup time.

# Build executable part II with codesigning

## Before you start

Set up all the stuff apple requires, as described in the "Setup" section of https://github.com/txoof/codesign/blob/main/Signing_and_Notarizing_HOWTO.md:

- Developer ID Application certificate
- Developer ID Installer certificate

## Building the binary

Go through all the rigamarole to build the binary.

First, set up the keychain stuff:

xcrun notarytool store-credentials ODEWAHN \
 --apple-id andrew@odewahn.com \
 --team-id 8R36RY2J2J

## To build:

```
pyinstaller --noconfirm --clean fetcher.spec
```

## To package, sign, and notarize

This tool does all the steps in a nice package:

https://github.com/txoof/codesign

Note that I renamed it `pycodesign` when I downloaded it, even though it's called `pycodesign.py` when you download it from the repo.

```
cd dist
pycodesign ../pycodesign.ini
```

# Notes

https://cookiecutter.readthedocs.io/en/1.7.0/advanced/calling_from_python.html

When testing cookiecutter:

```
init --identifier=9781491973882 --dir=~/Desktop/content
```
