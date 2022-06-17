"""
Tests
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import os

import pytest
import numpy as np

from eureca_building.material import Material, AirGapMaterial
from eureca_building.window import SimpleWindow
from eureca_building.construction import Construction
from eureca_building.construction_dataset import ConstructionDataset
from eureca_building.thermal_zone import ThermalZone
from eureca_building.surface import Surface, SurfaceInternalMass
from eureca_building.exceptions import (
    MaterialPropertyOutsideBoundaries,
    MaterialPropertyNotFound,
    WrongConstructionType,
    Non3ComponentsVertex,
    SurfaceWrongNumberOfVertices,
    WindowToWallRatioOutsideBoundaries,
    InvalidSurfaceType,
    NonPlanarSurface,
    NegativeSurfaceArea,
)


class TestThermalZone:
    """
    This is a test class for the pytest module.
    It tests ThermalZone class and its property
    """

    def test_thermal_zone(self):
        # Load the material and contructions
        path = os.path.join(
            "eureca_building",
            "example_scripts",
            "materials_and_construction_test.xlsx",
        )

        dataset = ConstructionDataset.read_excel(path)
