"""
This module includes functions to model the thermal zone
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import logging

import numpy as np

from eureca_building.surface import Surface, SurfaceInternalMass
from eureca_building.exceptions import (
    Non3ComponentsVertex,
    SurfaceWrongNumberOfVertices,
    WindowToWallRatioOutsideBoundaries,
    InvalidSurfaceType,
    NonPlanarSurface,
    NegativeSurfaceArea,
)


# %% ThermalZone class


class ThermalZone(object):
    def __init__(self, name: str, surface_list: list, footprint_area=None, volume=None):
        """

        Args:
            name: str
                Name of the zone
            surface_list: list
                list of Surface/SurfaceInternalMass objects
            footprint_area: float (default None)
                footprint area of the zone in m2. If None searches for a ground floor surface
            volume: float (default None)
                volume of the zone in m3. If None sets 0 m3.

        """
        self.name = name
        self._surface_list = surface_list
        if volume == None:
            logging.warning(f"Thermal zone {self.name}, the volume is not set. Initialized with 0 m3")
            self._volume = 0.
        else:
            self._volume = volume
        if footprint_area == None:
            floors_area = [surf._area for surf in self._surface_list if
                           surf._surface_type == 'GroundFloor']
            if len(floors_area) == 0:
                logging.warning(f"Thermal zone {self.name}, the footprint area is not set. Initialized with 0 m2")
            else:
                self._footprint_area = np.array(floors_area).sum()
        else:
            self._footprint_area = footprint_area

    @property
    def _surface_list(self) -> float:
        return self.__surface_list

    @_surface_list.setter
    def _surface_list(self, value: list):
        try:
            value = list(value)
        except ValueError:
            raise TypeError(f"Thermal zone {self._idx}, the surface_list must be a list or a tuple: {type(value)}")
        for surface in value:
            if not isinstance(surface, Surface) and not isinstance(surface, SurfaceInternalMass):
                raise TypeError(f"Thermal zone {self._idx}, non SUrface object in surface_list. ")
        self.__surface_list = value

    @property
    def _footprint_area(self) -> float:
        return self.__footprint_area

    @_footprint_area.setter
    def _footprint_area(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(f"Thermal zone {self._idx}, footprint area is not an float: {value}")
        if value < 0.0:
            raise logging.error(
                f"Thermal zone {self._idx} {self.name}, negative footprint area: {value}. Simulation will continue with absolute value"
            )
        if float(abs(value)) < 1e-5:
            self.__area = 1e-5
        else:
            self.__area = abs(value)

    @property
    def _volume(self) -> float:
        return self.__volume

    @_volume.setter
    def _volume(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(f"Thermal zone {self._idx}, volume is not an float: {value}")
        if value < 0.0:
            raise logging.error(
                f"Thermal zone {self._idx} {self.name}, negative volume: {value}. Simulation will continue with absolute value"
            )
        if float(abs(value)) < 1e-5:
            self.__volume = 1e-5
        else:
            self.__volume = abs(value)
