"""
This module includes classes and functions to manage weather file
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import json
from datetime import datetime, timedelta


# %% ---------------------------------------------------------------------------------------------------
class Config(dict):
    """
    This class is a container for config settings.

    Methods:
        to_json
        from_json
    """

    @property
    def ts_per_hour(self) -> int:
        return self._ts_per_hour

    @ts_per_hour.setter
    def ts_per_hour(self, value: int):
        try:
            value = int(value)
        except ValueError:
            raise TypeError(f"Config, time_step_per_hour is not an int: {value}")
        if 60 % value != 0:
            raise ValueError(f"Config, time_step_per_hour must be a divider of 60")
        self._ts_per_hour = value

    @classmethod
    def from_json(cls, file_path):
        try:
            with open(file_path, "r") as json_data_file:
                config_dict = cls(json.load(json_data_file))
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file {file_path} not found")
        # Generic config settings
        config_dict.ts_per_hour = int(config_dict['simulation settings']['time steps per hour'])
        config_dict.start_date = datetime.strptime(config_dict['simulation settings']['start date'], "%m-%d %H:%M")
        config_dict.final_date = datetime.strptime(config_dict['simulation settings']['final date'], "%m-%d %H:%M")
        config_dict.time_step = int(3600 / config_dict.ts_per_hour)  # s
        config_dict.number_of_time_steps = int((config_dict.final_date - config_dict.start_date) / timedelta(
            minutes=config_dict.time_step / 60)) + 1
        start_time_step = int(
            (config_dict.start_date - datetime(config_dict.start_date.year, 1, 1, 00, 00, 00)) / timedelta(
                minutes=config_dict.time_step / 60))
        config_dict.start_time_step = start_time_step
        config_dict.final_time_step = start_time_step + config_dict.number_of_time_steps

        # Radiation
        config_dict.azimuth_subdivisions = int(config_dict['solar radiation settings']["azimuth subdivisions"])
        config_dict.height_subdivisions = int(config_dict['solar radiation settings']["height subdivisions"])
        return config_dict

    def to_json(self, file_path):
        with open(file_path, "w") as outfile:
            json.dump(self, outfile, indent=4, )
