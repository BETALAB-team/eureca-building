"""
List of custom exceptions
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"


class PropertyOutsideBoundaries(Exception):
    """
    Class to raise the exeption property outside boundaries
    """

    def __init__(self, mat, prop, lim=None, unit=None, value=None):
        """
        Create an exception for properties problems

        Args:
            mat  ([str]): name of the property
            prop ([str]): string with the property
            unit ([str]): unit of the property
            lim  ([list]): list with boundaries
        """

        super().__init__(mat, prop, lim, unit, value)
        self.prop = prop
        self.mat = mat
        self.lim = lim
        self.unit = unit
        self.value = value


class MaterialPropertyOutsideBoundaries(PropertyOutsideBoundaries):
    """
    Class to raise the exeption material property outside boundaries
    """

    pass


class MaterialPropertyNotFound(Exception):
    """
    Class to raise the exeption material property not found
    """

    pass


class WrongConstructionType(Exception):
    """
    Class to raise the exeption wrong construction type
    """

    pass


class WrongMaterialType(Exception):
    """
    Class to raise the exeption wrong construction type
    """

    pass


#%% Surfaces exeptions
class Non3ComponentsVertex(Exception):

    pass


class SurfaceWrongNumberOfVertices(Exception):

    pass


class WindowToWallRatioOutsideBoundaries(Exception):

    pass


class InvalidSurfaceType(Exception):

    pass


class NonPlanarSurface(Exception):

    pass


class NegativeSurfaceArea(Exception):

    pass
