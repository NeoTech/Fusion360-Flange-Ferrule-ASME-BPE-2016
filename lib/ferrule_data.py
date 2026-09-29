"""ASME BPE-2016 hygienic clamp ferrule dimension data.

This module encodes the published dimensions from ASME BPE Table DT-7-1
(Hygienic Clamp Ferrule Standard Dimensions and Tolerances) plus the derived
profile parameters that the standard does NOT fully pin down.

Dimension vocabulary (all millimetres):
    A    tube outside diameter (nominal size basis)
    B    bore diameter measured at the ferrule face
    D    flange outside diameter
    E    flange thickness (reference)
    F    gasket-groove / gasket-contact diameter
    L    overall ferrule length (short / medium / long variants)
    wall tube weld-end wall thickness

CAVEAT: The six published dimensions (A, B, D, E, F, L) do not fully define the
revolved profile. Gasket-groove depth/width, hub length, and weld-end chamfer are
an engineering interpretation. They are exposed as ``ProfileParams`` so a caller
can override them, and the values here are defensible defaults only. Verify
against a licensed copy of ASME BPE-2016 before releasing a manufacturing drawing.

The data below is transcribed from public manufacturer catalogs that reference
the BPE profile and is provided for modeling convenience, not as a substitute for
the licensed standard.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Length variants keyed by overall length L (mm).
LENGTH_VARIANTS = ("short", "medium", "long")

# Default overall lengths (L) shared across the small-bore family.
DEFAULT_LENGTHS_MM: Dict[str, float] = {
    "short": 12.70,
    "medium": 28.58,
    "long": 44.45,
}


@dataclass(frozen=True)
class FerruleSize:
    """A single nominal ferrule size / type row from Table DT-7-1."""

    label: str          # human label, e.g. '1/2 in'
    type: str           # 'A' or 'B'
    a: float            # tube OD
    b: float            # bore at face
    d: float            # flange OD
    e: float            # flange thickness (reference)
    f: float            # gasket-groove diameter
    wall: float         # weld-end wall thickness
    lengths: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_LENGTHS_MM))
    dn: Optional[str] = None  # metric DN equivalent, if any
    flange_angle: float = 20.0  # flange seat/hub angle C (deg) per DT-5-2
    g: float = 0.8      # gasket groove depth G (mm); half the groove width


# --- ASME BPE-2009 Table DT-5-2 (Hygienic Clamp Ferrule) -------------------
# Transcribed from the published table (inches) and converted to mm (x25.4).
# DT-5-2 lists nominal size in inches only; the DN equivalent is added to each
# label so DN<->inch sizes are easy to compare. The weld-end wall thickness is
# not published; it uses sensible family defaults.
# Groove depth G is set to half the groove width (0.8 mm) so the face ring is a
# clean shallow semicircle that stays within the thin tube wall; the standard's
# larger published G values are too deep for the modeled wall and are overridable
# in the dialog.
DT52_SIZES: List[FerruleSize] = [
    FerruleSize("DN6 / 1/4 in",   "A", 6.35,   4.57,  24.99, 3.63, 20.32, 0.89, dn="DN6", g=0.8),
    FerruleSize("DN10 / 3/8 in",   "A", 9.53,   7.75,  24.99, 3.63, 20.32, 0.89, dn="DN10", g=0.8),
    FerruleSize("DN15 / 1/2 in",   "A", 12.70,  9.40,  24.99, 3.63, 20.32, 1.65, dn="DN15", g=0.8),
    FerruleSize("DN20 / 3/4 in",   "A", 19.05,  15.75, 24.99, 3.63, 20.32, 1.65, dn="DN20", g=0.8),
    FerruleSize("DN25 / 1 in",     "A", 25.40,  22.10, 34.01, 3.63, 28.00, 1.65, dn="DN25", g=0.8),
    FerruleSize("DN25 / 1 in",     "B", 25.40,  22.10, 50.39, 2.84, 43.64, 1.65, dn="DN25", g=0.8),
    FerruleSize("DN38 / 1 1/2 in", "B", 38.10,  34.80, 50.39, 2.84, 43.64, 1.65, dn="DN38", g=0.8),
    FerruleSize("DN50 / 2 in",     "B", 50.80,  47.50, 63.91, 2.84, 56.34, 1.65, dn="DN50", g=0.8),
    FerruleSize("DN65 / 2 1/2 in", "B", 63.50,  60.20, 77.39, 2.84, 70.64, 1.65, dn="DN65", g=0.8),
    FerruleSize("DN76 / 3 in",     "B", 76.20,  72.90, 90.91, 2.84, 83.34, 1.65, dn="DN76", g=0.8),
    FerruleSize("DN100 / 4 in",     "B", 101.60, 97.38, 118.92, 2.84, 110.34, 1.65, dn="DN100", g=0.8),
    FerruleSize("DN150 / 6 in",     "B", 152.40, 146.86, 166.88, 5.59, 156.87, 2.00, dn="DN150", g=0.8),
]


@dataclass(frozen=True)
class Standard:
    """A selectable ASME BPE ferrule dimensional table."""

    key: str                 # short id, e.g. 'DT-5-2'
    title: str               # dropdown label
    sizes: List[FerruleSize]


# Registry of supported metallic ferrule standards, in dropdown order.
STANDARDS: List[Standard] = [
    Standard("DT-5-2", "ASME BPE-2009 DT-5-2", DT52_SIZES),
]

# Default table (DT-5-2 is the commonly stocked hygienic clamp ferrule).
SIZES: List[FerruleSize] = DT52_SIZES

_DEFAULT_STANDARD = "DT-5-2"


def standard_keys() -> List[str]:
    """Dropdown keys for every supported standard, in order."""
    return [s.key for s in STANDARDS]


def standard_titles() -> List[str]:
    """Dropdown titles for every supported standard, in order."""
    return [s.title for s in STANDARDS]


def get_standard(key: str) -> Standard:
    """Return the :class:`Standard` for a key (default DT-5-2 if unknown)."""
    for s in STANDARDS:
        if s.key == key:
            return s
    return STANDARDS[0]


def size_labels(standard_key: str = _DEFAULT_STANDARD) -> List[str]:
    """Dropdown labels for every size/type combination, in table order."""
    return [f"{s.label} ({s.type})" for s in get_standard(standard_key).sizes]


def find_size(label: str, standard_key: str = _DEFAULT_STANDARD) -> Optional[FerruleSize]:
    """Look up a :class:`FerruleSize` by its :func:`size_labels` string.

    Accepts the full label (``"DN15 / 1/2 in (A)"``) or the inch-and-type
    suffix alone (``"1/2 in (A)"``) for convenience.
    """
    sizes = get_standard(standard_key).sizes
    labels = [f"{s.label} ({s.type})" for s in sizes]
    if label in labels:
        return sizes[labels.index(label)]
    for i, l in enumerate(labels):
        if l.endswith(" / " + label) or l == label:
            return sizes[i]
    return None


def get_size(index: int, standard_key: str = _DEFAULT_STANDARD) -> FerruleSize:
    """Return the size at a dropdown index."""
    return get_standard(standard_key).sizes[index]
