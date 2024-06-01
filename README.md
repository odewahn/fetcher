# Usage

## Get a long-lived JWT

Ask U&A to to generate a long-lived jwt for me against prod as described in devdocs:

```
../manage.py generate_jwt odewahn+admin@oreilly.com --expiration-minutes=525600
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
 --name=grabbah \
 --hidden-import=prompt_toolkit \
 --hidden-import=slugify \
 --noconfirm \
 main.py

```

To view the sizes of the included files, cd into the `dist/_internal` directory and run:

```
du -hs *
```

Originally, I compiled this using `--onefile` but found that it became incredibly slow to start up. Ths seems to be a common complaint about pyinstaller. I think it also has to do with a virus scanner, which has to scan each file in the package as it's unzipped every time. So, I started just directibuting the dist folder. It's less convenient and clear, but gives an acceptable startup time.
