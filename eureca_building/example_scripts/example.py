"""
List of custom exceptions
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import os

import matplotlib.pyplot as plt
import numpy as np

#########################################################
# Config loading
# Loads a global config object
from eureca_building.config import load_config

config_path = os.path.join('.', 'config.json')
load_config(config_path)
from eureca_building.config import CONFIG

#########################################################

from eureca_building.weather import WeatherFile
from eureca_building.surface import Surface, SurfaceInternalMass
from eureca_building.thermal_zone import ThermalZone
from eureca_building.internal_load import People, Lights, ElectricLoad
from eureca_building.natural_ventilation import NaturalVentilation
from eureca_building.schedule import Schedule
from eureca_building.construction_dataset import ConstructionDataset
from eureca_building.setpoints import SetpointDualBand

#########################################################
# Epw loading
epw_path = os.path.join('..', 'example_scripts', 'ITA_Venezia-Tessera.161050_IGDG.epw')
weather_file = WeatherFile(epw_path,
                           time_steps=CONFIG.ts_per_hour,
                           azimuth_subdivisions=CONFIG.azimuth_subdivisions,
                           height_subdivisions=CONFIG.height_subdivisions, )
#########################################################
path = os.path.join(
    "..",
    "example_scripts",
    "materials_and_construction_test.xlsx",
)
# Define some constructions
dataset = ConstructionDataset.read_excel(path)
ceiling = dataset.constructions_dict[13]
floor = dataset.constructions_dict[13]
ext_wall = dataset.constructions_dict[35]
window = dataset.windows_dict[2]
#########################################################

# Definition of surfaces
wall_1 = Surface(
    "Wall 1",
    vertices=((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)),
    wwr=0.4,
    surface_type="ExtWall",
    construction=ext_wall,
    window=window,
)
wall_2 = Surface(
    "Wall 2",
    vertices=((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)),
    surface_type="ExtWall",
    construction=ext_wall,
)
floor_1 = Surface(
    "Fllor 1",
    vertices=((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)),
    wwr=0.0,
    surface_type="GroundFloor",
    construction=floor,
)
roof_1 = Surface(
    "Roof 1",
    vertices=((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)),
    wwr=0.4,
    surface_type="Roof",
    construction=ceiling,
    window=window,
)
intwall_1 = SurfaceInternalMass(
    "Roof 1",
    area=2.,
    surface_type="IntWall",
    construction=ext_wall,
)
#########################################################

# Create zone
tz1 = ThermalZone(
    name="Zone 1",
    surface_list=[wall_1, wall_2, floor_1, roof_1, intwall_1],
    net_floor_area=None,
    volume=100.)

tz1._ISO13790_params()
tz1._VDI6007_params()

#########################################################
# Loads

# A schedule
people_sched = Schedule(
    "PeopleOccupancy1",
    "percent",
    np.array(([0.1] * 7 * 2 + [0.6] * 2 * 2 + [0.4] * 5 * 2 + [0.6] * 10 * 2) * 365)[:-1],
)

# Loads
people = People(
    name='occupancy_tz',
    unit='px',
    nominal_value=1.2,
    schedule=people_sched,
    fraction_latent=0.45,
    fraction_radiant=0.3,
    fraction_convective=0.7,
    metabolic_rate=150,
)

lights = Lights(
    name='lights_tz',
    unit='W/m2',
    nominal_value=11.,
    schedule=people_sched,
    fraction_radiant=0.7,
    fraction_convective=0.3,
)

pc = ElectricLoad(
    name='pc_tz',
    unit='W',
    nominal_value=300.,
    schedule=people_sched,
    fraction_radiant=0.2,
    fraction_convective=0.8,
)

tz1.add_internal_load(people)
tz1.add_internal_load(lights, pc)

# IHG preprocessing
tz_loads = tz1.extract_convective_radiative_latent_load()
tz1.calculate_zone_loads_ISO13790(weather_file)
# tz1._plot_ISO13790_IHG()

# 2C model
tz1.calculate_zone_loads_VDI6007(weather_file)
# tz1._plot_VDI6007_IHG(weather_file)

#########################################################
# Setpoints
heat_t = Schedule(
    "t_heat",
    "temperature",
    np.array(([18] * 7 * 2 + [21] * 2 * 2 + [18] * 5 * 2 + [21] * 10 * 2) * 365)[:-1],
)

cool_t = Schedule(
    "t_heat",
    "temperature",
    np.array(([28] * 8 * 2 + [26] * 2 * 2 + [28] * 4 * 2 + [26] * 10 * 2) * 365)[:-1],
)

heat_h = Schedule(
    "h_heat",
    "dimensionless",
    np.array(([0.1] * 7 * 2 + [0.3] * 2 * 2 + [.1] * 5 * 2 + [.3] * 10 * 2) * 365)[:-1],
)

cool_h = Schedule(
    "h_heat",
    "dimensionless",
    np.array(([.9] * 8 * 2 + [.5] * 2 * 2 + [.9] * 4 * 2 + [.5] * 10 * 2) * 365)[:-1],
)

t_sp = SetpointDualBand(
    "t_sp",
    "temperature",
    schedule_lower=heat_t,
    schedule_upper=cool_t,
)
h_sp = SetpointDualBand(
    "h_sp",
    "relative_humidity",
    schedule_lower=heat_h,
    schedule_upper=cool_h,
)

tz1.add_temperature_setpoint(t_sp)
tz1.add_humidity_setpoint(h_sp)

#########################################################
# Ventilation

infiltration_sched = Schedule(
    "inf_sched",
    "dimensionless",
    np.array(([.3] * 8 * 2 + [.5] * 2 * 2 + [.3] * 4 * 2 + [.5] * 10 * 2) * 365)[:-1],
)

inf_obj = NaturalVentilation(
    name='inf_obj',
    unit='Vol/h',
    nominal_value=1.,
    schedule=infiltration_sched,
)

# Natural Ventilation preprocessing
tz1.add_natural_ventilation(inf_obj)
tz_inf = tz1.extract_natural_ventilation(weather_file)
# tz1._plot_Zone_Natural_Ventilation(weather_file)

# Simulation Still Incomplete
import time
import pandas as pd

df = pd.DataFrame(index=range(-8000, 8760 * 2 - 1),
                  columns=pd.MultiIndex.from_product([['1C', '2C'], ['Ta', 'TmAW', 'TmIW', 'Load']]))
start = time.time()
for t in range(-8000, 8760 * 2 - 1):
    ta, [tmaw, tmiw], pot = tz1.solve_timestep(t, weather_file, model='1C')
    df.loc[t]['1C'] = [ta, tmaw, tmiw, pot]
print(f"1C model: \n\t{8760 * 2 - 1} time steps\n\t{(time.time() - start):.2f} s")
start = time.time()
for t in range(-8000, 8760 * 2 - 1):
    ta, [tmaw, tmiw], pot = tz1.solve_timestep(t, weather_file, model='2C')
    df.loc[t]['2C'] = [ta, tmaw, tmiw, pot]
print(f"2C model: \n\t{8760 * 2 - 1} time steps\n\t{(time.time() - start):.2f} s")

fig, [[ax11, ax12], [ax21, ax22]] = plt.subplots(ncols=2, nrows=2)

df['1C'][['Ta', 'TmAW', 'TmIW']].plot(ax=ax11)
df['2C'][['Ta', 'TmAW', 'TmIW']].plot(ax=ax21)

df['1C']['Load'].plot(ax=ax12)
df['2C']['Load'].plot(ax=ax22)
