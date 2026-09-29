"""Parametric revolved-profile builder for an ASME BPE clamp ferrule.

Pure geometry: no ``adsk`` imports, so this is unit-testable outside Fusion.

Coordinate convention (sketch space):
    x = radius from the ferrule centerline (always >= 0)
    y = axial position; the gasket face lies at y = 0 and the weld end at y = L.

The profile is returned as an ordered list of ``segments`` (straight lines and
circular arcs) that trace a single closed loop (counter-clockwise) suitable for
revolving 360 degrees about the centerline (the sketch y-axis). The loop never
touches the axis because the ferrule has a through bore. ``points`` is the flat
ordered list of every segment endpoint (and arc mid-point) for quick bounding
checks and tests.

Profile interpretation (the parts the standard does NOT fully define):
    * At the gasket face sits a flat flange disc of OD ``D`` and thickness ``E``.
      The flange meets the tube through a short conical hub that rises at the
      published flange angle ``C`` measured from the flange back plane, so its
      axial run is ``(D/2 - A/2) * tan(C)`` (a shallow ramp, not a long taper).
      The concave corner where the hub meets the tube is rounded by the hub
      fillet ``R1`` (a tangent arc, see ``hub_fillet``).
    * The weld end carries a 45-degree weld-prep chamfer on BOTH the outer
      (``weld_chamfer``) and inner / bore (``bore_chamfer``) corners.
    * An optional rounded gasket ring groove of ``groove_depth`` x
      ``groove_width`` is cut into the face, centered on the tube OD radius
      ``A/2`` (directly under the tube wall). When the depth reaches half the
      width it is a clean semicircle; deeper grooves get straight sides and a
      rounded bottom, shallower ones a single circular segment.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .ferrule_data import FerruleSize

Point = Tuple[float, float]
Segment = Dict[str, object]  # {"type": "line", "p": P, "q": P}
                              # {"type": "arc", "start": P, "mid": P, "end": P}


@dataclass
class ProfileParams:
    """Override-able dimensions for features the standard leaves open (mm).

    The hub geometry is fully defined by the published flange angle ``C`` on the
    size, so it is not a tunable parameter here.
    """

    weld_chamfer: float = 0.5      # 45-deg outer weld-prep chamfer leg
    bore_chamfer: float = 0.5      # 45-deg inner (bore) weld-prep chamfer leg
    hub_fillet: float = 0.8        # R1 hub fillet radius at the flange/tube corner
    flange_fillet: float = 0.5     # R2 radius on the flange-face outer corner
    groove_depth: float = 0.75     # 0 disables the gasket groove
    groove_width: float = 1.6      # radial width of the gasket groove


@dataclass
class ProfileResult:
    points: List[Point]
    segments: List[Segment]
    size: FerruleSize
    params: ProfileParams

    @property
    def overall_length(self) -> float:
        return self.size.lengths.get("medium", max(p[1] for p in self.points))


def _line(p: Point, q: Point) -> Segment:
    return {"type": "line", "p": p, "q": q}


def _arc(start: Point, mid: Point, end: Point) -> Segment:
    return {"type": "arc", "start": start, "mid": mid, "end": end}


def _tangent_fillet(corner: Point, dir1: Point, dir2: Point, r: float):
    """Return (t1, mid, t2) for an arc of radius ``r`` tangent to two legs.

    ``corner`` is the sharp vertex; ``dir1``/``dir2`` are unit vectors pointing
    from the corner along each leg. ``t1``/``t2`` are the tangent points and
    ``mid`` is the arc point nearest the corner.
    """
    d1x, d1y = dir1
    d2x, d2y = dir2
    dot = max(-1.0, min(1.0, d1x * d2x + d1y * d2y))
    theta = math.acos(dot)                 # angle between the legs
    if theta <= 1e-6 or math.pi - theta <= 1e-6:
        return corner, corner, corner      # degenerate: no fillet
    tan_len = r / math.tan(theta / 2.0)
    t1 = (corner[0] + d1x * tan_len, corner[1] + d1y * tan_len)
    t2 = (corner[0] + d2x * tan_len, corner[1] + d2y * tan_len)
    bx, by = d1x + d2x, d1y + d2y          # bisector (points into the corner)
    blen = math.hypot(bx, by)
    bx, by = bx / blen, by / blen
    center_dist = r / math.sin(theta / 2.0)
    cx, cy = corner[0] + bx * center_dist, corner[1] + by * center_dist
    mid = (cx - bx * r, cy - by * r)        # arc point nearest the corner
    return t1, mid, t2


def build_profile(size: FerruleSize, length_variant: str = "medium",
                  params: ProfileParams = None) -> ProfileResult:
    """Build the closed revolved profile for ``size`` at the given length variant."""
    params = params or ProfileParams()
    L = size.lengths.get(length_variant, size.lengths.get("medium"))

    r_bore = size.b / 2.0
    r_flange = size.d / 2.0
    r_tube = size.a / 2.0
    o_ch = params.weld_chamfer
    i_ch = params.bore_chamfer

    segs: List[Segment] = []

    # --- Face (y = 0), from bore outward, with optional rounded groove. ---
    face_start = (r_bore, 0.0)
    cur = face_start
    if params.groove_depth > 0.0:
        # Per DT-5-2 the gasket groove is centered on the published groove
        # diameter F (an annulus on the flange face, outboard of the tube OD).
        g_center = size.f / 2.0
        half = params.groove_width / 2.0
        g_in = g_center - half
        g_out = g_center + half
        if g_in > r_bore and g_out < r_flange:
            segs.append(_line(cur, (g_in, 0.0)))
            floor_y = params.groove_depth - half
            if floor_y > 1e-6:
                # Deeper than a semicircle: straight sides down to the floor,
                # then a rounded (semicircular) bottom of radius ``half``.
                segs.append(_line((g_in, 0.0), (g_in, floor_y)))
                segs.append(_arc((g_in, floor_y), (g_center, params.groove_depth),
                                 (g_out, floor_y)))
                segs.append(_line((g_out, floor_y), (g_out, 0.0)))
            else:
                # Semicircle (depth == half) or shallower: a single circular
                # arc dipping from the face to depth and back out.
                segs.append(_arc((g_in, 0.0), (g_center, params.groove_depth),
                                 (g_out, 0.0)))
            cur = (g_out, 0.0)
    segs.append(_line(cur, (r_flange, 0.0)))

    # --- Flange disc of thickness E, with the face outer corner (R2) rounded. ---
    if params.flange_fillet > 0.0:
        corner = (r_flange, 0.0)
        t_face, t_mid, t_od = _tangent_fillet(corner, (-1.0, 0.0), (0.0, 1.0),
                                             params.flange_fillet)
        if t_face != t_mid != t_od:
            segs[-1] = _line(cur, t_face)          # face stops at the tangent
            segs.append(_arc(t_face, t_mid, t_od))
            od_bottom = t_od
        else:
            od_bottom = corner
    else:
        od_bottom = (r_flange, 0.0)
    segs.append(_line(od_bottom, (r_flange, size.e)))

    # --- Short conical hub ramp, rounded into the tube by the R1 fillet. ---
    hub_run = (r_flange - r_tube) * math.tan(math.radians(size.flange_angle))
    hub_end = size.e + hub_run
    corner = (r_tube, hub_end)
    ramp_dir = (r_flange - r_tube, size.e - hub_end)
    rl = math.hypot(*ramp_dir)
    ramp_dir = (ramp_dir[0] / rl, ramp_dir[1] / rl)
    tube_dir = (0.0, 1.0)
    if params.hub_fillet > 0.0:
        t_ramp, t_mid, t_tube = _tangent_fillet(corner, ramp_dir, tube_dir,
                                                params.hub_fillet)
        if t_ramp != t_mid != t_tube:
            segs.append(_line((r_flange, size.e), t_ramp))
            segs.append(_arc(t_ramp, t_mid, t_tube))
            tube_bottom = t_tube
        else:
            segs.append(_line((r_flange, size.e), corner))
            tube_bottom = corner
    else:
        segs.append(_line((r_flange, size.e), corner))
        tube_bottom = corner

    # --- Straight thin-walled tube to the weld end. ---
    segs.append(_line(tube_bottom, (r_tube, L - o_ch)))

    # --- Weld end: 45-deg chamfer on the OUTER corner. ---
    segs.append(_line((r_tube, L - o_ch), (r_tube - o_ch, L)))

    # --- Flat weld land across the top to the bore chamfer. ---
    segs.append(_line((r_tube - o_ch, L), (r_bore + i_ch, L)))

    # --- Weld end: 45-deg chamfer on the INNER (bore) corner. ---
    segs.append(_line((r_bore + i_ch, L), (r_bore, L - i_ch)))

    # --- Constant bore straight back to the face (bore == tube ID). ---
    segs.append(_line((r_bore, L - i_ch), face_start))

    # Flatten to an ordered point list (endpoints + arc mid-points).
    pts: List[Point] = []
    for s in segs:
        if s["type"] == "line":
            pts.append(s["p"])
        else:
            pts.append(s["start"])
            pts.append(s["mid"])
    pts.append(segs[-1]["q"] if segs[-1]["type"] == "line" else segs[-1]["end"])

    return ProfileResult(points=pts, segments=segs, size=size, params=params)


def validate_profile(result: ProfileResult) -> List[str]:
    """Return a list of human-readable geometry problems (empty == valid)."""
    errors: List[str] = []
    s = result.size
    p = result.params

    if s.b >= s.a:
        errors.append("Bore B must be smaller than tube OD A.")
    if s.f >= s.d:
        errors.append("Gasket diameter F must be smaller than flange OD D.")
    if s.f <= s.b:
        errors.append("Gasket diameter F must be larger than bore B.")
    if s.wall <= 0 or s.wall * 2 >= s.a:
        errors.append("Weld wall thickness must be positive and less than A/2.")
    if s.d <= s.a:
        errors.append("Flange OD D must be larger than tube OD A for a hub.")
    L = s.lengths.get("medium")
    if L is not None:
        hub_run = (s.d / 2 - s.a / 2) * math.tan(math.radians(s.flange_angle))
        if L <= s.e + hub_run + p.weld_chamfer:
            errors.append("Overall length L is too short for the flange + hub.")
    if p.weld_chamfer >= (s.a / 2 - s.b / 2):
        errors.append("Weld chamfer is larger than the available wall at the weld end.")
    if p.bore_chamfer + p.weld_chamfer >= s.a - s.b:
        errors.append("Weld-end chamfers together exceed the wall thickness.")

    # all radii must be strictly positive (loop must not touch the axis)
    for i, (x, y) in enumerate(result.points):
        if x <= 0:
            errors.append(f"Profile point {i} has non-positive radius {x}.")
            break
    return errors
