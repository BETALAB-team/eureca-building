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
    Internal Gain Class
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
            # TODO
            pass

    def get_air_flow_rate(self, *args, **kwarg) -> np.array:
        raise NotImplementedError(
            f"""
You must override the get_convective_load method for each class inherited from InternalLoad
Return value must be a np.array
"""
        )

    def get_vapour_flow_rate(self, *args, **kwarg) -> np.array:
        raise NotImplementedError(
            f"""
You must override the get_radiant_load method for each class inherited from InternalLoad
Return value must be a np.array
"""
        )

    def get_flow_rate(self, *args, **kwargs) -> list:
        """
        Return the convective, radiant, latent load np.array
        If the calculation method is specific (W/m2 or px/m2) the area must be passed
        Args:
            area: None

        Returns:
            [np.array, np.array, np.array]:
                the schedules: convective [W], radiant [W], vapour [kg_vap/s]

        """
        if "area" not in kwargs.keys():
            area = None
        else:
            area = kwargs['area']
        if "volume" not in kwargs.keys():
            area = None
        else:
            area = kwargs['volume']
        vapuor = self.get_vapour_flow_rate(area=area, volume=volume)
        air = self.get_air_flow_rate(area=area, volume=volume)
        return vapuor, air
