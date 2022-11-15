#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2013-2022 Pyresample Developers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Test cases for SPoint and SMultiPoint."""
import unittest

import numpy as np
import pytest

from pyresample.future.spherical import SMultiPoint, SPoint


class TestSPoint(unittest.TestCase):
    """Test SPoint."""

    def test_latitude_validity(self):
        # Test latitude outside range
        lon = 0
        lat = np.pi
        with pytest.raises(ValueError):
            SPoint(lon, lat)
        # Test inf
        lon = 0
        lat = np.inf
        with pytest.raises(ValueError):
            SPoint(lon, lat)

    def test_longitude_validity(self):
        # Test inf
        lon = np.inf
        lat = 0
        with pytest.raises(ValueError):
            SPoint(lon, lat)

    def test_raise_error_if_multi_point(self):
        lons = np.array([0, np.pi])
        lats = np.array([-np.pi / 2, np.pi / 2])
        with pytest.raises(ValueError):
            SPoint(lons, lats)

    def test_to_shapely(self):
        """Test conversion to shapely."""
        from shapely.geometry import Point
        lon = 0.0
        lat = np.pi / 2
        spherical_point = SPoint(lon, lat)
        shapely_point = Point(0.0, 90.0)
        self.assertTrue(shapely_point.equals_exact(spherical_point.to_shapely(), tolerance=1e-10))


class TestSMultiPoint(unittest.TestCase):
    """Test SMultiPoint."""

    def test_single_point(self):
        """Test behaviour when providing single lon,lat values."""
        # Single values must raise error
        with pytest.raises(ValueError):
            SMultiPoint(2, 1)
        # Array values must not raise error
        p = SMultiPoint([2], [1])
        assert p.lon.shape == (1,)
        assert p.lat.shape == (1,)
        assert p.vertices.shape == (1, 2)

    def test_vertices(self):
        """Test vertices property."""
        lons = np.array([0, np.pi])
        lats = np.array([-np.pi / 2, np.pi / 2])
        p = SMultiPoint(lons, lats)
        res = np.array([[0., -1.57079633],
                        [-3.14159265, 1.57079633]])
        self.assertTrue(np.allclose(p.vertices, res))

    def test_distance(self):
        """Test Vincenty formula."""
        lons = np.array([0, np.pi])
        lats = np.array([-np.pi / 2, np.pi / 2])
        p1 = SMultiPoint(lons, lats)
        lons = np.array([0, np.pi / 2, np.pi])
        lats = np.array([-np.pi / 2, 0, np.pi / 2])
        p2 = SMultiPoint(lons, lats)
        d12 = p1.distance(p2)
        d21 = p2.distance(p1)
        self.assertEqual(d12.shape, (2, 3))
        self.assertEqual(d21.shape, (3, 2))
        res = np.array([[0., 1.57079633, 3.14159265],
                        [3.14159265, 1.57079633, 0.]])
        self.assertTrue(np.allclose(d12, res))
        # Special case with 1 point
        p1 = SMultiPoint(lons[[0]], lats[[0]])
        p2 = SMultiPoint(lons[[0]], lats[[0]])
        d12 = p1.distance(p2)
        assert isinstance(d12, float)

    def test_hdistance(self):
        """Test Haversine formula."""
        lons = np.array([0, np.pi])
        lats = np.array([-np.pi / 2, np.pi / 2])
        p1 = SMultiPoint(lons, lats)
        lons = np.array([0, np.pi / 2, np.pi])
        lats = np.array([-np.pi / 2, 0, np.pi / 2])
        p2 = SMultiPoint(lons, lats)
        d12 = p1.hdistance(p2)
        d21 = p2.hdistance(p1)
        self.assertEqual(d12.shape, (2, 3))
        self.assertEqual(d21.shape, (3, 2))
        res = np.array([[0., 1.57079633, 3.14159265],
                        [3.14159265, 1.57079633, 0.]])
        self.assertTrue(np.allclose(d12, res))

    def test_eq(self):
        """Check the equality."""
        lons = [0, np.pi]
        lats = [-np.pi / 2, np.pi / 2]
        p = SMultiPoint(lons, lats)
        p1 = SMultiPoint(lons, lats)
        self.assertTrue(p == p1)

    def test_eq_antimeridian(self):
        """Check the equality with longitudes at -180/180 degrees."""
        lons = [np.pi, np.pi]
        lons1 = [-np.pi, -np.pi]
        lats = [-np.pi / 2, np.pi / 2]
        p = SMultiPoint(lons, lats)
        p1 = SMultiPoint(lons1, lats)
        self.assertTrue(p == p1)

    def test_neq(self):
        """Check the equality."""
        lons = np.array([0, np.pi])
        lats = [-np.pi / 2, np.pi / 2]
        p = SMultiPoint(lons, lats)
        p1 = SMultiPoint(lons + 0.1, lats)
        self.assertTrue(p != p1)

    def test_str(self):
        """Check the string representation."""
        lons = [0, np.pi]
        lats = [-np.pi / 2, np.pi / 2]
        p = SMultiPoint(lons, lats)
        self.assertEqual(str(p), '[[   0.  -90.]\n [-180.   90.]]')

    def test_repr(self):
        """Check the representation."""
        lons = [0, np.pi]
        lats = [-np.pi / 2, np.pi / 2]
        p = SMultiPoint(lons, lats)
        self.assertEqual(repr(p), '[[   0.  -90.]\n [-180.   90.]]')

    def test_to_shapely(self):
        """Test conversion to shapely."""
        from shapely.geometry import MultiPoint
        lons = np.array([0.0, np.pi])
        lats = np.array([-np.pi / 2, np.pi / 2])
        spherical_multipoint = SMultiPoint(lons, lats)
        shapely_multipoint = MultiPoint([(0.0, -90.0), (-180.0, 90.0)])
        self.assertTrue(shapely_multipoint.equals_exact(spherical_multipoint.to_shapely(), tolerance=1e-10))
