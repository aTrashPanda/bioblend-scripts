from pprint import pprint
from .common import connect

def list(args: list):
    if len(args) == 0:
        print("ERROR: no library ID was provided")
        return
    gi = connect()
    folders = gi.libraries.get_folders(args[0])
    pprint(folders)


def create(args: list):
    if len(args) < 2:
        print("ERROR: Invalid parameters.  Required the library ID, folder name and folder description (optional")
        return
    library_id = args[0]
    folder_name = args[1]
    folder_description = "No description available"
    if len(args) > 2:
        folder_description = args[2]
    gi = connect()
    result = gi.libraries.create_folder(library_id, folder_name, folder_description)
    pprint(result)


def delete(args: list):
    print("This functionality has not been implemented yet.")


