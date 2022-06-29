"""
Tests for schedules
"""

__author__ = "Enrico Prataviera"
__credits__ = ["Enrico Prataviera"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Enrico Prataviera"

import os

import pytest
import numpy as np

from eureca_building.schedule import Schedule
from eureca_building.exceptions import (
    InvalidScheduleType,
    ScheduleOutsideBoundaryCondition,
    InvalidScheduleDimension,
)


class TestSchedule:
    """
    This is a test class for the pytest module.
    It tests Schedules class and Internal Heat Gains
    """

    def test_schedule(self):
        # Standard schedule
        Schedule(
            "Temperature1",
            "Temperature",
            np.random.rand(100) + 10,
        )

    def test_schedule_2(self):
        # Standard schedule
        with pytest.raises(ScheduleOutsideBoundaryCondition):
            Schedule(
                "Temperature1",
                "Temperature",
                np.random.rand(100) + 10,
                upper_limit=5,
                lower_limit=-10,
            )

    def test_schedule_3(self):
        # Standard schedule
        with pytest.raises(InvalidScheduleDimension):
            Schedule(
                "Temperature1",
                "Temperature",
                np.array([[3, 3, 3, 5]]) + 10,
                upper_limit=5,
                lower_limit=-10,
            )
