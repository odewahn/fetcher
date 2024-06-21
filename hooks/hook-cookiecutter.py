print("\n********************** RUNNING HOOK FOR COOKIECUTTER **********************\n")
from PyInstaller.utils.hooks import collect_data_files

# This will grab the VERSION.txt file that the cookiecutter package depends on
datas = collect_data_files("cookiecutter")
