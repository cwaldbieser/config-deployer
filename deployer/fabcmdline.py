

def yesno2boolean(value):
    """
    Convert string command line flags to boolean 
    (case insensitive):
    
    y -> True
    yes -> True
    t -> True
    true -> True
    1 -> True
    Anything else -> False
    """
    value = value.lower()
    if value in ('y', 'yes', 't', 'true', '1'):
        return True
    else:
        return False

