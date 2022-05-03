"""
This module includes functions to model a 3D surface
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import numpy as np

from eureca_building.logs import logs_printer
from eureca_building.exeptions import (
    Non3ComponentsVertex,
    WindowToWallRatioOutsideBoundaries,
    InvalidSurfaceType,
    NonPlanarSurface,
    NegativeSurfaceArea,
)
from eureca_building._geometry_auxiliary_functions import (
    check_complanarity,
    poly_area,
    normal_versor_2,
)

#%% Surface class


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
        vertices: tuple = ([0, 0, 0], [0, 0, 0], [0, 0, 0]),
        azimuth_subdivisions: int = 8,
        height_subdivisions: int = 3,
        wwr: float = 0.0,
        surface_type=None,
    ):
        """
        Creates the surface object

        Parameters
        ----------
        name : str
            Name.
        vertices : tuple, optional
            List of vertixes coordinates [m]. The default is ([0, 0, 0], [0, 0, 0], [0, 0, 0]).
        azimuth_subdivisions : int, optional
            Number of azimuth discretization for radiation purposes. The default is 8.
        height_subdivisions : int, optional
            Number of heaigh discretization for radiation purposes. The default is 3.
        wwr : float, optional
            window to wall ratio (between  and 0 and 1). The default is 0.0.
        surface_type : str, optional
            Type of surface 'ExtWall' or 'GroundFloor' or 'Roof'.
            If not provided autocalculate.

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
        self.vertices = vertices
        self.azimuth_subdivisions = azimuth_subdivisions
        self.height_subdivisions = height_subdivisions
        self.wwr = wwr
        self.surface_type = surface_type

        # Check coplanarity

        if not check_complanarity(self.vertices):
            raise NonPlanarSurface(f"Surface {self.name}. Non planar points")
        # Area calculation

        self.area = poly_area(self.vertices)
        if self.area == 0.0:
            self.area = 0.0000001
        """
        Considering only three points in calculating the normal vector could create
        reverse orientations if the three points are in a non-convex angle of the surface

        for this reason theres an alternative way to calculate the normal,
        implemented in function: normalAlternative

        reference: https://stackoverflow.com/questions/32274127/how-to-efficiently-determine-the-normal-to-a-polygon-in-3d-space
        """

        self.normal = normal_versor_2(self.vertList)

        self._set_azimuth_and_zenith()
        # Run in sequence
        self._set_azimuth_and_zenith_solar_radiation()

        if isinstance(surface_type, None):
            self._set_auto_surface_type()
        # # Set the window area

        # if self.type == "ExtWall":
        #     self.centroid_coord = centroid(vertList)
        #     if 135 < self.azimuth_round <= 180 or -180 <= self.azimuth_round < -135:
        #         self.wwr = wwr[0]
        #     elif -135 <= self.azimuth_round <= -45:
        #         self.wwr = wwr[1]
        #     elif -45 < self.azimuth_round < 45:
        #         self.wwr = wwr[2]
        #     elif 45 <= self.azimuth_round <= 135:
        #         self.wwr = wwr[3]
        # else:
        #     self.wwr = 0
        # self.opaqueArea = (1 - self.wwr) * self.area
        # self.glazedArea = (self.wwr) * self.area
        # if self.glazedArea == 0:
        #     self.glazedArea = 0.0000001  # Avoid zero division
        # if self.opaqueArea == 0:
        #     self.opaqueArea = 0.0000001  # Avoid zero division

    @property
    def vertices(self) -> tuple:
        return self._vertices

    @vertices.setter
    def vertices(self, value: tuple):
        try:
            value = tuple(value)
        except ValueError:
            raise TypeError(f"Vertices of surface {self.name} are not a tuple: {value}")
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
                vtx[0] = float(vtx[0])
                vtx[1] = float(vtx[1])
                vtx[2] = float(vtx[2])
            except ValueError:
                raise ValueError(
                    f"Surface {self.name}. One vertex contains non float values: {vtx}"
                )
        self._vertices = value

    @property
    def azimuth_subdivisions(self) -> int:
        return self._azimuth_subdivisions

    @azimuth_subdivisions.setter
    def azimuth_subdivisions(self, value: int):
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
            logs_printer(
                f"For one or more surfaces azimuth_subdivisions is high: {value}.\nThe calculation time can be long"
            )
            self.__warning_azimuth_subdivisions = True
        self._azimuth_subdivisions = value

    @property
    def height_subdivisions(self) -> int:
        return self._height_subdivisions

    @height_subdivisions.setter
    def height_subdivisions(self, value: int):
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
            logs_printer(
                f"For one or more surfaces height_subdivisions is high: {value}.\nThe calculation time can be long"
            )
            self.__warning_height_subdivisions = True
        self._height_subdivisions = value

    @property
    def wwr(self) -> float:
        return self._wwr

    @wwr.setter
    def wwr(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(f"Surface {self.name}, wwr is not an float: {value}")
        if value < 0.0 or value > 0.999:
            raise WindowToWallRatioOutsideBoundaries(
                f"Surface {self.name}, wwrS must included between 0 and 1: {value}"
            )
        self._wwr = value

    @property
    def surface_type(self):
        return self._surface_type

    @surface_type.setter
    def surface_type(self, value):
        if not isinstance(value, str) and not isinstance(value, None):
            raise TypeError(f"Surface {self.name}, surface_type is not a str: {value}")
        if value not in ["ExtWall", "GroundFloor", "Roof"]:
            raise InvalidSurfaceType(
                f"Surface {self.name}, surface_type must choosen from: [ExtWall, GroundFloor, Roof] {value}"
            )
        self._surface_type = value

    @property
    def area(self) -> float:
        return self._area

    @area.setter
    def area(self, value: float):
        try:
            value = float(value)
        except ValueError:
            raise TypeError(f"Surface {self.name}, area is not an float: {value}")
        if value < 0.0:
            raise NegativeSurfaceArea(
                f"Surface {self.name}, negative surface area: {value}"
            )
        self._area = value

    def _set_azimuth_and_zenith(self):

        # set the azimuth and zenith

        if self.normal[2] == 1:
            self._height = 0
            self._azimuth = 0
        elif self.normal[2] == -1:
            self._height = 180
            self._azimuth = 0
        else:
            self._height = 90 - np.degrees(
                np.arctan(
                    (
                        self.normal[2]
                        / (np.sqrt(self.normal[0] ** 2 + self.normal[1] ** 2))
                    )
                )
            )
            if self.normal[1] == 0:
                if self.normal[0] > 0:
                    self._azimuth = -90
                elif self.normal[0] < 0:
                    self._azimuth = 90
            else:
                if self.normal[1] < 0:
                    self._azimuth = np.degrees(
                        np.arctan(self.normal[0] / self.normal[1])
                    )
                else:
                    if self.normal[0] < 0:
                        self._azimuth = 180 + np.degrees(
                            np.arctan(self.normal[0] / self.normal[1])
                        )
                    else:
                        self._azimuth = -180 + np.degrees(
                            np.arctan(self.normal[0] / self.normal[1])
                        )

    def _set_azimuth_and_zenith_solar_radiation(self):
        # Azimuth and tilt approximation

        delta_a = 360 / (2 * self.azimuth_subdivisions)
        delta_h = 90 / (2 * self.height_subdivisions)
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

        """
        Find the higher vertex

        
        Parameters
            ----------
            None
                
        Returns
        -------
        float.    [m]     
        
        """

        hmax = 0
        for vert in self.vertices:
            hmax = max(hmax, vert[2])
        return hmax

    def min_height(self):

        """
        Find the lower vertex

        
        Parameters
            ----------
            None
                
        Returns
        -------
        float.        [m] 
        
        """

        hmin = 10000
        for vert in self.vertices:
            hmin = min(hmin, vert[2])
        return hmin

    # def reduceInternalHoles(self, hole_area, hole_points_list, rh_gross=1.0):
    #     self.area -= hole_area * rh_gross
    #     if self.area < 1e-10:
    #         self.area = 0.0000001
    #     self.opaqueArea = (1 - self.wwr) * self.area
    #     self.glazedArea = (self.wwr) * self.area
    #     if self.glazedArea == 0:
    #         self.glazedArea = 0.0000001  # Avoid zero division
    #     if self.opaqueArea == 0:
    #         self.opaqueArea = 0.0000001  # Avoid zero division
    #     try:
    #         self.internal_holes_list
    #     except AttributeError:
    #         self.internal_holes_list = []
    #     self.internal_holes_list.append(hole_points_list)

    # def checkSurfaceCoincidence(self, otherSurface):
    #     """
    #     Check if two surface are coincident

    #     Parameters
    #         ----------
    #         otherSurface : EUReCA.RC_classes.geometry.Surface
    #             another surface object

    #     Returns
    #     -------
    #     boolean. Are the surfaces coincident? True/Flase
    #     """

    #     # Check Input data type

    #     if not isinstance(otherSurface, Surface):
    #         raise ValueError(
    #             f"ERROR Surface class, surface {self.name}, checkSurfaceCoincidence. otherSurface is not a Surface object: otherSurface {otherSurface}"
    #         )
    #     # Check the coincidence of two surface looking firstly at the coplanarity
    #     # of the points and then the direction of the normals vectors

    #     flagPoints = False
    #     plane = self.vertList

    #     # Coplanarity test
    #     for i in otherSurface.vertList:
    #         if check_complanarity(plane + [i], precision=5):
    #             flagPoints = True
    #     # Normal vector test
    #     flagNormal = False
    #     if np.linalg.norm(self.normal + otherSurface.normal) < 0.2:
    #         flagNormal = True
    #     return flagNormal and flagPoints

    # def calculateIntersectionArea(self, otherSurface):
    #     """
    #     Claculates the area between two adjacent surfaces

    #     reference: https://stackoverflow.com/questions/39003450/transform-3d-polygon-to-2d-perform-clipping-and-transform-back-to-3d

    #     Parameters
    #         ----------
    #         otherSurface : EUReCA.RC_classes.geometry.Surface
    #             another surface object

    #     Returns
    #     -------
    #     float. The area [m2]
    #     """

    #     # Check Input data type

    #     if not isinstance(otherSurface, Surface):
    #         raise ValueError(
    #             f"ERROR Surface class, surface {self.name}, calculateIntersectionArea. otherSurface is not a Surface object: otherSurface {otherSurface}"
    #         )
    #     # Check the coincidence of two surface looking firstly at the coplanarity
    #     # of the points and then the direction of the normals vectors
    #     a = (
    #         self.normal[0] * self.vertList[0][0]
    #         + self.normal[1] * self.vertList[0][1]
    #         + self.normal[2] * self.vertList[0][2]
    #     )
    #     proj_axis = max(range(3), key=lambda i: abs(self.normal[i]))
    #     projA = [project(x, proj_axis) for x in self.vertList]
    #     projB = [project(x, proj_axis) for x in otherSurface.vertList]
    #     scaledA = pc.scale_to_clipper(projA)
    #     scaledB = pc.scale_to_clipper(projB)
    #     clipper = pc.Pyclipper()
    #     clipper.AddPath(scaledA, poly_type=pc.PT_SUBJECT, closed=True)
    #     clipper.AddPath(scaledB, poly_type=pc.PT_CLIP, closed=True)
    #     intersections = clipper.Execute(
    #         pc.CT_INTERSECTION, pc.PFT_NONZERO, pc.PFT_NONZERO
    #     )
    #     intersections = [pc.scale_from_clipper(i) for i in intersections]
    #     if len(intersections) == 0:
    #         return 0
    #     intersection = [
    #         project_inv(x, proj_axis, a, self.normal) for x in intersections[0]
    #     ]
    #     area = poly_area(intersection)
    #     return area if area > 0 else 0.0

    # def reduceArea(self, AreaToReduce):
    #     """
    #     Reduces the area of the surface

    #     Parameters
    #         ----------
    #         AreaToReduce : float
    #             the area to subtract [m2]

    #     Returns
    #     -------
    #     None.
    #     """

    #     # Check Input data type

    #     if not isinstance(AreaToReduce, float) or AreaToReduce < 0.0:
    #         try:
    #             AreaToReduce = float(AreaToReduce)
    #         except ValueError:
    #             raise ValueError(
    #                 f"ERROR Surface class, surface {self.name}, reduceArea. The area is not a positive float: AreaToReduce {AreaToReduce}"
    #             )
    #     # Area reduction

    #     if self.area - AreaToReduce > 0.0000001:
    #         self.area = self.area - AreaToReduce
    #         self.opaqueArea = (1 - self.wwr) * self.area
    #         self.glazedArea = (self.wwr) * self.area
    #     else:
    #         self.area = 0.0000001
    #         self.opaqueArea = 0.0000001
    #         self.glazedArea = 0.0000001

    # def printInfo(self):

    #     """
    #     Just prints some attributes of the surface

    #     Parameters
    #         ----------
    #         None

    #     Returns
    #     -------
    #     None.
    #     """

    #     print(
    #         "Name: "
    #         + self.name
    #         + "\nArea: "
    #         + str(self.area)
    #         + "\nType: "
    #         + str(self.type)
    #         + "\nAzimuth: "
    #         + str(self.azimuth)
    #         + "\nHeight: "
    #         + str(self.height)
    #         + "\nVertices: "
    #         + str(self.vertList)
    #         + "\n"
    #     )


#%%---------------------------------------------------------------------------------------------------
#%% SurfaceInternalMass class


class SurfaceInternalMass:

    """
    Class to define a surface for thermal capacity using area and surface type
    with a specific geometry
    
    Methods:
        init
    """

    def __init__(self, name, area=0.0000001, surfType="IntWall"):
        """
        input:
            area: area of the internal surface
            surfType: 'IntWall' or 'IntCeiling'

        attrubutes:
            area
            surfType

        Parameters
            ----------
            name : string
                name of the surface
            area: float
                number of azimuth subdivision [m2]
            surfType : string
                string that defines the surface type.
                'IntWall' or  'IntCeiling'  or 'IntFloor'
                
        Returns
        -------
        None.        
        
        """

        # Check input data type

        if not isinstance(name, str):
            raise TypeError(
                f"ERROR SurfaceInternalMass class geometry, name is not a string: name {name}"
            )
        if not isinstance(area, float) or area < 0.0:
            raise TypeError(
                f"ERROR SurfaceInternalMass class geometry, area is not a positive float: area {area}"
            )
        if not surfType in ["IntWall", "IntCeiling", "IntFloor"]:
            raise TypeError(
                f"ERROR SurfaceInternalMass class geometry, surfType is not a correct string: surfType {surfType}"
            )
        # Sets some attributes

        self.name = name
        self.area = area
        self.type = surfType
        if self.area < 0.0000001:
            self.area = 0.0000001
        self.opaqueArea = self.area


#%%---------------------------------------------------------------------------------------------------
#%% SurfaceInternalAdjacent class


class SurfaceInternalAdjacent(SurfaceInternalMass):

    """
    Inherited from SurfaceInternalMass
    adds the adjacentZone attribute
    Currently not used in the code
    
    """

    def __init__(self, name, area, surfType="IntCeiling", adjacentZone=None):
        super().__init__(area, surfType)
        self.adjacentZone = adjacentZone
