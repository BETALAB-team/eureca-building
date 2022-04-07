"""
Tests
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import pytest
import numpy as np

from eureca_building.material import Material, AirGapMaterial
from eureca_building.exceptions import (
    MaterialPropertyOutsideBoundaries,
    MaterialPropertyNotFound,
    WrongConstructionType,
)


class TestMaterials:
    """
    This is a test class for the pytest module.
    It tests Material class and its property
    """

    def test_material(self):
        # Standard material creation
        Material("Test material")

    def test_material_comp(self):
        # Standard material creation
        Material("Test material", thick=0.100, cond=1.00, spec_heat=1000.0, dens=1000.0)

    def test_material_with_prop_wrong(self):
        # Standard material creation
        with pytest.raises(MaterialPropertyOutsideBoundaries):
            Material("Test material", cond=1000.0)

    def test_material_setter(self):
        # Standard material creation
        mat = Material(
            "Test material", thick=0.100, cond=1.00, spec_heat=1000.0, dens=1000.0
        )

        with pytest.raises(MaterialPropertyOutsideBoundaries):
            mat.thick = 100.0

    def test_material_setter_good(self):
        # Standard material creation
        mat = Material(
            "Test material", thick=0.100, cond=1.00, spec_heat=1000.0, dens=1000.0
        )

        mat.dens = 800.0

    def test_material_setter_list(self):
        # Standard material creation
        mat = Material(
            "Test material", thick=0.100, cond=1.00, spec_heat=1000.0, dens=1000.0
        )

        with pytest.raises(TypeError):
            mat.thick = "fd"

    def test_air_material(self):
        AirGapMaterial("Test material")

    def test_air_material_2(self):
        AirGapMaterial("Test material", thick=0.100, resistance=1)

    def test_airgapmaterial_with_prop_wrong(self):
        with pytest.raises(MaterialPropertyOutsideBoundaries):
            AirGapMaterial("Test material", resistance=100)

    def test_airgapmaterial_setter(self):
        mat = AirGapMaterial("Test material", thick=0.100, resistance=1)

        with pytest.raises(MaterialPropertyOutsideBoundaries):
            mat.thick = 100.0

    def test_airgapmaterial_setter_good(self):
        mat = AirGapMaterial("Test material", thick=0.100, resistance=1)

        mat.resistance = 800.0

    def test_airgapmaterial_setter_list(self):
        mat = AirGapMaterial("Test material", thick=0.100, resistance=1)

        with pytest.raises(TypeError):
            mat.thick = "fd"
