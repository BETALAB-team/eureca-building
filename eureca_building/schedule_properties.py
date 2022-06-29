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
        "Dimensionless",
        "Percent",
        "Temperature",
        "Capacity",
        "Power",
    ]
}

# schedule_types = {
#     "internal_load": {
#         "people": {
#             "unit": ["W", "W/m2", "px", "px/m2"],
#             "fraction_latent": [0., 1.],
#             "fraction_radiant": [0., 1.],
#             "fraction_sensible": [0., 1.],
#             "MET": ["W/px"],
#         },
#         "light": {
#             "unit": ["W", "W/m2", ],
#             "fraction_to_zone": [0., 1.],
#             "fraction_radiant": [0., 1.],
#             "fraction_sensible": [0., 1.],
#         },
#         "electric": {
#             "unit": ["W", "W/m2", ],
#             "fraction_to_zone": [0., 1.],
#             "fraction_radiant": [0., 1.],
#             "fraction_sensible": [0., 1.],
#         },
#         "vapour": {
#             "unit": ["W", "W/m2", "g", "g/m2"],
#             "fraction_to_zone": [0., 1.],
#         },
#
#     },
#     "setpoint": {
#         "temperature": {
#             "unit": ["C"],
#         },
#         "humidity": {
#             "unit": ["%", "kg_v/kg_as"],
#         },
#     },
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
