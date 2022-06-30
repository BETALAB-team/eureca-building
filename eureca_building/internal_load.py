"""
This module includes functions to model internal gains
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import logging

import numpy as np

from eureca_building.schedule_properties import internal_loads_prop
from eureca_building.schedule import Schedule
from eureca_building.fluids_properties import vapour_properties

from eureca_building.exceptions import (
    ConvectiveRadiantFractionError,
    InvalidHeatGainUnit,
    InvalidHeatGainSchedule,
    AreaNotProvided,
)


# TODO: implement interface for methods to be implemented
# https://realpython.com/python-interface/

class InternalLoad:
    """
    Internal Gain Class
    """

    def __init__(
            self,
            name: str,
            nominal_value: float,
            schedule: Schedule,
    ):
        """
        Parent class for some inherited InternalLoads

        Args:
            name: str
                name
            nominal_value: float
                the value to be multiplied by the schedule
            schedule: Schedule
                Schedule object
        """
        self.name = name
        self.nominal_value = nominal_value
        self.schedule = schedule

    @property
    def nominal_value(self):
        return self._nominal_value

    @nominal_value.setter
    def nominal_value(self, value):
        try:
            value = float(value)
        except ValueError:
            raise ValueError(f"Internal Heat Gain {self.name}, nominal value not float: {value}")
        self._nominal_value = value

    @property
    def schedule(self):
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        if not isinstance(value, Schedule):
            raise ValueError(f"Internal Heat Gain {self.name}, schedule type not Schedule: {type(value)}")
        if value.schedule_type not in ["Dimensionless", "Percent", ]:
            raise InvalidHeatGainSchedule(
                f"Internal Heat Gain {self.name}, schedule type must be 'Dimensionless' or 'Percent': {value.schedule_type}"
            )
        self._schedule = value

    @property
    def fraction_latent(self):
        return self._fraction_latent

    @fraction_latent.setter
    def fraction_latent(self, value):
        if value < 0 or value > 1.:
            raise ValueError(f"Internal Heat Gain {self.name}, fraction latent outside range [0.,1.]: {value}")
        self._fraction_latent = value

    @property
    def fraction_radiant(self):
        return self._fraction_radiant

    @fraction_radiant.setter
    def fraction_radiant(self, value):
        if value < 0 or value > 1.:
            raise ValueError(f"Internal Heat Gain {self.name}, fraction radiant outside range [0.,1.]: {value}")
        try:
            if abs(value + self._fraction_convective - 1.) > 1e-5:
                raise ConvectiveRadiantFractionError(
                    f"Internal Heat Gain {self.name}, radiant/convective fraction sum not 1."
                )
        except AttributeError:
            # This is just to avoid the check if self.fraction_radiant doesn't exist
            pass

        self._fraction_radiant = value

    @property
    def fraction_convective(self):
        return self._fraction_convective

    @fraction_convective.setter
    def fraction_convective(self, value):
        if value < 0 or value > 1.:
            raise ValueError(f"Internal Heat Gain {self.name}, fraction convective outside range [0.,1.]: {value}")
        try:
            if abs(value + self.fraction_radiant - 1.) > 1e-5:
                raise ConvectiveRadiantFractionError(
                    f"Internal Heat Gain {self.name}, radiant/convective fraction sum not 1."
                )
        except AttributeError:
            # This is just to avoid the check if self.fraction_radiant doesn't exist
            pass
        self._fraction_convective = value

    def get_convective_load(self, *args, **kwarg) -> np.array:
        raise NotImplementedError(
            f"""
You must override the get_convective_load method for each class inherited from InternalLoad
Return value must be a np.array
"""
        )

    def get_radiant_load(self, *args, **kwarg) -> np.array:
        raise NotImplementedError(
            f"""
You must override the get_radiant_load method for each class inherited from InternalLoad
Return value must be a np.array
"""
        )

    def get_latent_load(self, *args, **kwarg) -> np.array:
        raise NotImplementedError(
            f"""
You must override the get_latent_load method for each class inherited from InternalLoad
Return value must be a np.array
"""
        )


class People(InternalLoad):
    def __init__(
            self,
            name: str,
            nominal_value: float,
            unit: str,
            schedule: Schedule,
            fraction_latent: float = 0.55,
            fraction_radiant: float = 0.3,
            fraction_convective: float = 0.7,
            metabolic_rate: float = 110,

    ):
        f"""
        Inherited from InternalLoad class
        The sum of radiant and convective fraction must be 1
        
        Args:
            name: str
                name
            nominal_value: float
                the value to be multiplied by the schedule
            unit: str
                define the unit from the list {internal_loads_prop["people"]["unit"]}
            schedule: Schedule
                Schedule object
            fraction_latent: float
                latent fraction (between 0 and 1)
            fraction_radiant: float
                radiant fraction of the sensible part (between 0 and 1)
            fraction_convective: float
                convective fraction of the sensible part (between 0 and 1)
            metabolic_rate: float
                Metabolic rate [W/px]
        """
        super().__init__(name, nominal_value, schedule)
        self.unit = unit
        self.fraction_latent = fraction_latent
        self.fraction_radiant = fraction_radiant
        self.fraction_convective = fraction_convective
        self.metabolic_rate = metabolic_rate

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, value):
        if not isinstance(value, str):
            raise TypeError(f"People load {self.name}, type is not a str: {value}")
        if value not in internal_loads_prop["people"]["unit"]:
            raise InvalidHeatGainUnit(
                f"People load {self.name}, unit not in: {internal_loads_prop['people']['unit']}\n{value}"
            )
        if value in ["W/m2", "px/m2", ]:
            self._calculation_method = "floor_area"
        elif value in ["W", "px", ]:
            self._calculation_method = "absolute"
        self._unit = value

    @property
    def metabolic_rate(self):
        return self._metabolic_rate

    @metabolic_rate.setter
    def metabolic_rate(self, value):
        try:
            value = float(value)
        except ValueError:
            raise ValueError(f"People load {self.name}, metabolic_rate is not a float: {value}")
        if value < 0.:
            raise ValueError(
                f"People load {self.name}, negative metabolic rate: {value}"
            )
        if value > 250.:
            logging.warning(
                f"People load {self.name}, metabolic rate over 250 W/px: {value}"
            )
        self._metabolic_rate = value

    def _get_absolute_value_nominal(self, area=None):
        """
        Returns occupancy nominal value in W
        Args:
            area: None
                [m2]: must be provide if the load is specific

        Returns:
            float
        """
        if self._calculation_method == "floor_area":
            if area == None:
                raise AreaNotProvided(
                    f"Internal Heat Gain {self.name}, specific load but area not provided."
                )
            area = float(area)
        else:
            area = 1.
        if self.unit in ["px", "px/m2", ]:
            px_w_converter = self.metabolic_rate
        else:
            px_w_converter = 1.

        # This value is in W
        self.nominal_value_absolute = area * px_w_converter * self.nominal_value

    def get_convective_load(self, area=None):
        """
        Return the convective load np.array
        If the calculation method is specific (W/m2 or px/m2) the area must be passed
        Args:
            area: None

        Returns:
            np.array:
                the schedule [W]

        """
        try:
            self.nominal_value_absolute
        except AttributeError:
            self._get_absolute_value_nominal(area=area)
        convective_fraction = (1 - self.fraction_latent) * self.fraction_convective
        return convective_fraction * self.nominal_value_absolute * self.schedule.schedule

    def get_radiant_load(self, area=None):
        """
        Return the radiant load np.array
        If the calculation method is specific (W/m2 or px/m2) the area must be passed
        Args:
            area: None

        Returns:
            np.array:
                the schedule [W]

        """
        try:
            self.nominal_value_absolute
        except AttributeError:
            self._get_absolute_value_nominal(area=area)
        radiant_fraction = (1 - self.fraction_latent) * self.fraction_radiant
        return radiant_fraction * self.nominal_value_absolute * self.schedule.schedule

    def get_latent_load(self, area=None):
        """
        Return the latent load np.array
        If the calculation method is specific (W/m2 or px/m2) the area must be passed
        Args:
            area: None

        Returns:
            np.array:
                the schedule [kg_vap/s]

        """
        try:
            self.nominal_value_absolute
        except AttributeError:
            self._get_absolute_value_nominal(area=area)
        vapour_nominal_value_kg_s = self.fraction_latent * self.nominal_value_absolute / vapour_properties[
            'latent_heat']
        return self.schedule.schedule * vapour_nominal_value_kg_s

    def get_loads(self, area=None):
        """
        Return the convective, radiant, latent load np.array
        If the calculation method is specific (W/m2 or px/m2) the area must be passed
        Args:
            area: None

        Returns:
            [np.array, np.array, np.array]:
                the schedules: convective [W], radiant [W], vapour [kg_vap/s]

        """
        conv = self.get_convective_load(area=area)
        rad = self.get_radiant_load(area=area)
        lat = self.get_latent_load(area=area)
        return conv, rad, lat
