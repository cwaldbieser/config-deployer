
import os
from fabric import utils as fabutils
from fabric.api import (lcd, local)
import deployer.config as config
from deployer.shellfuncs import shellquote

def filter_files_for_archival(extension):
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
                with lcd(dirpath):
                    if os.path.exists(os.path.join(dirpath, transformed)):
                        local("git add -f {0}".format(shellquote(transformed))) 
                    else:
                        fabutils.warn("Could not find file '{0}' for archival.".format(transformed))
                    local("git rm -f {0}".format(shellquote(fname)))
        
