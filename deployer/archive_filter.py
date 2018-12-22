
import os
import sys
from deployer.shellfuncs import shellquote
from deployer.terminal import warn

def filter_files_for_archival(conn, config, extension):
    """
    Scan the working tree for files that end with `extension`.
    Add the file in the same folder with the same name sans
    the extension to the archival branch, and remove the file
    with the extension from the archival branch. 
    
    Excludes descending into dotfile folders.
    """
    wt = config.get_working_tree()
    for dirpath, dirnames, filenames in os.walk(wt):
        parts = os.path.split(dirpath)
        has_dotfile = False
        for part in parts:
            if part.startswith("."):
                has_dotfile = True
                break
        if has_dotfile:
            continue
        for fname in filenames:
            if fname.endswith(extension):
                transformed = os.path.splitext(fname)[0]
                if os.path.exists(os.path.join(dirpath, transformed)):
                    conn.run("cd {} && git add -f {}".format(shellquote(dirpath), shellquote(transformed))) 
                else:
                    warn("Could not find file '{}' for archival.".format(transformed))
                conn.run("cd {} && git rm -f {}".format(shellquote(dirpath), shellquote(fname)))
        
