__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

"""
This dictionary defines for each schedule type 
the properties using a JSON/Dictionary structure
"""
schedule_types = {
    "unit_type": [
        "dimensionless",
        "percent",
        "temperature",
        "capacity",
        "power",
    ]
}

internal_loads_prop = {
    "people": {
        "unit": ["W", "W/m2", "px", "px/m2", ],
        "fraction_latent": [0., 1.],
        "fraction_radiant": [0., 1.],
        "fraction_convective": [0., 1.],
        "MET": ["W/px"],
        "tags": [],
    },
    "light": {
        "unit": ["W", "W/m2", ],
        "fraction_to_zone": [0., 1.],
        "fraction_radiant": [0., 1.],
        "fraction_convective": [0., 1.],
        "tags": [],
    },
    "electric": {
        "unit": ["W", "W/m2", "W/px"],
        "fraction_to_zone": [0., 1.],
        "fraction_radiant": [0., 1.],
        "fraction_convective": [0., 1.],
        "tags": [],
    },
    "vapour": {
        "unit": ["W", "W/m2", "g", "g/m2", ],
        "fraction_to_zone": [0., 1.],
        "tags": [],
    },
}

setpoint_prop = {
    "temperature": {
        "unit": "°C",
        "limit": [-50., 60.],  # Throws just a warning
        "tags": [],
    },
    "relative_humidity": {
        "unit": "-",
        "limit": [0., 1.],  # Throws just a warning
        "tags": [],
    },
    # Eventually add the specific humidity
}
#
#     "ventilation": {
#         "mechanical": {
#             "unit": ["Vol/h", "kg/s", "kg/(m2 s)", "m3/s", "m3/(m2 s)"],
#         },
#         "natural": {
#             "unit": ["Vol/h", "kg/s", "kg/(m2 s)", "m3/s", "m3/(m2 s)"],
#         },
#         "infiltration": {
#             "unit": ["Vol/h", "kg/s", "kg/(m2 s)", "m3/s", "m3/(m2 s)"],
#         },
#     },
# }
