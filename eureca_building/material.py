"""
This module includes classes and fuction to implement materials properties
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

from eureca_building.exceptions import (
    MaterialPropertyOutsideBoundaries,
)
from eureca_building.units import units, material_limits
from eureca_building.logs import logs_printer

# @dataclass


class Material:
    """
    A class used to define the material

    ...

    Attributes
    ----------
    name : str
        name
    thick : float
        thickness
    cond : float
        conductivity
    spec_heat : float
        spec_heat
    dens : float
        density
    nodes_number : int
        number of nodes to dicretize the material

    Methods
    -------
    __init__(self,
        name,
        thick: float = 0.100,
        cond: float = 1.00,
        spec_heat: float = 1000.0,
        dens: float = 1000.0,
        starting_temperature : float = 20.0,
        nodes_number: int = None)

        Creates the material and checks the properties 
    """

    name: str
    thick: float = 0.100  # Thickness [m]
    cond: float = 1.00  # Conductivity [W/mK]
    spec_heat: float = 1000.0  # Specific heat [J/kgK]
    dens: float = 1000.0  # Density [kg/m3]

    # Just to use the @property decorator and the setter function
    # _name: str = field(init = False, repr = False)
    # _thick: float = field(init = False, repr = False)
    # _cond: float = field(init = False, repr = False)
    # _spec_heat: float = field(init = False, repr = False)
    # _dens: float = field(init = False, repr = False)

    def __init__(
        self,
        name,
        thick: float = 0.100,
        cond: float = 1.00,
        spec_heat: float = 1000.0,
        dens: float = 1000.0,
    ):
        """
        Define the material and check the properties

        Parameters
        ----------
        name : str
            name
        thick : float
            thickness
        cond : float
            conductivity
        spec_heat : float
            spec_heat
        dens : float
            density

        Returns
        -------
        None


        Raises
        -------
        MaterialPropertyOutsideBoundaries
            If a material parameter is not allowed.
        """
        self.name = name
        self.thick = thick
        self.dens = dens
        self.cond = cond
        self.spec_heat = spec_heat
        self.calc_paramas()

    @property
    def thick(self) -> float:
        return self._thick

    @thick.setter
    def thick(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(
                f"Material {self.name}, thickness is not a float: {value}")
        if (
            value < material_limits["thickness"][0]
            or value > material_limits["thickness"][1]
        ):
            # Value in [m]. Take a look to units
            # Check if thickenss is outside
            raise MaterialPropertyOutsideBoundaries(
                self.name,
                "thickness",
                lim=material_limits["thickness"],
                unit=units["length"],
                value=value,
            )
        self._thick = value

    @property
    def dens(self) -> float:
        return self._dens

    @dens.setter
    def dens(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(
                f"Material {self.name}, density is not a float: {value}")
        if (
            value < material_limits["density"][0]
            or value > material_limits["density"][1]
        ):
            # Value in [m]. Take a look to units
            # Check if thickenss is outside
            raise MaterialPropertyOutsideBoundaries(
                self.name,
                "density",
                lim=material_limits["density"],
                unit=units["density"],
                value=value,
            )
        self._dens = value

    @property
    def cond(self) -> float:
        return self._cond

    @cond.setter
    def cond(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(
                f"Material {self.name}, conductivity is not a float: {value}"
            )
        if (
            value < material_limits["conductivity"][0]
            or value > material_limits["conductivity"][1]
        ):
            # Value in [m]. Take a look to units
            # Check if thickenss is outside
            raise MaterialPropertyOutsideBoundaries(
                self.name,
                "conductivity",
                lim=material_limits["conductivity"],
                unit=units["conductivity"],
                value=value,
            )
        self._cond = value

    @property
    def spec_heat(self) -> float:
        return self._spec_heat

    @spec_heat.setter
    def spec_heat(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(
                f"Material {self.name}, specific heat is not a float: {value}"
            )
        if (
            value < material_limits["specific_heat"][0]
            or value > material_limits["specific_heat"][1]
        ):
            # Value in [m]. Take a look to units
            # Check if thickenss is outside
            raise MaterialPropertyOutsideBoundaries(
                self.name,
                "specific_heat",
                lim=material_limits["specific_heat"],
                unit=units["specific_heat"],
                value=value,
            )
        self._spec_heat = value

    @property
    def absorptance(self) -> float:
        return self._spec_heat

    @absorptance.setter
    def absorptance(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(
                f"Material {self.name}, absorptance is not a float: {value}"
            )
        if (
            value < material_limits["absorptance"][0]
            or value > material_limits["absorptance"][1]
        ):
            # Value in [m]. Take a look to units
            # Check if thickenss is outside
            raise MaterialPropertyOutsideBoundaries(
                self.name,
                "absorptance",
                lim=material_limits["absorptance"],
                unit=units["absorptance"],
                value=value,
            )
        self._absorptance = value

    def calc_capacity(self):
        self.capacity = (
            self.thick * self.dens * self.spec_heat
        )

    def calc_resistance(self):
        self.resistance = (
            self.thick / self.cond
        )

    def calc_paramas(self):
        self.calc_capacity()
        self.calc_resistance()


class AirGapMaterial:
    """
    A class used to define the air gap material

    ...

    Attributes
    ----------
    name : str
        name
    thick : float
        thickness
    resistance : float
        resistance

    Methods
    -------
    __init__(self,
        name,
        thick: float = 0.100,
        resistance: float = 1.00)
        Creates the material and checks the properties
    """

    name: str
    thick: float = 0.100  # Thickness [m]
    resistance: float = 1.00  # Conductivity [mK/W]

    # Just to use the @property decorator and the setter function
    # _name: str = field(init = False, repr = False)
    # _thick: float = field(init = False, repr = False)
    # _resistance: float = field(init = False, repr = False)

    def __init__(
        self,
        name,
        thick: float = 0.100,
        resistance: float = 1.00
    ):
        """
        Define the material and check the properties

        Parameters
        ----------
        name : str
            name
        thick : float
            thickness
        resistance : float
            resistance

        Returns
        -------
        None


        Raises
        -------
        MaterialPropertyOutsideBoundaries
            If a material parameter is not allowed.
        """
        self.name = name
        self.thick = thick
        self.resistance = resistance

    @property
    def thick(self) -> float:
        return self._thick

    @thick.setter
    def thick(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(
                f"Material {self.name}, thickness is not a float: {value}")
        if (
            value < material_limits["thickness"][0]
            or value > material_limits["thickness"][1]
        ):
            # Value in [m]. Take a look to units
            # Check if thickenss is outside
            raise MaterialPropertyOutsideBoundaries(
                self.name,
                "thickness",
                lim=material_limits["thickness"],
                unit=units["length"],
                value=value,
            )
        self._thick = value

    @property
    def resistance(self) -> float:
        return self._resistance

    @resistance.setter
    def resistance(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(
                f"Material {self.name}, resistance is not a float: {value}")
        if (
            value < material_limits["thermal_resistance"][0]
            or value > material_limits["thermal_resistance"][1]
        ):
            # Value in [m]. Take a look to units
            # Check if thickenss is outside
            raise MaterialPropertyOutsideBoundaries(
                self.name,
                "thermal_resistance",
                lim=material_limits["thermal_resistance"],
                unit=units["thermal_resistance"],
                value=value,
            )
        self._resistance = value
