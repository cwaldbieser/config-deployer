

def shellquote(s):
    """
    Quote a string so it appears as a single argument
    on the shell command line.
    """
    return "'" + s.replace("'", "'\\''") + "'"

