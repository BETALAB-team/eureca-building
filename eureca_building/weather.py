"""
This module includes classes and functions to manage weather file
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import logging

import pvlib
import numpy as np
import pandas as pd


# %% ---------------------------------------------------------------------------------------------------
# Weather class
class WeatherFile():
    '''
    This class is a container for all weather data.
    It processes the epw file to extract arrays of temperature, wind, humidity etc......

    Methods:
        init
    '''

    def __init__(self,
                 epw: str,
                 year=None,
                 time_steps: int = 1,
                 irradiances_calculation: bool = True,
                 azimuth_subdivisions: int = 8,
                 height_subdivisions: int = 3,
                 urban_shading_tol=[80., 100., 80.]
                 ):
        '''
        initialize weather obj
        It processes the epw file to extract arrays of temperature, wind, humidity etc......

        Parameters
        ----------
        epw_name : str
            path of the epw file.
        year : int
            the year of simulation. it is used only to create a pd.DataFrame.
        time_steps : int
            number of time steps in a hour.
        azimuth_subdivisions: int
            number of the different direction (azimuth) solar radiation will be calculated
        height_subdivisions: int
            number of the different direction (solar height) solar radiation will be calculated
        urban_shading_tol: list of 3 floats
            list of the tolerances for urban shading calc (azimuth, distance, theta)

        Returns
        -------
        None
        '''

        # Importing and processing weather data from .epw
        try:
            epw = pvlib.iotools.read_epw(epw, coerce_year=year)  # Reading the epw via pvlib
        except FileNotFoundError:
            raise FileNotFoundError \
                (f"ERROR Weather epw file not found in the Input folder: epw name {epw_name}, input folder {input_path}")

        # Check some integer inputs
        if not isinstance(time_steps, int):
            raise TypeError(f"WeatherFile: time_steps must be a integer: time_steps = {time_steps}")
        if not isinstance(azimuth_subdivisions, int):
            raise TypeError(
                f"WeatherFile: azimuth_subdivisions must be a integer: azimuth_subdivisions = {azimuth_subdivisions}")
        if not isinstance(height_subdivisions, int):
            raise TypeError(f"WeatherFile: time_steps must be a integer: height_subdivisions = {height_subdivisions}")
        if time_steps > 6:
            logging.warning(f"WeatherFile: time_steps higher than 6")
        if azimuth_subdivisions > 10:
            logging.warning(f"WeatherFile: azimuth_subdivisions higher than 10")
        if height_subdivisions > 4:
            logging.warning(f"WeatherFile: height_subdivisions higher than 4")

        self._epw_hourly_data = epw[0]  # Hourly values
        self._epw_general_data = epw[1]  # Extracting general data
        self._site = pvlib.location.Location(self._epw_general_data['latitude'],
                                             self._epw_general_data['longitude'],
                                             tz=self._epw_general_data['TZ'])  # Creating a location variable

        if time_steps > 1:
            m = str(60 / float(time_steps)) + 'min'
            self._epw_hourly_data = epw[0].resample(m).interpolate(method='linear')

        # Weather Data and Average temperature difference between Text and Tsky
        self.hourly_data = {}
        self.general_data = {}
        self.hourly_data["time_index"] = self._epw_hourly_data.index
        self.hourly_data["wind_speed"] = self._epw_hourly_data['wind_speed'].values  # [m/s]
        self.hourly_data["out_air_db_temperature"] = self._epw_hourly_data['temp_air'].values  # [??C]
        self.hourly_data["out_air_dp_temperature"] = self._epw_hourly_data['temp_dew'].values  # [??C]
        self.hourly_data["out_air_relative_humidity"] = self._epw_hourly_data['relative_humidity'].values / 100  # [0-1]
        self.hourly_data["out_air_pressure"] = self._epw_hourly_data['atmospheric_pressure'].values  # Pa
        self.hourly_data["opaque_sky_coverage"] = self._epw_hourly_data['opaque_sky_cover'].values  # [0-10]
        # Average temperature difference between Text and Tsky
        self.general_data['average_dt_air_sky'] = _TskyCalc(self.hourly_data["out_air_db_temperature"],
                                                            self.hourly_data["out_air_dp_temperature"],
                                                            self.hourly_data["out_air_pressure"],
                                                            self.hourly_data["opaque_sky_coverage"],
                                                            time_steps)
        self.general_data['number_of_time_steps'] = len(self._epw_hourly_data.index)
        self.general_data['time_steps_per_hour'] = time_steps
        self.general_data['azimuth_subdivisions'] = azimuth_subdivisions
        self.general_data['height_subdivisions'] = height_subdivisions

        # Check some weather data values
        if not np.all(np.greater(self.hourly_data["out_air_db_temperature"], -50.)) or not np.all(
                np.less(self.hourly_data["out_air_db_temperature"], 60.)):
            logging.warning(f"WeatherFile class, input drybulb outdoor temperature is out of range [-50:60] ??C")
        if not np.all(np.greater(self.hourly_data["wind_speed"], -0.001)) or not np.all(
                np.less(self.hourly_data["wind_speed"], 25.001)):
            logging.warning(f"WeatherFile, input wind speed is out of range [-0.001, 25.] m/s")
        if not np.all(np.greater(self.hourly_data["out_air_relative_humidity"], -0.0001)) or not np.all(
                np.less(self.hourly_data["out_air_relative_humidity"], 1.)):
            logging.warning(f"WeatherFile, input relative humidity is out of range [-0.001, 1] [-]")

        if irradiances_calculation:
            self.irradiances_calculation()

        self.general_data['urban_shading_tol'] = urban_shading_tol

    def irradiances_calculation(self):
        # Get and store solar position arrays
        self._solar_position = self._site.get_solarposition(times=self._epw_hourly_data.index)
        if self.general_data['time_steps_per_hour'] > 1:
            m = str(60 / float(self.general_data['time_steps_per_hour'])) + 'min'
            self._solar_position = self._solar_position.resample(m).interpolate(
                method='ffill')  # Bfill for azimuth that is not continuous
        self.hourly_data["solar_position_apparent_zenith"] = self._solar_position['apparent_zenith'].values
        self.hourly_data["solar_position_zenith"] = self._solar_position['zenith'].values
        self.hourly_data["solar_position_apparent_elevation"] = self._solar_position['apparent_elevation'].values
        self.hourly_data["solar_position_elevation"] = self._solar_position['elevation'].values
        self.hourly_data["solar_position_azimuth"] = self._solar_position['azimuth'].values - 180.
        self.hourly_data["solar_position_equation_of_time"] = self._solar_position['equation_of_time'].values

        # Dataframe with hourly solar radiation per each direction
        azimuth_array = np.linspace(-180, 180, self.general_data['azimuth_subdivisions'] + 1)[:-1]
        height_array = np.linspace(90, 0, self.general_data['height_subdivisions'] + 1)[:-1]
        self.hourly_data_irradiances = {}
        for az in azimuth_array:
            self.hourly_data_irradiances[az] = {}
            for h in height_array:
                self.hourly_data_irradiances[az][h] = {}
                POA = _get_irradiance(self, h, az)
                self.hourly_data_irradiances[az][h]['global'] = POA['POA'].values
                self.hourly_data_irradiances[az][h]['direct'] = POA['POA_B'].values
                self.hourly_data_irradiances[az][h]['AOI'] = POA['AOI'].values


def _TskyCalc(T_ext, T_dp, P_, n_opaque, time_steps):
    '''
    Apparent sky temperature calculation procedure
    Martin Berdhal model used by TRNSYS

    Parameters
    ----------
    T_ext : np.array column
        External Temperature [??C]
    T_dp : dataframe column
        External dew point temperature [??C]
    P_ : dataframe column
        External pressure [Pa]
    n_opaque : dataframe column
        Opaque sky covering [-]

    Returns
    -------
    dTer: int, Average temperature difference between External air temperature and Apparent sky temperature [??C]

    '''

    # Check input data type
    # Calculation Martin Berdhal model used by TRNSYS

    day = np.arange(24 * time_steps)  # Inizialization day vector
    T_sky = np.zeros(24 * time_steps)
    Tsky = []
    T_sky_year = []
    for i in range(365):
        for x in day:
            t = i * 24 + x
            Tdp = T_dp[t]
            P = P_[t] / 100  # [mbar]
            nopaque = n_opaque[t] * 0.1  # [0-1]
            eps_m = 0.711 + 0.56 * Tdp / 100 + 0.73 * (Tdp / 100) ** 2
            eps_h = 0.013 * np.cos(2 * np.pi * (x + 1) / 24)
            eps_e = 0.00012 * (P - 1000)
            eps_clear = eps_m + eps_h + eps_e  # Emissivity under clear sky condition
            C = nopaque * 0.9  # Infrared cloud amount
            eps_sky = eps_clear + (1 - eps_clear) * C  # Sky emissivity
            T_sky[x] = ((T_ext[t] + 273) * (eps_sky ** 0.25)) - 273  # Apparent sky temperature [??C]
        Tsky = np.append(Tsky, T_sky)  # Annual Tsky created day by day

    # Average temperature difference between External air temperature and Apparent sky temperature
    dT_er = np.mean(T_ext - Tsky[:-time_steps + 1])

    return dT_er


def _get_irradiance(weather_obj, surf_tilt, surf_az):
    '''
    function from pvlib to calculate irradiance on a specific surface
    https://pvlib-python.readthedocs.io/en/stable/auto_examples/plot_ghi_transposition.html#sphx-glr-auto-examples-plot-ghi-transposition-py

    Parameters
    ----------
    weather_obj : weather object
    surf_tilt: float
        tilt of the surface
    surf_az: float
        azimuth of the surface

    Returns
    -------
    pandas DataFrame with the irradiances on the surface
    '''

    if surf_tilt < 0 or surf_tilt > 90 or surf_az < -180 or surf_az > 180:
        logging.warning(
            f"WARNING get_irradiance function, are you sure that the surface orientation is correct?? surf_tilt {surf_tilt}, surf_az {surf_az}")

    # Use pvlib function to calculate the irradiance on the surface

    surf_az = surf_az + 180
    POA_irradiance = pvlib.irradiance.get_total_irradiance(
        surface_tilt=surf_tilt,
        surface_azimuth=surf_az,
        dni_extra=pvlib.irradiance.get_extra_radiation(weather_obj.hourly_data["time_index"], solar_constant=1366.1,
                                                       method='spencer'),
        dni=weather_obj._epw_hourly_data['dni'],
        ghi=weather_obj._epw_hourly_data['ghi'],
        dhi=weather_obj._epw_hourly_data['dhi'],
        solar_zenith=weather_obj.hourly_data["solar_position_apparent_zenith"],
        solar_azimuth=weather_obj.hourly_data["solar_position_azimuth"],
        model='isotropic',
        model_perez='allsitescomposite1990',
        airmass=weather_obj._site.get_airmass(solar_position=weather_obj._solar_position))
    AOI = pvlib.irradiance.aoi(
        surface_tilt=surf_tilt,
        surface_azimuth=surf_az,
        solar_zenith=weather_obj.hourly_data["solar_position_apparent_zenith"],
        solar_azimuth=weather_obj.hourly_data["solar_position_azimuth"])

    # Cleaning AOI vector

    for i in range(len(AOI)):
        if AOI[i] > 90 or weather_obj.hourly_data["solar_position_apparent_zenith"][i] > 90:
            AOI[i] = 90

    return pd.DataFrame({'GHI': weather_obj._epw_hourly_data['ghi'],
                         'POA': POA_irradiance['poa_global'],
                         'POA_B': POA_irradiance['poa_direct'],
                         'POA_D': POA_irradiance['poa_global'] - POA_irradiance['poa_direct'],
                         'AOI': AOI,
                         'solar zenith': weather_obj.hourly_data["solar_position_apparent_zenith"]})
