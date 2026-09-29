"""Unit tests for the pure ferrule dimension data module."""

from lib.ferrule_data import (
    SIZES, size_labels, find_size, get_size, LENGTH_VARIANTS, FerruleSize
)


def test_size_labels_are_unique_and_ordered():
    labels = size_labels()
    assert len(labels) == len(SIZES)
    # 1 in appears twice (Type A and Type B).
    assert any('1 in (A)' in l for l in labels)
    assert any('1 in (B)' in l for l in labels)


def test_find_size_roundtrips():
    for label in size_labels():
        size = find_size(label)
        assert isinstance(size, FerruleSize)
        assert f'{size.label} ({size.type})' == label


def test_find_size_unknown_returns_none():
    assert find_size('99 in (Z)') is None


def test_every_size_has_all_length_variants():
    for s in SIZES:
        for variant in LENGTH_VARIANTS:
            assert variant in s.lengths
            assert s.lengths[variant] > 0


def test_dimensions_are_physically_consistent():
    for s in SIZES:
        assert s.b < s.a, f'{s.label}: bore must be < tube OD'
        assert s.f < s.d, f'{s.label}: gasket dia must be < flange OD'
        assert s.f > s.b, f'{s.label}: gasket dia must be > bore'
        assert 0 < s.wall * 2 < s.a, f'{s.label}: wall must be sane'
        assert s.e > 0


def test_known_reference_values():
    half = find_size('DN15 / 1/2 in (A)')
    assert half.a == 12.70
    assert half.b == 9.40
    assert half.d == 25.00
    one_b = find_size('DN25 / 1 in (B)')
    assert one_b.d == 50.39
    one_a = find_size('DN25 / 1 in (A)')
    assert one_a.d == 34.00


def test_get_size_by_index():
    assert get_size(0).label == 'DN6 / 1/4 in'
