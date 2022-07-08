"""
This module includes functions to model the thermal zone
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import interpolate

from eureca_building.config import CONFIG
from eureca_building.surface import Surface, SurfaceInternalMass
from eureca_building.fluids_properties import air_properties
from eureca_building._VDI6007_auxiliary_functions import impedence_parallel, tri2star, long_wave_radiation, loadHK
from eureca_building.internal_load import Lights, ElectricLoad, People, InternalLoad
from eureca_building.natural_ventilation import NaturalVentilation
from eureca_building.weather import WeatherFile
from eureca_building.setpoints import Setpoint
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
                self._net_floor_area = 0.
            else:
                self._net_floor_area = np.array(floors_area).sum()
        else:
            self._net_floor_area = net_floor_area

        self.internal_loads_list = []
        self.natural_ventilation_list = []

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
            logging.error(
                f"Thermal zone {self.name}, negative footprint area: {value}. Simulation will continue with absolute value"
            )
        if float(abs(value)) < 1e-5:
            self.__net_floor_area = 1e-5
        else:
            self.__net_floor_area = abs(value)

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
            logging.error(
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
            logging.error(
                f"Thermal zone {self.name}, negative air thermal capacity: {value}. Simulation will continue with the absolute value"
            )
        if float(abs(value)) < 1e-5:
            self.__air_thermal_capacity = 1e-5
        else:
            self.__air_thermal_capacity = abs(value)

    def add_temperature_setpoint(self, setpoint, mode='air'):
        """
        Function to associate a setpoint to the thermal zone

        Args:
            setpoint: Setpoint
                object of the class Setpoint
            mode: str
                setpoint mode: ['air', 'operative', 'radiant']

        Returns:
            None
        """
        self.temperature_setpoint = setpoint
        self.temperature_setpoint_mode = mode

    @property
    def temperature_setpoint(self, value) -> Setpoint:
        self._temperature_setpoint = value

    @temperature_setpoint.setter
    def temperature_setpoint(self, value: Setpoint):
        if not isinstance(value, Setpoint):
            raise TypeError(
                f"Thermal zone {self.name}, setpoint must be a Setpoint object"
            )
        self._temperature_setpoint = value

    @property
    def temperature_setpoint_mode(self, value) -> str:
        self._temperature_setpoint_mode = value

    @temperature_setpoint_mode.setter
    def temperature_setpoint_mode(self, value: str):
        if not isinstance(value, str):
            raise TypeError(
                f"Thermal zone {self.name}, setpoint mode must be a str"
            )
        if value not in ['air', 'operative', 'radiant']:
            raise ValueError(
                f"Thermal zone {self.name}, setpoint mode must be chosen from 'air', 'operative', 'radiant'"
            )
        self._temperature_setpoint_mode = value

    def add_humidity_setpoint(self, setpoint):
        """
        Function to associate a humidity setpoint to the thermal zone

        Args:
            setpoint: Setpoint
                object of the class Setpoint
            mode: str
                setpoint mode: ['relative_humidity']

        Returns:
            None
        """
        self.humidity_setpoint = setpoint
        # the mode is in the SP object
        self.humidity_setpoint_mode = setpoint.setpoint_type

    @property
    def humidity_setpoint(self, value) -> Setpoint:
        self._humidity_setpoint = value

    @humidity_setpoint.setter
    def humidity_setpoint(self, value: Setpoint):
        if not isinstance(value, Setpoint):
            raise TypeError(
                f"Thermal zone {self.name}, setpoint must be a Setpoint object"
            )
        self._humidity_setpoint = value

    @property
    def humidity_setpoint_mode(self, value) -> str:
        self._humidity_setpoint_mode = value

    @humidity_setpoint_mode.setter
    def humidity_setpoint_mode(self, value: str):
        if not isinstance(value, str):
            raise TypeError(
                f"Thermal zone {self.name}, setpoint mode must be a str"
            )
        if value not in ['relative_humidity']:
            raise ValueError(
                f"Thermal zone {self.name}, setpoint mode must be chosen from 'relative_humidity'"
            )
        self._humidity_setpoint_mode = value

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
        self.Araum = 0
        self.Aaw = 0

        # Cycling surface to calculates the Resistance and capacitance of the vdi 6007

        for surface in self._surface_list:
            self.Araum += surface._area
            if surface.surface_type in ["ExtWall", "GroundFloor", "Roof"]:
                self.Aaw += surface._area
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
                raise TypeError(f'Surface {surface.name}: surface type not found: {surface.surface_type}.')

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

    def add_internal_load(self, *internal_load):
        """
        Function to associate a load to the thermal zone

        Args:
            internal_load: InternalLoad

        Returns:
            None
        """
        for int_load in internal_load:
            if not isinstance(int_load, InternalLoad):
                raise TypeError(
                    f"ThermalZone {self.name}, add_internal_load() method: internal_load not of InternalLoad type: {type(int_load)}"
                )
            self.internal_loads_list.append(int_load)

    def extract_convective_radiative_latent_load(self):
        """
        From the internal loads calculates 3 arrays (len equal to 8769 * number of time steps per hour):
        {
        convective [W] : np.array
        radiative [W] : np.array
        latent [kg_vap/s] : np.array
        }

        Returns:
            dict
        """
        convective = np.zeros(CONFIG.number_of_time_steps_year)
        radiant = np.zeros(CONFIG.number_of_time_steps_year)
        latent = np.zeros(CONFIG.number_of_time_steps_year)
        for load in self.internal_loads_list:
            load_conv, load_rad, load_lat = load.get_loads(area=self._net_floor_area)
            convective += load_conv
            radiant += load_rad
            latent += load_lat
        self.convective_load = convective
        self.radiative_load = radiant
        self.latent_load = latent
        return {'convective [W]': convective,
                'radiative [W]': radiant,
                'latent [kg_vap/s]': latent}

    def calculate_zone_loads_ISO13790(self, weather):
        '''
        Calculates the heat gains on the three nodes of the ISO 13790 network
        Vectorial calculation

        Parameters
            ----------
            weather : eureca_building.weather.WeatherFile
                WeatherFile object

        Returns
        -------
        None.
        '''

        # Check input data type

        if not isinstance(weather, WeatherFile):
            raise TypeError(f'ThermalZone {self.name}, weather type is not a WeatherFile: weather type {type(weather)}')
        # Check input data quality
        # First calculation of internal heat gains

        phi_int = self.extract_convective_radiative_latent_load()
        phi_sol_gl_tot = 0
        phi_sol_op_tot = 0

        # Solar radiation
        irradiances = weather.hourly_data_irradiances

        for surface in self._surface_list:

            phi_sol_op = 0
            phi_sol_gl = 0

            if surface.surface_type in ['ExtWall', 'Roof']:
                if hasattr(surface, 'window'):
                    h_r = surface.get_surface_external_radiative_coefficient()

                    irradiance = irradiances[float(surface._azimuth_round)][float(surface._height_round)]
                    BRV = irradiance['direct']
                    TRV = irradiance['global']
                    DRV = TRV - BRV
                    A_ww = surface._glazed_area
                    A_op = surface._opaque_area

                    # Glazed surfaces
                    F_sh_w = surface.window._shading_coef_ext
                    F_w = surface.window._shading_coef_int
                    F_f = surface.window._frame_factor
                    AOI = irradiance['AOI']
                    shgc = interpolate.splev(AOI, surface.window.solar_heat_gain_coef_profile, der=0)
                    shgc_diffuse = interpolate.splev(70, surface.window.solar_heat_gain_coef_profile, der=0)
                    # TODO: For urban shading
                    # if i.OnOff_shading == 'On':
                    #     phi_sol_gl = F_so * (BRV * F_sh * F_w * (
                    #             1 - F_f) * shgc * A_ww * i.shading_effect) + F_so * DRV * F_sh * F_w * (
                    #                          1 - F_f) * shgc_diffuse * A_ww
                    # else:
                    phi_sol_gl = BRV * F_sh_w * F_w * (1 - F_f) * shgc * A_ww \
                                 + DRV * F_sh_w * F_w * (1 - F_f) * shgc_diffuse * A_ww

                # Opaque surfaces
                # TODO:For now shading of surfaces = 1 (no urban contex)
                F_sh = 1.
                F_r = surface._sky_view_factor
                alpha = surface._construction.ext_absorptance
                sr = surface._construction._R_se
                U_net = surface._construction._u_value_net
                # if i.OnOff_shading == 'On':
                #     phi_sol_op = F_sh * (
                #             BRV * i.shading_effect + DRV) * self.alpha * self.sr_ew * self.U_ew_net * self.A_ew - self.F_r * self.sr_ew * self.U_ew_net * self.A_ew * h_r * weather.dT_er
                # else:
                phi_sol_op = F_sh * TRV * alpha * sr * U_net * A_op - \
                             F_r * sr * U_net * A_op * h_r * \
                             weather.general_data['average_dt_air_sky']

            # Total solar gain
            phi_sol_gl_tot += phi_sol_gl
            phi_sol_op_tot += phi_sol_op

        phi_sol = phi_sol_gl_tot + phi_sol_op_tot

        # Distribute heat gains to temperature nodes
        self.phi_ia = phi_int['convective [W]']
        self.phi_st = (1 - self.Am / self.Atot - self.Htr_w / (9.1 * self.Atot)) * (phi_int['radiative [W]'] + phi_sol)
        self.phi_m = self.Am / self.Atot * (phi_int['radiative [W]'] + phi_sol)

    def calculate_zone_loads_VDI6007(self, weather):
        '''
        Calculates zone loads for the vdi 6007 standard
        Also the external equivalent temperature

        Parameters
        ----------
            weather : RC_classes.WeatherData.weather
                weather obj

        Returns
        -------
        None
        '''

        # Check input data type

        if not isinstance(weather, WeatherFile):
            raise TypeError(f'ThermalZone {self.name}, weather type is not a WeatherFile: weather type {type(weather)}')

        '''
        Eerd = Solar_gain['0.0']['0.0']['Global']*rho_ground                          #
        Eatm = Solar_gain['0.0']['0.0']['Global']-Solar_gain['0.0']['0.0']['Direct']

        T_ext vettore

        '''

        Eatm, Eerd, theta_erd, theta_atm = long_wave_radiation(weather.hourly_data['out_air_db_temperature'])

        # Creates some vectors and set some parameters

        T_ext = weather.hourly_data['out_air_db_temperature']
        theta_eq = np.zeros([len(T_ext), len(self._surface_list)])
        delta_theta_eq_lw = np.zeros([len(T_ext), len(self._surface_list)])
        delta_theta_eq_kw = np.zeros([len(T_ext), len(self._surface_list)])
        theta_eq_w = np.zeros([len(T_ext), len(self._surface_list)])
        Q_il_str_A_iw = 0
        Q_il_str_A_aw = 0

        # Solar radiation
        irradiances = weather.hourly_data_irradiances

        i = -1

        # Lists all surfaces to calculate the irradiance on each one and creates the solar gains

        for surface in self._surface_list:
            i += 1
            if surface.surface_type in ['ExtWall', 'Roof']:
                # Some value loaded from surface and weather object
                h_r = surface.get_surface_external_radiative_coefficient()
                alpha_str_a = surface.construction.rad_heat_trans_coef
                alpha_a = surface.construction._conv_heat_trans_coef_ext + alpha_str_a
                phi = surface._sky_view_factor
                # TODO: External shading in urban contex
                F_sh_op = 1.
                irradiance = irradiances[float(surface._azimuth_round)][float(surface._height_round)]
                AOI = irradiance['AOI']
                BRV = irradiance['direct']
                TRV = irradiance['global']
                # Delta T long wave
                delta_theta_eq_lw[:, i] = ((theta_erd - T_ext) * (1 - phi) + \
                                           (theta_atm - T_ext) * phi) * h_r / (0.93 * alpha_a)
                delta_theta_eq_kw[:, i] = (BRV * F_sh_op + (TRV - BRV)) * surface.construction.ext_absorptance / alpha_a
                theta_eq[:, i] = (T_ext + delta_theta_eq_lw[:, i] + delta_theta_eq_kw[:, i]) * \
                                 surface.construction._u_value * surface._opaque_area / self.UA_tot
                if hasattr(surface, 'window'):
                    theta_eq_w[:, i] = (T_ext + delta_theta_eq_lw[:, i]) * \
                                       surface.window.u_value * surface._glazed_area / self.UA_tot
                    frame_factor = 1 - surface.window._frame_factor
                    F_sh = surface.window._shading_coef_ext
                    F_w = surface.window._shading_coef_int
                    F_sh_w = F_sh * F_w

                    shgc = interpolate.splev(AOI, surface.window.solar_heat_gain_coef_profile, der=0)
                    shgc_diffuse = interpolate.splev(70, surface.window.solar_heat_gain_coef_profile, der=0)
                    # Jacopo quì usa come A_v l'area finestrata, mentre la norma parla di area finestrata + opaca per la direzione
                    Q_il_str_A_iw += frame_factor * surface._glazed_area * (
                            shgc * BRV * F_sh_w + shgc_diffuse * (TRV - BRV)) * (
                                             (self.Araum - self.Aaw) / (self.Araum - surface._glazed_area))
                    Q_il_str_A_aw += frame_factor * surface._glazed_area * (
                            shgc * BRV * F_sh_w + shgc_diffuse * (TRV - BRV)) * (
                                             (self.Aaw - surface._glazed_area) / (self.Araum - surface._glazed_area))

            if surface.surface_type == 'GroundFloor':
                theta_eq[:, i] = T_ext * surface.construction._u_value * surface._opaque_area / self.UA_tot

        # self.Q_il_str_A = self.Q_il_str_A.to_numpy()
        # self.carichi_sol = (Q_il_str_A_iw+ Q_il_str_A_aw).to_numpy()

        self.theta_eq_tot = theta_eq.sum(axis=1) + theta_eq_w.sum(axis=1)

        # Calculates internal heat gains
        phi_int = self.extract_convective_radiative_latent_load()

        Q_il_str_I = phi_int['radiative [W]']
        self.Q_il_kon_I = phi_int['convective [W]']

        Q_il_str_I_iw = Q_il_str_I * (self.Araum - self.Aaw) / self.Araum
        Q_il_str_I_aw = Q_il_str_I * self.Aaw / self.Araum

        self.Q_il_str_iw = Q_il_str_A_iw + Q_il_str_I_iw
        self.Q_il_str_aw = Q_il_str_A_aw + Q_il_str_I_aw

        """
        sigma_fhk: fraction of radiant heating/cooling surfaces on total heating/cooling load
        sigma_fhk_aw: fraction of radiant heating/cooling inside external walls on the total radiant heating/cooling load
        sigma_hk_str: this is the radiant fraction the heating/cooling systems that are not embedded in the surfaces
        
        Let's say that a roof has 3 systems: 
            1) a radiant internal ceiling (20% of the total load) 
            2) a radiant floor (30% of the total load) in contact to the ground
            3) a radiator working 80% convective and 20% radiant (50% of the total load)
            
        sigma_fhk: 0.5 
            sum of 20% for the radiant ceiling and 30% for the radiant floor
        sigma_fhk_aw: 0.6
            because 0.3/(0.2+0.3) is equal to 0.6, i.e. the part of the radiant surface load 
            associated to external surfaces
        sigma_hk_str: 0.2
            because the radiator is radiative for the 20%        
        """
        # self.sigma = loadHK(sigma_fhk, sigma_fhk_aw, sigma_hk_str, self.Aaw, self.Araum)

    def _plot_ISO13790_IHG(self):
        fig, ax = plt.subplots()
        pd.DataFrame({
            'phi_ia': self.phi_ia,
            'phi_st': self.phi_st,
            'phi_m': self.phi_m
        }).plot(ax=ax)

    def _plot_VDI6007_IHG(self, weather_file):
        fig, [ax1, ax2] = plt.subplots(nrows=2)
        pd.DataFrame({
            'Q_il_kon_I': self.Q_il_kon_I,
            'Q_il_str_iw': self.Q_il_str_iw,
            'Q_il_str_aw': self.Q_il_str_aw
        }).plot(ax=ax1)
        pd.DataFrame({
            'theta_eq_tot': self.theta_eq_tot,
            'theta_ext': weather_file.hourly_data['out_air_db_temperature']
        }).plot(ax=ax2)

    def add_natural_ventilation(self, *natural_ventilation):
        """
        Function to associate a natural ventilation object to the thermal zone

        Args:
            natural_ventilation: NaturalVentilation

        Returns:
            None
        """
        for nat_vent in natural_ventilation:
            if not isinstance(nat_vent, NaturalVentilation):
                raise TypeError(
                    f"ThermalZone {self.name}, add_natural_ventilation() method: natural_ventilation not of NaturalVentilation type: {type(nat_vent)}"
                )
            self.natural_ventilation_list.append(nat_vent)

    def extract_natural_ventilation(self, weather):
        """
        From the natural_ventilation_list calculates 2 arrays (len equal to 8769 * number of time steps per hour):
        {
        air mass flow rate [kg/s] : np.array
        vapour mass flow rate [kg/s] : np.array
        }

        Args:
            weather: Weather
                weather object

        Returns:
            dict
        """
        natural_ventilation_air_flow_rate = np.zeros(CONFIG.number_of_time_steps_year)
        natural_ventilation_vapour_flow_rate = np.zeros(CONFIG.number_of_time_steps_year)
        for vent in self.natural_ventilation_list:
            air_rate, vapour_rate = vent.get_flow_rate(weather, area=self._net_floor_area, volume=self._volume)
            natural_ventilation_air_flow_rate += air_rate
            natural_ventilation_vapour_flow_rate += vapour_rate
        self.natural_ventilation_air_flow_rate = natural_ventilation_air_flow_rate
        self.natural_ventilation_vapour_flow_rate = natural_ventilation_vapour_flow_rate
        return {'natural_ventilation_air_flow_rate [kg/s]': natural_ventilation_air_flow_rate,
                'natural_ventilation_vapour_flow_rate [kg/s]': natural_ventilation_vapour_flow_rate, }

    def _plot_Zone_Natural_Ventilation(self, weather_file):
        fig, [ax1, ax2] = plt.subplots(nrows=2)
        ax1_ = ax1.twinx()
        pd.DataFrame({
            'natural_ventilation_air_flow_rate [kg/s]': self.natural_ventilation_air_flow_rate,
        }).plot(ax=ax1)
        pd.DataFrame({
            'natural_ventilation_vapour_flow_rate [kg/s]': self.natural_ventilation_vapour_flow_rate,
        }).plot(ax=ax1_, color='r')
        pd.DataFrame({
            'oa_specific_humidity': weather_file.hourly_data['out_air_specific_humidity'],
            'theta_ext': weather_file.hourly_data['out_air_db_temperature'],
            'oa_relative_humidity': weather_file.hourly_data['out_air_relative_humidity']
        }).plot(ax=ax2)
