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

from eureca_building.schedule_properties import schedule_types

from eureca_building.exceptions import (
    InvalidScheduleType,
    ScheduleOutsideBoundaryCondition,
)


class Schedule:
    """
    Class schedule with some generic methods for all schedule
    (in particular how they are created)
    """

    def __init__(
            self,
            name: str,
            type: str,
            schedule: np.array,
            lower_limit=None,
            upper_limit=None,
    ):
        f"""
        Schedule Constructor
        
        Args:
            name: str
                name
            type: str
                type of the {schedule_types.keys()}
            schedule: np.array
                the schedule array, length equal to 8760 time the number of time steps per hour
            upper_limit: float/int (default None)
                upper limit to check schedule validity
            lower_limit: float/int (default None)
                upper limit to check schedule validity
        """
        self.name = str(name)
        self.type = type
        self._lower_limit = lower_limit
        self._upper_limit = upper_limit
        self.schedule = schedule

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if not isinstance(value, str):
            raise TypeError(f"Schedule {self.name}, type is not a str: {value}")
        if value not in schedule_types.keys():
            raise InvalidScheduleType(
                f"Schedule {self.name}, type not in: {schedule_types.keys()}\n{value}"
            )
        self._type = value

    @property
    def _lower_limit(self):
        return self.__lower_limit

    @_lower_limit.setter
    def _lower_limit(self, value):
        if value is not None:
            if not isinstance(value, float) and not isinstance(value, int):
                raise TypeError(f"Schedule {self.name}, lower limit is not a number: {value}")
        self.__lower_limit = value

    @property
    def _upper_limit(self):
        return self.__upper_limit

    @_upper_limit.setter
    def _upper_limit(self, value):
        if value is not None:
            if not isinstance(value, float) and not isinstance(value, int):
                raise TypeError(f"Schedule {self.name}, upper limit is not a number: {value}")
        self.__upper_limit = value

    @property
    def schedule(self):
        return self._schedule

    @schedule.setter
    def schedule(self, _value):
        try:
            value = np.array(_value, dtype=float)
        except ValueError:
            raise ValueError(f"Schedule {self.name}, non-numeric values in the schedule")
        if np.any(np.greater(value, self._upper_limit)):
            raise ScheduleOutsideBoundaryCondition(
                f"Schedule {self.name}, there is a value above the upper limit: upper limit {self._upper_limit}"
            )
        if np.any(np.less(value, self._lower_limit)):
            raise ScheduleOutsideBoundaryCondition(
                f"Schedule {self.name}, there is a value below the lower limit: lower limit {self._lower_limit}"
            )

        self._schedule = value


class InternalLoad(Schedule):
    """
    Class schedule with some generic methods for all schedule
    (in particular how they are created)
    """

    def __init__(
            self,
            name: str,
            type: str,
            schedule: np.array,
            lower_limit=None,
            upper_limit=None,
    ):
