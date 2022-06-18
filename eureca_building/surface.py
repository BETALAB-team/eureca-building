"""
This module includes functions to model a 3D surface
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import logging

import numpy as np

from eureca_building.construction import Construction
from eureca_building.window import SimpleWindow
from eureca_building.exceptions import (
    Non3ComponentsVertex,
    SurfaceWrongNumberOfVertices,
    WindowToWallRatioOutsideBoundaries,
    InvalidSurfaceType,
    NonPlanarSurface,
    NegativeSurfaceArea,
)
from eureca_building._geometry_auxiliary_functions import (
    check_complanarity,
    polygon_area,
    normal_versor_2,
)


# %% Surface class


class Surface:
    """
    Class surface checks the complanarity and calculates the area.
    Then calculates the azimuth and tilt of the surface and set a surface
    type depending on the tilt angle
    
    complanarity:
        https://www.geeksforgeeks.org/program-to-check-whether-4-points-in-a-3-d-plane-are-coplanar/

    the area is calculated from:
        https://stackoverflow.com/questions/12642256/python-find-area-of-polygon-from-xyz-coordinates    
    """

    __warning_azimuth_subdivisions = False
    __warning_height_subdivisions = False

    def __init__(
            self,
            name: str,
            vertices: tuple = ((0, 0, 0), (0, 0, 0), (0, 0, 0)),
            wwr=None,
            subdivisions_solar_calc=None,
            surface_type=None,
            construction=None,
            window=None
    ):
        """
        Creates the surface object

        Parameters
        ----------
        name : str
            Name.
        vertices : tuple, optional
            List of vertices coordinates [m]. The default is ([0, 0, 0], [0, 0, 0], [0, 0, 0]).
        wwr : float, optional
            window to wall ratio (between  and 0 and 1). The default is 0.0.
        subdivisions_solar_calc : dict, optional
            keys:
                azimuth_subdivisions : int, optional
                    Number of azimuth discretization for radiation purposes. The default is 8.
                height_subdivisions : int, optional
                    Number of height discretization for radiation purposes. The default is 3.
        
        surface_type : str, optional
            Type of surface 'ExtWall' or 'GroundFloor' or 'Roof'.
            If not provided autocalculate.

        construction: Construction
            the construction object with the materials

        window: Window
            the Window object with the materials

        Raises
        ------
        TypeError
            DESCRIPTION.
        ValueError
            DESCRIPTION.

        Returns
        -------
        None.

        """

        self.name = name
        self._vertices = vertices

        # Area calculation

        self._area = polygon_area(self._vertices)
        """
        Considering only three points in calculating the normal vector could create
        reverse orientations if the three points are in a non-convex angle of the surface

        for this reason theres an alternative way to calculate the normal,
        implemented in function: normalAlternative

        reference: https://stackoverflow.com/questions/32274127/how-to-efficiently-determine-the-normal-to-a-polygon-in-3d-space
        """

        self._normal = normal_versor_2(self._vertices)

        self._set_azimuth_and_zenith()

        if wwr is not None:
            self._wwr = wwr
        else:
            self._wwr = 0.0
        # Param Solar Calc
        if subdivisions_solar_calc is not None:
            self.subdivisions_solar_calc = subdivisions_solar_calc
        # Surfcae type
        if surface_type is None:
            self._set_auto_surface_type()
        else:
            self.surface_type = surface_type

        if construction is not None:
            self.construction = construction
        if window is not None:
            self.window = window

    @property
    def _vertices(self) -> tuple:
        return self.__vertices

    @_vertices.setter
    def _vertices(self, value: tuple):
        try:
            value = tuple(value)
        except ValueError:
            raise TypeError(f"Vertices of surface {self.name} are not a tuple: {value}")
        if len(value) < 3:  # Not a plane - no area
            raise SurfaceWrongNumberOfVertices(
                f"Surface {self.name}. Number of vertices lower than 3: {value}"
            )
        for vtx in value:
            if not isinstance(vtx, tuple):
                raise TypeError(
                    f"Vertices of surface {self.name} are not a tuple: {value}"
                )
            if len(vtx) != 3:
                raise Non3ComponentsVertex(
                    f"Surface {self.name} has a vertex with len() != 3: {value}"
                )
            try:
                float(vtx[0])
                float(vtx[1])
                float(vtx[2])
            except ValueError:
                raise ValueError(
                    f"Surface {self.name}. One vertex contains non float values: {vtx}"
                )
            # Check coplanarity

            if not check_complanarity(value):
                raise NonPlanarSurface(f"Surface {self.name}. Non planar points")
        self.__vertices = value

    @property
    def _area(self) -> float:
        return self.__area

    @_area.setter
    def _area(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(f"Surface {self.name}, area is not an float: {value}")
        if value < 0.0:
            raise NegativeSurfaceArea(
                f"Surface {self.name}, negative surface area: {value}"
            )
        if float(value) == 0.0:
            self.__area = 1e-10
        else:
            self.__area = value

    @property
    def _wwr(self) -> float:
        return self.__wwr

    @_wwr.setter
    def _wwr(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(f"Surface {self.name}, wwr is not an float: {value}")
        if value < 0.0 or value > 0.999:
            raise WindowToWallRatioOutsideBoundaries(
                f"Surface {self.name}, wwrS must included between 0 and 1: {value}"
            )
        self._calc_glazed_and_opaque_areas(value)
        self.__wwr = value

    @property
    def subdivisions_solar_calc(self) -> dict:
        return self._subdivisions_solar_calc

    @subdivisions_solar_calc.setter
    def subdivisions_solar_calc(self, value: dict):
        if not isinstance(value, dict):
            raise TypeError(
                f"Surface {self.name}, subdivisions_solar_calc must be a dict: {value}"
            )
        try:
            self._azimuth_subdivisions = value["azimuth_subdivisions"]
        except KeyError:
            raise KeyError(
                f"Surface {self.name}, subdivisions_solar_calc must contain an azimuth_subdivisions key: {value}"
            )
        try:
            self._height_subdivisions = value["height_subdivisions"]
        except KeyError:
            raise KeyError(
                f"Surface {self.name}, subdivisions_solar_calc must contain an height_subdivisions key: {value}"
            )
        self._subdivisions_solar_calc = value
        self._set_azimuth_and_zenith_solar_radiation()

    @property
    def _azimuth_subdivisions(self) -> int:
        return self.__azimuth_subdivisions

    @_azimuth_subdivisions.setter
    def _azimuth_subdivisions(self, value: int):
        try:
            value = int(value)
        except ValueError:
            raise TypeError(
                f"Surface {self.name}, azimuth_subdivisions is not an int: {value}"
            )
        if value < 1 or value > 100:
            # Check if unreasonable values provided
            raise ValueError(
                f"Surface {self.name}, azimuth_subdivisions must be > 1 and lower than 100: {value}"
            )
        if value > 16 and not self.__warning_azimuth_subdivisions:
            logging.warning(
                f"For one or more surfaces azimuth_subdivisions is high: {value}.\nThe calculation time can be long"
            )
            self.__warning_azimuth_subdivisions = True
        self.__azimuth_subdivisions = value

    @property
    def _height_subdivisions(self) -> int:
        return self.__height_subdivisions

    @_height_subdivisions.setter
    def _height_subdivisions(self, value: int):
        try:
            value = int(value)
        except ValueError:
            raise TypeError(
                f"Surface {self.name}, height_subdivisions is not an int: {value}"
            )
        if value < 1 or value > 50:
            # Check if unreasonable values provided
            raise ValueError(
                f"Surface {self.name}, height_subdivisions must be > 1 and lower than 50: {value}"
            )
        if value > 6 and not self.__warning_height_subdivisions:
            logging.warning(
                f"For one or more surfaces height_subdivisions is high: {value}.\nThe calculation time can be long"
            )
            self.__warning_height_subdivisions = True
        self.__height_subdivisions = value

    @property
    def surface_type(self):
        return self._surface_type

    @surface_type.setter
    def surface_type(self, value):
        if not isinstance(value, str) and value is not None:
            raise TypeError(f"Surface {self.name}, surface_type is not a str: {value}")
        if value not in ["ExtWall", "GroundFloor", "Roof"]:
            raise InvalidSurfaceType(
                f"Surface {self.name}, surface_type must choosen from: [ExtWall, GroundFloor, Roof] {value}"
            )
        self._surface_type = value

    @property
    def construction(self):
        return self._construction

    @construction.setter
    def construction(self, value):
        if not isinstance(value, Construction):
            raise TypeError(f"Surface {self.name}, construction must be a Construction object: {type(value)}")
        self._construction = value

    @property
    def window(self):
        return self._window

    @window.setter
    def window(self, value):
        if not isinstance(value, SimpleWindow):
            raise TypeError(f"Surface {self.name}, window must be a SimpleWindow object: {type(value)}")
        self._window = value

    def _set_azimuth_and_zenith(self):

        # set the azimuth and zenith

        if self._normal[2] == 1:
            self._height = 0
            self._azimuth = 0
        elif self._normal[2] == -1:
            self._height = 180
            self._azimuth = 0
        else:
            self._height = 90 - np.degrees(
                np.arctan(
                    (
                            self._normal[2]
                            / (np.sqrt(self._normal[0] ** 2 + self._normal[1] ** 2))
                    )
                )
            )
            if self._normal[1] == 0:
                if self._normal[0] > 0:
                    self._azimuth = -90
                elif self._normal[0] < 0:
                    self._azimuth = 90
            else:
                if self._normal[1] < 0:
                    self._azimuth = np.degrees(
                        np.arctan(self._normal[0] / self._normal[1])
                    )
                else:
                    if self._normal[0] < 0:
                        self._azimuth = 180 + np.degrees(
                            np.arctan(self._normal[0] / self._normal[1])
                        )
                    else:
                        self._azimuth = -180 + np.degrees(
                            np.arctan(self._normal[0] / self._normal[1])
                        )

    def _calc_glazed_and_opaque_areas(self, wwr):
        self._opaque_area = (1 - wwr) * self._area
        self._glazed_area = wwr * self._area

    def _set_azimuth_and_zenith_solar_radiation(self):
        # Azimuth and tilt approximation

        delta_a = 360 / (2 * self._azimuth_subdivisions)
        delta_h = 90 / (2 * self._height_subdivisions)
        x = np.arange(-delta_h, 90 + 2 * delta_h, 2 * delta_h)

        for n in range(len(x) - 1):
            if self._height >= x[n] and self._height < x[n + 1]:
                self._height_round = int((x[n] + x[n + 1]) / 2)
                self._sky_view_factor = (1 + np.cos(np.radians(self._height_round))) / 2
            elif self._height >= x[-1] and self._height < 150:
                self._height_round = 90
                self._sky_view_factor = (1 + np.cos(np.radians(self._height_round))) / 2
            else:
                self._height_round = 0  # Only to avoid errors
        y = np.arange(-180 - delta_a, 180 + 2 * delta_a, 2 * delta_a)
        for n in range(len(y) - 1):
            if self._azimuth >= y[n] and self._azimuth < y[n + 1]:
                self._azimuth_round = int((y[n] + y[n + 1]) / 2)
                if self._azimuth_round == 180:
                    self._azimuth_round = -180
        if self._height_round == 0:
            self._azimuth_round = 0

    def _set_auto_surface_type(self):
        # Set surface inclination

        if self._height < 40:
            self.surface_type = "Roof"
        elif self._height > 150:
            self.surface_type = "GroundFloor"
        else:
            self.surface_type = "ExtWall"

    def max_height(self):
        hmax = 0
        for vert in self.__vertices:
            hmax = max(hmax, vert[2])
        return hmax

    def min_height(self):
        hmin = 10000
        for vert in self.__vertices:
            hmin = min(hmin, vert[2])
        return hmin


# %%---------------------------------------------------------------------------------------------------
# %% SurfaceInternalMass class


class SurfaceInternalMass:
    """
    Class to define a surface for thermal capacity using area and surface type
    with a specific geometry
    
    Methods:
        init
    """

    def __init__(self, name: str, area: float = 0., surface_type=None, construction=None):
        """
        input:
            area: area of the internal surface
            surfType: 'IntWall' or 'IntCeiling'

        Attributes:
            area
            surfType
            construction: Construction
                the construction object with the materials

        Parameters
            ----------
            name : string
                name of the surface
            area: float
                number of azimuth subdivision [m2]
            surface_type : string
                string that defines the surface type.
                'IntWall' or  'IntCeiling'  or 'IntFloor'

        Returns
        -------
        None.        
        
        """

        # Check input data type
        self.name = name
        self._area = area
        self.surface_type = surface_type
        if construction is not None:
            self.construction = construction

    @property
    def _area(self) -> float:
        return self.__area

    @_area.setter
    def _area(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(f"SurfaceInternalMass {self.name}, area is not an float: {value}")
        if value < 0.0:
            raise NegativeSurfaceArea(
                f"SurfaceInternalMass {self.name}, negative surface area: {value}"
            )
        if float(value) == 0.0:
            self.__area = 1e-10
        else:
            self.__area = value
        self._opaque_area = self._area
        self._glazed_area = 0.

    @property
    def surface_type(self):
        return self._surface_type

    @surface_type.setter
    def surface_type(self, value):
        if not isinstance(value, str) and value is not None:
            raise TypeError(f"SurfaceInternalMass {self.name}, surface_type is not a str: {value}")
        if value == None:
            logging.warning(f"SurfaceInternalMass {self.name}, surface_type is None: {value}. IntWall will be assigned")
            value = "IntWall"
        if value not in ["IntWall", "IntCeiling", "IntFloor"]:
            raise InvalidSurfaceType(
                f"Surface {self.name}, surface_type must choosen from: [IntWall, IntCeiling, IntFloor] {value}"
            )
        self._surface_type = value

    @property
    def construction(self):
        return self._construction

    @construction.setter
    def construction(self, value):
        if not isinstance(value, Construction):
            raise TypeError(f"Surface {self.name}, construction must be a Construction object: {type(value)}")
        self._construction = value
