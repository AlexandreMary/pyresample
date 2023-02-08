# Copyright (C) 2010-2022 Pyresample developers
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Test AreaDefinition objects."""
import contextlib

import dask.array as da
import numpy as np
import pytest
import xarray as xr

from pyresample.future.geometry import SwathDefinition
from pyresample.geometry import SwathDefinition as LegacySwathDefinition
from pyresample.test.utils import create_test_latitude, create_test_longitude


@pytest.fixture(params=[LegacySwathDefinition, SwathDefinition],
                ids=["LegacySwathDefinition", "SwathDefinition"])
def swath_class(request):
    """Get one of the currently active 'SwathDefinition' classes.

    Currently only includes the legacy 'SwathDefinition' class and the future
    'SwathDefinition' class in 'pyresample.future.geometry.swath'.

    """
    return request.param


@pytest.fixture
def create_test_swath(swath_class):
    """Get a function for creating SwathDefinitions for testing.

    Should be used as a pytest fixture and will automatically run the test
    function with the legacy SwathDefinition class and the future
    SwathDefinition class. If tests require a specific class they should
    NOT use this fixture and instead use the exact class directly.

    """
    def _create_test_swath(lons, lats):
        return swath_class(lons, lats)
    return _create_test_swath


def _gen_swath_def_xarray_dask(create_test_swath):
    """Create a SwathDefinition with xarray[dask] data inside.

    Note that this function is not a pytest fixture so that each call returns a
    new instance of the swath definition with new instances of the data arrays.

    """
    lons, lats = _gen_swath_lons_lats()
    lons_dask = da.from_array(lons)
    lats_dask = da.from_array(lats)
    lons_xr = xr.DataArray(lons_dask, dims=('y', 'x'))
    lats_xr = xr.DataArray(lats_dask, dims=('y', 'x'))
    return create_test_swath(lons_xr, lats_xr)


def _gen_swath_def_xarray_numpy(create_test_swath):
    lons, lats = _gen_swath_lons_lats()
    lons_xr = xr.DataArray(lons, dims=('y', 'x'))
    lats_xr = xr.DataArray(lats, dims=('y', 'x'))
    return create_test_swath(lons_xr, lats_xr)


def _gen_swath_def_dask(create_test_swath):
    lons, lats = _gen_swath_lons_lats()
    lons_dask = da.from_array(lons)
    lats_dask = da.from_array(lats)
    return create_test_swath(lons_dask, lats_dask)


def _gen_swath_def_numpy(create_test_swath):
    lons, lats = _gen_swath_lons_lats()
    return create_test_swath(lons, lats)


def _gen_swath_def_numpy_small_noncontiguous(create_test_swath):
    swath_def = _gen_swath_def_numpy_small(create_test_swath)
    swath_def_subset = swath_def[:, slice(0, 2)]
    return swath_def_subset


def _gen_swath_def_numpy_small(create_test_swath):
    lons = np.array([[1.2, 1.3, 1.4, 1.5],
                     [1.2, 1.3, 1.4, 1.5]])
    lats = np.array([[65.9, 65.86, 65.82, 65.78],
                     [65.9, 65.86, 65.82, 65.78]])
    swath_def = create_test_swath(lons, lats)
    return swath_def


def _gen_swath_lons_lats():
    swath_shape = (50, 10)
    lon_start, lon_stop, lat_start, lat_stop = (3.0, 12.0, 75.0, 26.0)
    lons = create_test_longitude(lon_start, lon_stop, swath_shape)
    lats = create_test_latitude(lat_start, lat_stop, swath_shape)
    return lons, lats


class TestSwathHashability:
    """Test geometry objects being hashable and other related uses."""

    @pytest.mark.parametrize(
        "swath_def_func1",
        [
            _gen_swath_def_numpy,
            _gen_swath_def_dask,
            _gen_swath_def_xarray_numpy,
            _gen_swath_def_xarray_dask,
            _gen_swath_def_numpy_small_noncontiguous,
        ])
    def test_swath_as_dict_keys(self, swath_def_func1, create_test_swath):
        from ..utils import assert_maximum_dask_computes
        swath_def1 = swath_def_func1(create_test_swath)
        swath_def2 = swath_def_func1(create_test_swath)

        with assert_maximum_dask_computes(0):
            assert hash(swath_def1) == hash(swath_def2)
            assert isinstance(hash(swath_def1), int)

            test_dict = {}
            test_dict[swath_def1] = 5
            assert test_dict[swath_def1] == 5
            assert test_dict[swath_def2] == 5
            assert test_dict.get(swath_def2) == 5
            test_dict[swath_def2] = 6
            assert test_dict[swath_def1] == 6
            assert test_dict[swath_def2] == 6

    def test_non_contiguous_swath_hash(self, create_test_swath):
        """Test swath hash."""
        swath_def = _gen_swath_def_numpy_small(create_test_swath)
        swath_def_subset = _gen_swath_def_numpy_small_noncontiguous(create_test_swath)
        assert hash(swath_def) != hash(swath_def_subset)


class TestSwathBboxLonLats:
    """Test 'get_bbox_lonlats' for various swath cases."""

    @pytest.mark.parametrize(
        ("lon_start", "lon_stop", "lat_start", "lat_stop", "exp_nonforced_clockwise"),
        [
            (3.0, 12.0, 75.0, 26.0, True),  # [0, 0] at north-west corner
            (12.0, 3.0, 75.0, 26.0, False),  # [0, 0] at north-east corner
            (3.0, 12.0, 26.0, 75.0, False),  # [0, 0] at south-west corner
            (12.0, 3.0, 26.0, 75.0, True),  # [0, 0] at south-east corner
        ]
    )
    @pytest.mark.parametrize("force_clockwise", [False, True])
    @pytest.mark.parametrize("use_dask", [False, True])
    @pytest.mark.parametrize("use_xarray", [False, True])
    @pytest.mark.parametrize("nan_pattern", [None, "scan", "half", "whole"])
    def test_swath_def_bbox(
            self, create_test_swath,
            lon_start, lon_stop, lat_start, lat_stop,
            exp_nonforced_clockwise, force_clockwise, use_dask, use_xarray, nan_pattern):
        swath_shape = (50, 10)
        lons = create_test_longitude(lon_start, lon_stop, swath_shape)
        lats = create_test_latitude(lat_start, lat_stop, swath_shape)
        lons, lats = _add_nans_if_necessary(lons, lats, nan_pattern)
        lons, lats = _convert_type_if_necessary(lons, lats, use_dask, use_xarray)
        swath_def = create_test_swath(lons, lats)
        with _raises_if(nan_pattern == "whole", ValueError):
            bbox_lons, bbox_lats = swath_def.get_bbox_lonlats(force_clockwise=force_clockwise)
        if nan_pattern != "whole":
            _check_bbox_structure_and_values(bbox_lons, bbox_lats)
            _check_bbox_clockwise(bbox_lons, bbox_lats, exp_nonforced_clockwise, force_clockwise)

    def test_swath_def_bbox_decimated(self, create_test_swath):
        swath_def = _gen_swath_def_numpy(create_test_swath)
        bbox_lons, bbox_lats = swath_def.get_bbox_lonlats(frequency=None)
        assert len(bbox_lons) == len(bbox_lats)
        assert len(bbox_lons) == 4
        assert len(bbox_lons[0]) == 10
        assert len(bbox_lons[1]) == 50
        assert len(bbox_lons[2]) == 10
        assert len(bbox_lons[3]) == 50

        bbox_lons, bbox_lats = swath_def.get_bbox_lonlats(frequency=5)
        assert len(bbox_lons) == len(bbox_lats)
        assert len(bbox_lons) == 4
        assert len(bbox_lons[0]) == 5
        assert len(bbox_lons[1]) == 5
        assert len(bbox_lons[2]) == 5
        assert len(bbox_lons[3]) == 5
        assert bbox_lons[0][-1] == bbox_lons[1][0]


def _add_nans_if_necessary(lons, lats, nan_pattern):
    if nan_pattern == "scan":
        lons[20:30, -1] = np.nan
    elif nan_pattern == "half":
        lons[:25, -1] = np.nan
    elif nan_pattern == "whole":
        lons[:, -1] = np.nan
    return lons, lats


def _convert_type_if_necessary(lons, lats, use_dask, use_xarray):
    if use_dask:
        lons = da.from_array(lons)
        lats = da.from_array(lats)
    if use_xarray:
        lons = xr.DataArray(lons, dims=('y', 'x'))
        lats = xr.DataArray(lats, dims=('y', 'x'))
    return lons, lats


def _check_bbox_structure_and_values(bbox_lons, bbox_lats):
    assert not any(np.isnan(side_lon).any() for side_lon in bbox_lons)
    assert not any(np.isnan(side_lat).any() for side_lat in bbox_lats)
    assert len(bbox_lons) == len(bbox_lats)
    assert len(bbox_lons) == 4
    for side_lons, side_lats in zip(bbox_lons, bbox_lats):
        assert isinstance(side_lons, np.ndarray)
        assert isinstance(side_lats, np.ndarray)
        assert side_lons.shape == side_lats.shape


def _check_bbox_clockwise(bbox_lons, bbox_lats, exp_nonforced_clockwise, force_clockwise):
    is_cw = _is_clockwise(np.concatenate(bbox_lons), np.concatenate(bbox_lats))
    if exp_nonforced_clockwise or force_clockwise:
        assert is_cw
    else:
        assert not is_cw


@contextlib.contextmanager
def _raises_if(condition, exp_exception, *args, **kwargs):
    expectation = pytest.raises(exp_exception, *args, **kwargs) if condition else contextlib.nullcontext()
    with expectation:
        yield


def _is_clockwise(lons, lats):
    # https://stackoverflow.com/a/1165943/433202
    prev_point = (lons[0], lats[0])
    edge_sum = 0
    for point in zip(lons[1:], lats[1:]):
        xdiff = point[0] - prev_point[0]
        ysum = point[1] + prev_point[1]
        edge_sum += xdiff * ysum
        prev_point = point
    return edge_sum > 0
