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

    def test_IHG_creation(self):
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

    def test_people_schedules(self):
        # Standard IHG
        sched = Schedule(
            "Percent1",
            "Percent",
            np.array([0.1, .2, .3, .5]),
        )

        people1 = People(
            name='test_IHG',
            unit='W/m2',
            nominal_value=10.,
            schedule=sched,
            fraction_latent=0.45,
            fraction_radiant=0.3,
            fraction_convective=0.7,
        )

        conv, rad, lat = people1.get_loads(area=2.)
        assert (
                np.linalg.norm(conv - np.array([0.385, 0.77, 1.155, 1.925]) * 2) < 1e-5 and
                np.linalg.norm(rad - np.array([0.165, 0.33, 0.495, 0.825]) * 2) < 1e-5 and
                np.linalg.norm(lat - np.array([1.79928029e-07,
                                               3.59856058e-07,
                                               5.39784086e-07,
                                               8.99640144e-07]) * 2) < 1e-5
        )

    def test_people_schedules_2(self):
        # Standard IHG
        sched = Schedule(
            "Percent1",
            "Percent",
            np.array([0.1, .2, .3, .5]),
        )

        people1 = People(
            name='test_IHG',
            unit='px/m2',
            nominal_value=5.,
            schedule=sched,
            fraction_latent=0.45,
            fraction_radiant=0.3,
            fraction_convective=0.7,
            metabolic_rate=150,
        )

        conv, rad, lat = people1.get_loads(area=2.)
        assert (
                np.linalg.norm(conv - np.array([57.75,
                                                115.5,
                                                173.25,
                                                288.75,
                                                ])) < 1e-5 and
                np.linalg.norm(rad - np.array([24.75,
                                               49.5,
                                               74.25,
                                               123.75,
                                               ])) < 1e-5 and
                np.linalg.norm(lat - np.array([2.69892E-05,
                                               5.39784E-05,
                                               8.09676E-05,
                                               0.000134946,
                                               ])) < 1e-3
        )
