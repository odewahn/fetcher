import glob
import os

base_path = "/Users/odewahn/Desktop/tmp/content/api8"


# concatenate a path and a filename together whether the path has a trailing slash or not
def path_concat(*args):
    components = []
    for arg in args:
        parts = arg.split("/")
        print(parts)
        # remove empty parts
        parts = [part for part in parts if part != ""]
        components.extend(parts)
    out = "/".join(components)
    return os.path.expanduser(out)


# Get all files in the directory that match the wildcard
print(path_concat(base_path, "output", "*.md"))
print(path_concat("~/Desktop/content/api8", "source/output/", "/*.md"))
print(path_concat("source/output/", "*.md"))
