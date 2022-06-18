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
from eureca_building.fluids_properties import air_properties
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
    """
    Thermal zone class
    """

    def __init__(self, name: str, surface_list: list, net_floor_area=None, volume=None):
        """

        Args:
            name: str
                Name of the zone
            surface_list: list
                list of Surface/SurfaceInternalMass objects
            net_floor_area: float (default None)
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
        if net_floor_area == None:
            floors_area = [surf._area for surf in self._surface_list if
                           surf._surface_type == 'GroundFloor']
            if len(floors_area) == 0:
                logging.warning(f"Thermal zone {self.name}, the footprint area is not set. Initialized with 0 m2")
            else:
                self._net_floor_area = np.array(floors_area).sum()
        else:
            self._net_floor_area = net_floor_area

    @property
    def _surface_list(self) -> float:
        return self.__surface_list

    @_surface_list.setter
    def _surface_list(self, value: list):
        try:
            value = list(value)
        except ValueError:
            raise TypeError(f"Thermal zone {self.name}, the surface_list must be a list or a tuple: {type(value)}")
        for surface in value:
            if not isinstance(surface, Surface) and not isinstance(surface, SurfaceInternalMass):
                raise TypeError(f"Thermal zone {self.name}, non SUrface object in surface_list. ")
        self.__surface_list = value

    @property
    def _net_floor_area(self) -> float:
        return self.__net_floor_area

    @_net_floor_area.setter
    def _net_floor_area(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(f"Thermal zone {self.name}, footprint area is not an float: {value}")
        if value < 0.0:
            raise logging.error(
                f"Thermal zone {self.name}, negative footprint area: {value}. Simulation will continue with absolute value"
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
            raise TypeError(f"Thermal zone {self.name}, volume is not an float: {value}")
        if value < 0.0:
            raise logging.error(
                f"Thermal zone {self.name}, negative volume: {value}. Simulation will continue with the absolute value"
            )
        if float(abs(value)) < 1e-5:
            self.__volume = 1e-5
        else:
            self.__volume = abs(value)
        self._air_thermal_capacity = self.__volume * air_properties["density"] * air_properties["specific_heat"]

    @property
    def _air_thermal_capacity(self) -> float:
        return self.__air_thermal_capacity

    @_air_thermal_capacity.setter
    def _air_thermal_capacity(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(f"Thermal zone {self.name}, air thermal capacity is not an float: {value}")
        if value < 0.0:
            raise logging.error(
                f"Thermal zone {self.name}, negative air thermal capacity: {value}. Simulation will continue with the absolute value"
            )
        if float(abs(value)) < 1e-5:
            self.__air_thermal_capacity = 1e-5
        else:
            self.__air_thermal_capacity = abs(value)

    def _ISO13790_params(self):
        '''
        Calculates the thermal zone parameters of the ISO 13790
        it does not require input

        Parameters
            ----------
            None

        Returns
        -------
        None.
        '''

        self.Htr_is = 0.
        self.Htr_w = 0.
        self.Htr_ms = 0.
        self.Htr_em = 0.
        self.Cm = 0.
        self.DenAm = 0.
        self.Atot = 0.
        self.Htr_op = 0.

        # list all surface to extract the window and opeque area and other thermo physical prop

        for surface in self._surface_list:
            # try:
            if surface.surface_type == 'IntFloor':
                self.Cm += surface._opaque_area * surface.construction.k_est
                self.DenAm += surface._opaque_area * surface.construction.k_est ** 2
            else:
                self.Cm += surface._opaque_area * surface.construction.k_int
                self.DenAm += surface._opaque_area * surface.construction.k_int ** 2
            self.Atot += surface._area

            if surface.surface_type in ["ExtWall", "GroundFloor", "Roof"]:
                self.Htr_op += surface._opaque_area * surface.construction._u_value
                if surface._glazed_area > 0.:
                    self.Htr_w += surface._glazed_area * surface.window._u_value
            # except AttributeError:
            #     raise AttributeError(
            #         f"Thermal zone {self.name}, surface {surface.name} construction or window not specified"
            #     )

        # Final calculation
        self.htr_ms = 9.1  # heat tranfer coeff. ISO 13790 [W/(m2 K)]
        self.h_is = 3.45  # heat tranfer coeff. ISO 13790 [W/(m2 K)]

        self.Am = self.Cm ** 2 / self.DenAm
        self.Htr_ms = self.Am * self.htr_ms
        self.Htr_em = 1 / (1 / self.Htr_op - 1 / self.Htr_ms)
        self.Htr_is = self.h_is * self.Atot
        self.UA_tot = self.Htr_op + self.Htr_w
