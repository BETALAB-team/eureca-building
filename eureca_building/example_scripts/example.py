"""
List of custom exceptions
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import os
from eureca_building.surface import Surface
from eureca_building.construction_dataset import ConstructionDataset

s = Surface(name='S1', vertices=((0, 0, 0), (1., 0, 0), (0, 1., 0)))

print(s._area)

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
#########################################################

# Definition of surfaces
wall_1 = Surface(
    "Wall 1",
    vertices=((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)),
    wwr=0.4,
    surface_type="ExtWall",
    construction=ext_wall,
)
floor_1 = Surface(
    "Fllor 1",
    vertices=((0, 0, 0), (0, 1, 0), (0, 1, 0), (1, 1, 0)),
    wwr=0.0,
    surface_type="GroundFloor",
    construction=floor,
)
roof_1 = Surface(
    "Roof 1",
    vertices=((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)),
    wwr=0.4,
    surface_type="Roof",
    construction=ceiling,
)
intwall_1 = SurfaceInternalMass(
    "Roof 1",
    area=2.,
    surface_type="IntWall",
    construction=ext_wall,
)
#########################################################

# Create zone
ThermalZone(
    name="Zone 1",
    surface_list=[wall_1, floor_1, roof_1, intwall_1],
    footprint_area=None,
    volume=None)
