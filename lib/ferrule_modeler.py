"""Fusion 360 modeler: turns a ferrule profile into a revolved solid.

This is the only geometry module that imports ``adsk``. The pure profile math
lives in :mod:`lib.ferrule_geometry` so it can be unit-tested without Fusion.

All public functions accept an optional ``app``/``design`` injection point so the
test suite can pass a stub. In production they default to the live application.
"""

import math
from typing import List, Tuple

import adsk.core
import adsk.fusion

from .ferrule_data import FerruleSize
from .ferrule_geometry import ProfileParams, build_profile

# Fusion internal length unit is centimetres; our profile is millimetres.
MM_TO_CM = 0.1


def _active_design():
    app = adsk.core.Application.get()
    return app, adsk.fusion.Design.cast(app.activeProduct)


def create_ferrule(size: FerruleSize, length_variant: str = "medium",
                   params: ProfileParams = None, *,
                   preview: bool = False) -> "adsk.fusion.Component":
    """Model a ferrule as a revolved solid in its own new component.

    Each call creates a fresh component so the add-in can be run repeatedly
    without replacing previously generated ferrules. A transient preview
    component (``preview=True``) is removed first so previews never stack, and
    the committed run replaces it. Returns the new :class:`Component`.
    """
    app, design = _active_design()
    if design is None:
        raise RuntimeError("A part design must be active to create a ferrule.")

    root: adsk.fusion.Component = design.rootComponent

    # Drop any leftover preview component before building the new one.
    _delete_preview(root)

    # New component (and its occurrence) at the root origin.
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp: adsk.fusion.Component = occ.component

    profile = build_profile(size, length_variant, params)

    # Sketch on the component's YZ origin plane; sketch-space (x, y) == (radius, axial).
    plane = comp.yZConstructionPlane
    sketch: adsk.fusion.Sketch = comp.sketches.add(plane)

    _draw_profile(sketch, profile.segments)
    axis = _draw_centerline(sketch, profile.points)

    profiles = sketch.profiles
    if profiles.count < 1:
        raise RuntimeError("Profile loop did not close; nothing to revolve.")

    rev = comp.features.revolveFeatures
    rfi = rev.createInput(profiles.item(0), axis, False)  # False = solid
    rfi.setAngleExtent(False, adsk.core.ValueInput.createByReal(math.pi * 2))
    feature = rev.add(rfi)
    feature.name = f"Ferrule {size.label} ({size.type})"

    suffix = " (preview)" if preview else ""
    comp.name = f"Ferrule {size.label} ({size.type}){suffix}"
    return comp


def _pt(p: Tuple[float, float]):
    return adsk.core.Point3D.create(p[0] * MM_TO_CM, p[1] * MM_TO_CM, 0)


def _draw_profile(sketch: adsk.fusion.Sketch, segments):
    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    for seg in segments:
        if seg["type"] == "line":
            lines.addByTwoPoints(_pt(seg["p"]), _pt(seg["q"]))
        else:
            arcs.addByThreePoints(_pt(seg["start"]), _pt(seg["mid"]),
                                  _pt(seg["end"]))


def _draw_centerline(sketch: adsk.fusion.Sketch, points: List[Tuple[float, float]]):
    """Add the revolve axis as a sketch centerline along the sketch y-axis."""
    top = max(p[1] for p in points)
    p1 = adsk.core.Point3D.create(0, -0.5 * MM_TO_CM, 0)
    p2 = adsk.core.Point3D.create(0, (top + 1.0) * MM_TO_CM, 0)
    line = sketch.sketchCurves.sketchLines.addByTwoPoints(p1, p2)
    line.isConstruction = True
    line.isCenterLine = True
    return line


PREVIEW_SUFFIX = " (preview)"


def _delete_preview(root: adsk.fusion.Component):
    """Remove any transient preview component left over from a previous pass.

    Only components whose name ends with the preview marker are deleted, so
    previously committed ferrules are never touched.
    """
    for i in range(root.occurrences.count - 1, -1, -1):
        occ = root.occurrences.item(i)
        name = occ.name or ""
        if name.startswith("Ferrule ") and name.endswith(PREVIEW_SUFFIX):
            try:
                occ.deleteMe()
            except Exception:
                pass
