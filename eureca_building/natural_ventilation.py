"""
This module includes functions to model natural ventilation and infiltration
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import logging

import numpy as np

from eureca_building.schedule_properties import ventilation_prop
from eureca_building.schedule import Schedule
from eureca_building.fluids_properties import air_properties

from eureca_building.exceptions import (
    InvalidScheduleType
)


class NaturalVentilation:
    """
    Ventilation
    """

    def __init__(
            self,
            name: str,
            unit: str,
            nominal_value: float,
            schedule: Schedule,
            tag: str = None,
    ):
        """
        Parent class for some inherited InternalLoads

        Args:
            name: str
                name
            unit: str
                value of the unit: ["Vol/h", "kg/s", "kg/(m2 s)", "m3/s", "m3/(m2 s)"]
            nominal_value: float
                the value to be multiplied by the schedule
            schedule: Schedule
                Schedule object
            tag: str
                a tag to define the type of internal load
        """
        self.name = name
        self.unit = unit
        self.nominal_value = nominal_value
        self.schedule = schedule
        self.tag = tag

    @property
    def nominal_value(self):
        return self._nominal_value

    @nominal_value.setter
    def nominal_value(self, value):
        try:
            value = float(value)
        except ValueError:
            raise ValueError(f"Ventilation object {self.name}, nominal value not float: {value}")
        self._nominal_value = value

    @property
    def schedule(self):
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        if not isinstance(value, Schedule):
            raise ValueError(f"Ventilation object {self.name}, schedule type not Schedule: {type(value)}")
        if value.schedule_type not in ["dimensionless", "percent", ]:
            raise InvalidScheduleType(
                f"Ventilation object  {self.name}, schedule type must be 'Dimensionless' or 'Percent': {value.schedule_type}"
            )
        self._schedule = value

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, value):
        if not isinstance(value, str):
            raise ValueError(f"Ventilation object {self.name}, unit is not a string: {type(value)}")
        if value not in ventilation_prop["natural"]["unit"]:
            raise ValueError(
                f"Ventilation object  {self.name}, unit must be chosen from: {ventilation_prop['natural']['unit']}"
            )
        self._unit = value

    def _get_absolute_value_nominal(self, area=None, volume=None):
        """
        Returns ventilation nominal value in kg/s
        Args:
            area: None
                [m2]: must be provided if the load is area specific
            volume: None
                [m3]: must be provided if the load is volume specific

        Returns:
            float
        """
        air_density = air_properties['density']
        try:
            self.nominal_value_absolute = {
                "Vol/h": self.nominal_value * volume * air_density / 3600,
                "kg/s": self.nominal_value,
                "kg/(m2 s)": self.nominal_value * area,
                "m3/s": self.nominal_value * air_density,
                "m3/(m2 s)": self.nominal_value * area * air_density,
            }[self.unit]
        except TypeError:
            raise AttributeError(
                f"Ventilation object  {self.name}, to calculate ventilation mass flow rate with specific unit you have to provide a volume or an area"
            )
        except KeyError:
            raise ValueError(
                f"Ventilation object  {self.name}, unit must be chosen from: {ventilation_prop['natural']['unit']}"
            )

    def get_air_flow_rate(self, area=None, volume=None) -> np.array:
        """
        Calc the air mass flow rate in kg/s
        Args:
            area: float
                area [m2]
            volume: float
                volume [m3]

        Returns:
            np.array

        """
        try:
            self.nominal_value_absolute
        except AttributeError:
            self._get_absolute_value_nominal(area=area, volume=volume)
        return self.nominal_value_absolute * self.schedule.schedule

    def get_vapour_flow_rate(self, weather, area=None, volume=None) -> np.array:
        """
        Calc the vapour mass flow rate in kg/s
        Args:
            weather: Weather
                Weather class object
            area: float
                area [m2]
            volume: float
                volume [m3]

        Returns:
            np.array

        """
        try:
            self.nominal_value_absolute
        except AttributeError:
            self._get_absolute_value_nominal(area=area, volume=volume)
        return self.nominal_value_absolute * self.schedule.schedule * weather.hourly_data['out_air_specific_humidity']

    def get_flow_rate(self, weather, *args, **kwargs) -> list:
        """
        Return the air and vapour flow rate from natural ventilation.
        weather object must be passed
        Args:
            weather: Weather
                weather object used for outdoor specific humidity

        Returns:
            [np.array, np.array, np.array]:
                the schedules: air flow rate [kg/s], vapour [kg/s]

        """
        if "area" not in kwargs.keys():
            area = None
        else:
            area = kwargs['area']
        if "volume" not in kwargs.keys():
            volume = None
        else:
            volume = kwargs['volume']
        vapuor = self.get_vapour_flow_rate(weather, area=area, volume=volume)
        air = self.get_air_flow_rate(area=area, volume=volume)
        return air, vapuor
