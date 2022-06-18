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
from eureca_building._VDI6007_auxiliary_functions import impedence_parallel, tri2star
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
            try:
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
            except AttributeError:
                raise AttributeError(
                    f"Thermal zone {self.name}, surface {surface.name} construction or window not specified"
                )

        # Final calculation
        self.htr_ms = 9.1  # heat tranfer coeff. ISO 13790 [W/(m2 K)]
        self.h_is = 3.45  # heat tranfer coeff. ISO 13790 [W/(m2 K)]

        self.Am = self.Cm ** 2 / self.DenAm
        self.Htr_ms = self.Am * self.htr_ms
        self.Htr_em = 1 / (1 / self.Htr_op - 1 / self.Htr_ms)
        self.Htr_is = self.h_is * self.Atot
        self.UA_tot = self.Htr_op + self.Htr_w

    def _VDI6007_params(self):
        '''
        Calculates the thermal zone parameters of the VDI 6007
        it does not require input

        Parameters
            ----------
            None

        Returns
        -------
        None.
        '''

        # Creation of some arrys of variables and parameters

        alphaStr = 5  # vdi Value
        alphaKonA = 20  # vdi Value
        R1IW_m = np.array([])
        C1IW_m = np.array([])
        R_IW = np.array([])
        R1AW_v = np.array([])
        C1AW_v = np.array([])
        R_AW = np.array([])
        R1_AF_v = np.array([])
        HAW_v = np.array([])
        HAF_v = np.array([])
        alphaKonAW = np.array([])
        alphaKonIW = np.array([])
        alphaKonAF = np.array([])
        RalphaStrAW = np.array([])
        RalphaStrIW = np.array([])
        RalphaStrAF = np.array([])
        AreaAW = np.array([])
        AreaAF = np.array([])
        AreaIW = np.array([])

        # Cycling surface to calculates the Resistance and capacitance of the vdi 6007

        for surface in self._surface_list:
            if surface.surface_type in ["ExtWall", "GroundFloor", "Roof"]:
                surface_R1, surface_C1 = surface.get_VDI6007_surface_params(asim=True)
                C1AW_v = np.append(C1AW_v, [surface_C1], axis=0)
                # Opaque params
                HAW_v = np.append(HAW_v, surface.construction._u_value * surface._opaque_area)
                alphaKonAW = np.append(alphaKonAW,
                                       [surface._opaque_area * (1 / surface.construction._R_si - alphaStr)],
                                       axis=0)
                RalphaStrAW = np.append(RalphaStrAW, [1 / (surface._opaque_area * alphaStr)])
                try:
                    # Glazed params
                    R_AF_v = (surface.window.Rl_w / surface._glazed_area)  # Eq 26
                    HAF_v = np.append(HAF_v, surface.window._u_value * surface._glazed_area)
                    alphaKonAF = np.append(alphaKonAF,
                                           [surface._glazed_area * (1 / surface.window.Ri_w - alphaStr)], axis=0)
                    RalphaStrAF = np.append(RalphaStrAF, [1 / (surface._glazed_area * alphaStr)])
                except AttributeError:
                    # case of no glazed area
                    R_AF_v = 1e15
                    HAF_v = np.append(HAF_v, 0.)
                    alphaKonAF = np.append(alphaKonAF,
                                           [0.], axis=0)
                    RalphaStrAF = np.append(RalphaStrAF, [1e15])
                # this part is a little different in Jacopo model,
                # However this part calculates opaque R, glazed R and insert the parallel ass wall R
                R1AW_v = np.append(R1AW_v, [1 / (1 / surface_R1 + 1 / R_AF_v)], axis=0)
                # R1AW_v = np.append(R1AW_v,[1/(1/surface_R1+6/R_AF_v)],axis=0) ALTERNATIVA NORMA

                AreaAW = np.append(AreaAW, surface._opaque_area)
                AreaAF = np.append(AreaAF, surface._glazed_area)

            elif surface.surface_type in ["IntWall", "IntCeiling", "IntFloor"]:
                surface_R1, surface_C1 = surface.get_VDI6007_surface_params(asim=True)
                R1IW_m = np.append(R1IW_m, [surface_R1], axis=0)
                C1IW_m = np.append(C1IW_m, [surface_C1], axis=0)
                R_IW = np.append(R_IW, [sum(surface.construction.thermal_resistances)], axis=0)
                alphaKonIW = np.append(alphaKonIW,
                                       [surface._opaque_area * (1 / surface.construction._R_si - alphaStr)],
                                       axis=0)

                # if surface.opaqueArea*alphaStr == 0:
                #    print(surface.name)
                RalphaStrIW = np.append(RalphaStrIW, [1 / (surface._opaque_area * alphaStr)])

                AreaIW = np.append(AreaIW, surface._area)
            else:
                raise TypeError('Surface {surface.name}: surface type not found: {surface.surface_type}.')

        # Doing the parallel of the impedances

        self.R1AW, self.C1AW = impedence_parallel(R1AW_v, C1AW_v)  # eq 22
        self.R1IW, self.C1IW = impedence_parallel(R1IW_m, C1IW_m)

        # Final params

        self.RgesAW = 1 / (sum(HAW_v) + sum(HAF_v))  # eq 27

        RalphaKonAW = 1 / (sum(alphaKonAW) + sum(alphaKonAF))  # scalar
        RalphaKonIW = 1 / sum(alphaKonIW)  # scalar

        if sum(AreaAW) <= sum(AreaIW):
            RalphaStrAWIW = 1 / (sum(1 / RalphaStrAW) + sum(1 / RalphaStrAF))  # eq 29
        else:
            RalphaStrAWIW = 1 / sum(1 / RalphaStrIW)  # eq 31

        self.RrestAW = self.RgesAW - self.R1AW - 1 / (1 / RalphaKonAW + 1 / RalphaStrAWIW)  # eq 28

        RalphaGesAW_A = 1 / (alphaKonA * (sum(AreaAF) + sum(AreaAW)))

        if self.RgesAW < RalphaGesAW_A:  # this is different from Jacopo's model but equal to the standard
            self.RrestAW = RalphaGesAW_A  # eq 28a
            self.R1AW = self.RgesAW - self.RrestAW - 1 / (1 / RalphaKonAW + 1 / RalphaStrAWIW)  # eq 28b

            if self.R1AW < 10 ** (-10):
                self.R1AW = 10 ** (-10)  # Thresold (only numerical to avoid division by zero)  #eq 28c

        self.RalphaStarIL, self.RalphaStarAW, self.RalphaStarIW = tri2star(RalphaStrAWIW, RalphaKonIW, RalphaKonAW)
        self.UA_tot = sum(HAW_v) + sum(HAF_v)
        self.Htr_op = sum(HAW_v)
        self.Htr_w = sum(HAF_v)
