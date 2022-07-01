"""
This module includes functions to model any schedule
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import logging

import numpy as np
import matplotlib.pyplot as plt

from eureca_building.schedule_properties import schedule_types
from eureca_building.config import CONFIG
from eureca_building.exceptions import (
    InvalidScheduleType,
    ScheduleOutsideBoundaryCondition,
    InvalidScheduleDimension,
    ScheduleLengthNotConsistent,
)


class Schedule:
    """
    Class schedule with some generic methods for all schedule
    (in particular how they are created)
    """

    def __init__(
            self,
            name: str,
            schedule_type: str,
            schedule: np.array,
            lower_limit=None,
            upper_limit=None,
    ):
        f"""
        Schedule Constructor
        
        Args:
            name: str
                name
            schedule_type: str
                type of the {schedule_types["unit_type"]}
            schedule: np.array
                the schedule array, length equal to 8760 time the number of time steps per hour
            upper_limit: float/int (default None)
                upper limit to check schedule validity
            lower_limit: float/int (default None)
                upper limit to check schedule validity
        """
        self.name = str(name)
        self.schedule_type = schedule_type
        self._lower_limit = lower_limit
        self._upper_limit = upper_limit
        self.schedule = schedule

    @property
    def schedule_type(self):
        return self._schedule_type

    @schedule_type.setter
    def schedule_type(self, value):
        if not isinstance(value, str):
            raise TypeError(f"Schedule {self.name}, type is not a str: {value}")
        if value not in schedule_types["unit_type"]:
            raise InvalidScheduleType(
                f"Schedule {self.name}, type not in: {schedule_types['unit_type']}\n{value}"
            )
        self._schedule_type = value

    @property
    def _lower_limit(self):
        return self.__lower_limit

    @_lower_limit.setter
    def _lower_limit(self, value):
        if value is not None:
            if not isinstance(value, float) and not isinstance(value, int):
                raise TypeError(f"Schedule {self.name}, lower limit is not a number: {value}")
            self.__lower_limit = value
        else:
            self.__lower_limit = -1e20
        if self.schedule_type == "Percent":
            if value is not None:
                logging.warning(
                    f"""
Schedule {self.name}, the schedule is a percentage schedule but a lower limit was set.
Lower limit set to 0."""
                )
            self.__lower_limit = 0.

    @property
    def _upper_limit(self):
        return self.__upper_limit

    @_upper_limit.setter
    def _upper_limit(self, value):
        if value is not None:
            if not isinstance(value, float) and not isinstance(value, int):
                raise TypeError(f"Schedule {self.name}, upper limit is not a number: {value}")
            self.__upper_limit = value
        else:
            self.__upper_limit = 1e20
        if self.schedule_type == "Percent":
            if value is not None:
                logging.warning(
                    f"""
Schedule {self.name}, the schedule is a percentage schedule but a upper limit was set.
Lower limit set to 1."""
                )
            self.__upper_limit = 1.

    @property
    def schedule(self):
        return self._schedule

    @schedule.setter
    def schedule(self, _value):
        try:
            value = np.array(_value, dtype=float)
        except ValueError:
            raise ValueError(f"Schedule {self.name}, non-numeric values in the schedule")
        if value.ndim > 1:
            raise InvalidScheduleDimension(f"Schedule {self.name}, schedule dimension higher than 1: {value.ndim}")
        if np.any(np.greater(value, self._upper_limit)):
            raise ScheduleOutsideBoundaryCondition(
                f"Schedule {self.name}, there is a value above the upper limit: upper limit {self._upper_limit}"
            )
        if np.any(np.less(value, self._lower_limit)):
            raise ScheduleOutsideBoundaryCondition(
                f"Schedule {self.name}, there is a value below the lower limit: lower limit {self._lower_limit}"
            )
        if len(value) != CONFIG.number_of_time_steps_year:
            raise ScheduleLengthNotConsistent(
                f"""
Schedule {self.name}: the length of the schedule is not consistent 
with the number of time steps provided. 
Schedule length : {len(value)}
Number of time steps: {CONFIG.number_of_time_steps_year}
                """
            )

        self._schedule = value

    def plot(self):
        plt.plot(self.schedule)
        plt.title(f'Schedule: {self.name}')

    @classmethod
    def from_daily_schedule(
            cls,
            name: str,
            schedule_type: str,
            schedule_week_day: np.array,
            schedule_saturday: np.array,
            schedule_sunday: np.array,
            schedule_holiday: np.array,
            lower_limit=None,
            upper_limit=None,
    ):
        # TODO: create the method
        pass

    @classmethod
    def from_constant_value(
            cls,
            name: str,
            schedule_type: str,
            schedule_week_day: float,
            lower_limit=None,
            upper_limit=None,
    ):
        # TODO: create the method
        pass
