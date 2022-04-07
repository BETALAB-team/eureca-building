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
from eureca_building.construction import Construction
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

        mat.resistance = 2.0

    def test_airgapmaterial_setter_list(self):
        mat = AirGapMaterial("Test material", thick=0.100, resistance=1)

        with pytest.raises(TypeError):
            mat.thick = "fd"


class TestConstruction:
    """
    This is a test class for the pytest module.
    It tests Construction class and its property
    """

    def test_wall(self):
        plaster = Material(
            "plaster", thick=0.01, cond=1.0, spec_heat=800.0, dens=2000.0
        )

        hollowed_bricks = Material(
            "hollowed_bricks", thick=0.150, cond=1.4, spec_heat=800.0, dens=2000.0,
        )

        air = AirGapMaterial("AirMaterial", thick=0.02, resistance=0.5)

        insulation = Material("tyles", thick=0.01, cond=1, spec_heat=840.0, dens=2300.0)

        Construction(
            "ExtWall",
            materials_list=[plaster, hollowed_bricks, air, insulation, plaster],
            construction_type="ExtWall",
        )

    def test_wall_values(self):
        plaster = Material(
            "plaster", thick=0.01, cond=1.0, spec_heat=800.0, dens=2000.0
        )

        hollowed_bricks = Material(
            "hollowed_bricks", thick=0.150, cond=1.4, spec_heat=800.0, dens=2000.0,
        )

        air = AirGapMaterial("AirMaterial", thick=0.02, resistance=0.5)

        insulation = Material(
            "tyles", thick=0.01, cond=0.03, spec_heat=1000.0, dens=30.0
        )

        ext_wall = Construction(
            "ExtWall",
            materials_list=[plaster, hollowed_bricks, air, insulation, plaster],
            construction_type="ExtWall",
        )

        # U net should be 1.041150223
        # U should be 0.884684616

        assert abs(ext_wall.U - 0.884684616) < ext_wall.U / 0.001
        assert abs(ext_wall.U_net - 1.041150223) < ext_wall.U_net / 0.001
