"""Tests for the Fusion-facing modeler using the adsk stub.

These verify that :func:`lib.ferrule_modeler.create_ferrule` drives the API
correctly: it sketches a closed profile, adds a centerline axis, and creates a
360-degree solid revolve. No real Fusion instance is required.
"""

import math
import pytest

from tests import adsk_stub
from lib.ferrule_data import find_size
from lib.ferrule_geometry import ProfileParams
from lib.ferrule_modeler import create_ferrule, MM_TO_CM


@pytest.fixture(autouse=True)
def _clean_recorder():
    adsk_stub.reset()
    yield
    adsk_stub.reset()


def _profile_point_count(size, params=None):
    from lib.ferrule_geometry import build_profile
    return len(build_profile(size, 'medium', params).points)


def test_create_ferrule_sketches_closed_loop():
    size = find_size('1/2 in (A)')
    create_ferrule(size, 'medium')
    line_calls = [c for c in adsk_stub.recorder().calls
                  if c[0] == 'sketchLines.addByTwoPoints']
    # One line per profile edge (closed polygon) plus the centerline.
    expected = _profile_point_count(size) + 1
    assert len(line_calls) == expected


def test_create_ferrule_uses_yz_plane():
    size = find_size('1/2 in (A)')
    create_ferrule(size, 'medium')
    add_calls = [c for c in adsk_stub.recorder().calls if c[0] == 'sketches.add']
    assert add_calls and add_calls[0][1]['plane'] == 'yz'


def test_create_ferrule_revolve_is_solid_full_angle():
    size = find_size('1/2 in (A)')
    create_ferrule(size, 'medium')
    create = [c for c in adsk_stub.recorder().calls if c[0] == 'revolve.createInput']
    angle = [c for c in adsk_stub.recorder().calls if c[0] == 'revolve.setAngleExtent']
    assert create and create[0][1]['solid'] is False  # False == solid body
    assert angle and angle[0][1]['angle'] == pytest.approx(math.pi * 2)


def test_create_ferrule_converts_mm_to_cm():
    size = find_size('1/2 in (A)')
    create_ferrule(size, 'medium')
    pts = [c[1] for c in adsk_stub.recorder().calls if c[0] == 'Point3D.create']
    # The flange outer radius D/2 must appear scaled to cm.
    expected = (size.d / 2.0) * MM_TO_CM
    assert any(abs(p['x'] - expected) < 1e-9 for p in pts)


def test_create_ferrule_sets_feature_name():
    size = find_size('1 in (B)')
    feat = create_ferrule(size, 'medium')
    assert feat.name == 'Ferrule 1 in (B)'


def test_recreate_replaces_previous_feature():
    size = find_size('1/2 in (A)')
    create_ferrule(size, 'medium')
    create_ferrule(size, 'long')  # should delete the prior Ferrule feature first
    design = adsk_stub.Design.cast(object())
    ferrule_feats = [design.rootComponent.features.item(i)
                     for i in range(design.rootComponent.features.count)
                     if design.rootComponent.features.item(i).name.startswith('Ferrule ')]
    assert len(ferrule_feats) == 1


def test_missing_profile_raises():
    size = find_size('1/2 in (A)')
    # Force the sketch to report zero profiles.
    design = adsk_stub.Design.cast(object())
    design.rootComponent.profile_count = 0
    with pytest.raises(RuntimeError):
        create_ferrule(size, 'medium')
