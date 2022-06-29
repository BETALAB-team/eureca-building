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
from eureca_building.internal_load import InternalLoad, People
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


class TestInternalHeatGains:

    def test_IHG(self):
        # Standard IHG
        sched = Schedule(
            "Percent1",
            "Percent",
            np.array([0.1, .2, .3, .5]),
            upper_limit=0.,
            lower_limit=1.,
        )

        InternalLoad(
            name='test_IHG',
            nominal_value=10.,
            schedule=sched,
        )

        People(
            name='test_IHG',
            unit='W/m2',
            nominal_value=10.,
            schedule=sched,
            fraction_latent=0.55,
            fraction_radiant=0.3,
            fraction_convective=0.7,
            metabolic_rate=110,
        )
