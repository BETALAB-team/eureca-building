"""
List of custom exceptions
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

from eureca_building.surface import Surface

s = Surface(name = 'S1', vertices = ((0, 0, 0), (1., 0, 0), (0, 1., 0)))

print(s._area)