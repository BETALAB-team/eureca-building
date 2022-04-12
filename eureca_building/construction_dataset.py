"""
This module includes a container class for materials, constructions, and windows
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import pandas as pd

from eureca_building.construction import Construction
from eureca_building.window import SimpleWindow
from eureca_building.material import Material
from eureca_building.logs import logs_printer


class ConstructionDataset:
    """
    This class is a class to include the list of materials,
    construction and windows that are used in the project

    Attributes:
        self.materials_dict:
            Dict: dictionary with all materials
        self.constructions_dict:
            Dict: dictionary with all constructions
        self.windows_dict:
            Dict: dictionary with all windows
    """

    def __init__(self):
        """
        Generates the ConstructionDataset and the list of materials,
        contructions, and windows

        Returns
        -------
        None.

        """

        self.materials_dict = {}
        self.constructions_dict = {}
        self.windows_dict = {}

    @classmethod
    def read_excel(cls, file):
        dataset = cls.__init__()

        data = pd.read_excel(file, sheetname=None)

        # Windows
        for win_idx in data["Windows"].index:
            win = data["Windows"].loc(win_idx)
            dataset.windows_dict[win_idx] = SimpleWindow(
                idx=win_idx,
                name=win["name"],
                u_value=win["U [W/(m²K)]"],
                solar_heat_gain_coef=win["Solar_Heat_Gain_Coef [-]"],
                visible_transmittance=win["visible_transmittance [-]"],
                frame_factor=win["frame_factor [-]"],
                shading_coef_int=win["shading_coeff_int [-]"],
                shading_coef_ext=win["shading_coeff_ext [-]"],
            )
        # Materials
        for mat_idx in data["Materials"].index:
            mat = data["Materials"].loc(mat_idx)
            if mat["Material_type"] == "Opaque":
                dataset.materials_dict[win_idx] = Material(
                    idx=mat_idx,
                    name=mat["name"],
                    thick=mat["Thickness [m]"],
                    cond=mat["Conductivity [W/(m K)]"],
                    spec_heat=mat["Specific_heat [J/(kg K)]"],
                    dens=mat["Density [kg/m³]"],
                )
