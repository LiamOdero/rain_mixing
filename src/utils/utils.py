import os

# Confirms that the directory <dir> exists, and if it does not, attempts the create it. Returns true if the
# directory exists at function return time, and false otherwise.
def verify_dir(dir: str):
    if not os.path.isdir(dir):
        try:
            os.makedirs(dir)
            return True
        except OSError:
            return False
    return True
