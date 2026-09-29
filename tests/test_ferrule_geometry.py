"""Unit tests for the pure revolved-profile geometry builder."""

import math
import pytest

from lib.ferrule_data import find_size
from lib.ferrule_geometry import (
    ProfileParams, build_profile, validate_profile
)


def _sizes():
    return [find_size(l) for l in
            ['1/4 in (A)', '1/2 in (A)', '3/4 in (A)', '1 in (A)', '1 in (B)',
             '1 1/2 in (B)', '2 in (B)', '2 1/2 in (B)', '3 in (B)', '4 in (B)']]


def test_profile_is_closed_loop():
    size = find_size('1/2 in (A)')
    result = build_profile(size, 'medium')
    pts = result.points
    # A closed polygon: consecutive points distinct, last connects to first.
    # Straight tube + flange + hub profile has 7 points (no groove).
    assert len(pts) >= 7
    assert pts[0] != pts[-1]


def test_all_radii_positive():
    for size in _sizes():
        result = build_profile(size, 'medium')
        for (x, y) in result.points:
            assert x > 0, f'{size.label}: radius must be positive'


def test_face_at_y_zero_and_weld_end_at_L():
    size = find_size('1/2 in (A)')
    L = size.lengths['medium']
    result = build_profile(size, 'medium')
    ys = [p[1] for p in result.points]
    assert min(ys) == 0.0
    assert max(ys) == pytest.approx(L)


def test_bore_radius_matches_B():
    size = find_size('1/2 in (A)')
    result = build_profile(size, 'medium')
    # First point is the bore at the face.
    assert result.points[0] == pytest.approx((size.b / 2.0, 0.0))


def test_flange_radius_matches_D():
    size = find_size('1/2 in (A)')
    result = build_profile(size, 'medium')
    radii = [p[0] for p in result.points]
    assert max(radii) == pytest.approx(size.d / 2.0)


def test_groove_adds_points_when_enabled():
    size = find_size('1/2 in (A)')
    no_groove = build_profile(size, 'medium', ProfileParams(groove_depth=0.0))
    groove = build_profile(size, 'medium', ProfileParams(groove_depth=0.5, groove_width=1.6))
    assert len(groove.points) == len(no_groove.points) + 3


def test_groove_disabled_when_out_of_bounds():
    size = find_size('1/2 in (A)')
    # Groove centered on F/2 but absurdly wide -> should be skipped.
    result = build_profile(size, 'medium', ProfileParams(groove_depth=0.5, groove_width=100.0))
    base = build_profile(size, 'medium', ProfileParams(groove_depth=0.0))
    assert len(result.points) == len(base.points)


def test_validate_passes_for_all_sizes():
    for size in _sizes():
        result = build_profile(size, 'medium')
        assert validate_profile(result) == [], f'{size.label} should be valid'


def test_validate_flags_bad_weld_chamfer():
    size = find_size('1/2 in (A)')
    # Chamfer larger than the wall at the weld end.
    params = ProfileParams(weld_chamfer=10.0)
    result = build_profile(size, 'medium', params)
    errors = validate_profile(result)
    assert any('chamfer' in e.lower() for e in errors)


def test_overall_length_property():
    size = find_size('1/2 in (A)')
    result = build_profile(size, 'long')
    assert result.overall_length == size.lengths['long']


def test_length_variant_changes_L():
    size = find_size('1/2 in (A)')
    short = build_profile(size, 'short')
    long = build_profile(size, 'long')
    assert max(p[1] for p in long.points) > max(p[1] for p in short.points)
