"""
function for logs
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"


import os

global log_path
log_file = os.path.join(".", "logs.txt")
log_path = os.path.join(*log_file.split(os.sep)[:-1])
if not os.path.exists(log_path):
    os.mkdir(log_path)
with open(log_file, "w") as log_file_:
    # Just to clear the log file
    log_file_.write("")


def logs_printer(message):
    """
    Function to write in the log file a message

    Attributes
    -----------
    message: str
        message to write

    Return
    -----------
        None
    """
    with open(log_file, "a") as log_file_:
        print("----------------------WARNING---------------------------")
        print(message)
        print("--------------------------------------------------------")
        log_file_.write(
            f"""
***************************************************************************
{message}
***************************************************************************
    """
        )
