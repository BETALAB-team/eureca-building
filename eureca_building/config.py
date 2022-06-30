"""
This module includes classes and functions to manage weather file
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import json


# %% ---------------------------------------------------------------------------------------------------
class Config(dict):
    '''
    This class is a container for config settings.

    Methods:
        to_json
        from_json
    '''

    @dataclasses
    def from_json(cls, file_path):
        try:
            with open(file_path, "r") as json_data_file:
                data = cls(json.load(json_data_file))
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file {file_path} not found")

        return data

    def to_json(self, file_path):
        with open(file_path, "w") as outfile:
            json.dump(self, outfile)
