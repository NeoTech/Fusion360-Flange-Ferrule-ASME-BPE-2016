# Ferrule Comparative Design Specification

Source of truth: **ASME BPE-2009, Table DT-5-2 — Hygienic Clamp Ferrule Standard
Dimensions and Tolerances** (provided as a screenshot; values in inches).
The add-in's `lib/ferrule_data.py` cites the equivalent BPE-2016 table (DT-7-1);
the published dimensional content is the same across these editions, so the two
are directly comparable.

This document (1) transcribes the standard, (2) converts it to the millimetre
units the modeler uses, and (3) compares it against the values currently encoded
in `ferrule_data.py`, flagging every discrepancy that needs correcting.

---

## 1. Standard dimensions (DT-5-2, inches)

Dimension vocabulary (see the figure in the table):

| Sym | Meaning |
|-----|---------|
| A | Tube diameter (weld-end bore side basis) |
| B | I.D. bore at the ferrule face |
| C | Flange angle (deg) |
| D | Flange diameter (OD) |
| E | Flange thickness (reference) |
| F | Groove diameter (gasket contact) |
| R1, R2, R3, R4, A1, G, H | Groove-detail radii / callouts (profile interpretation) |

| Nominal | Type | A ±.005 | B ±.005 | C ± | D +/− | E ±.005 (ref) | F ±.005 |
|---------|------|---------|---------|-----|-------|---------------|---------|
| 1/4 in  | A | 0.250 | 0.180 | 20 ±0.5 | 0.984 +.005/−.005 | 0.143 | 0.800 |
| 3/8 in  | A | 0.375 | 0.305 | 20 ±0.5 | 0.984 | 0.143 | 0.800 |
| 1/2 in  | A | 0.500 | 0.370 | 20 ±0.5 | 0.984 | 0.143 | 0.800 |
| 3/4 in  | A | 0.750 | 0.620 | 20 ±0.5 | 0.984 | 0.143 | 0.800 |
| 1 in    | A | 1.000 | 0.870 | 20 ±1.0 | 1.339 | 0.143 | 0.800 |
| 1 in    | B | 1.000 | 0.870 | 20 ±1.0 | 1.984 +.008/−.005 | 0.112 | 1.718 |
| 1-1/2 in| B | 1.500 | 1.370 | 20 ±1.0 | 1.984 | 0.112 | 1.718 |
| 2 in    | B | 2.000 | 1.870 | 20 ±1.0 | 2.516 | 0.112 | 2.218 |
| 2-1/2 in| B | 2.500 | 2.370 | 20 ±1.0 | 3.047 | 0.112 | 2.781 |
| 3 in    | B | 3.000 | 2.870 | 20 ±1.0 | 3.579 | 0.112 | 3.281 |
| 4 in    | B | 4.000 | 3.834 | 20 ±1.0 | 4.682 +.015/−.030 | 0.112 | 4.344 |
| 6 in    | B | 6.000 | 5.782 | 20 ±1.0 | 6.570 +.030/−.030 | 0.220 | 6.176 |

> Note: DT-5-2 does **not** publish overall length **L** or the weld-end wall
> thickness; those come from a separate length table / manufacturer catalog and
> are carried in `ferrule_data.py` as `DEFAULT_LENGTHS_MM` and `wall`.

---

## 2. Converted to millimetres (×25.4) — modeler units

| Nominal | Type | A | B | D | E | F |
|---------|------|------|-------|--------|-------|--------|
| 1/4 in  | A | 6.35 | 4.57 | 24.99 | 3.63 | 20.32 |
| 3/8 in  | A | 9.53 | 7.75 | 24.99 | 3.63 | 20.32 |
| 1/2 in  | A | 12.70 | 9.40 | 24.99 | 3.63 | 20.32 |
| 3/4 in  | A | 19.05 | 15.75 | 24.99 | 3.63 | 20.32 |
| 1 in    | A | 25.40 | 22.10 | 34.01 | 3.63 | 20.32 |
| 1 in    | B | 25.40 | 22.10 | 50.39 | 2.84 | 43.64 |
| 1-1/2 in| B | 38.10 | 34.80 | 50.39 | 2.84 | 43.64 |
| 2 in    | B | 50.80 | 47.50 | 63.91 | 2.84 | 56.34 |
| 2-1/2 in| B | 63.50 | 60.20 | 77.39 | 2.84 | 70.64 |
| 3 in    | B | 76.20 | 72.90 | 90.91 | 2.84 | 83.34 |
| 4 in    | B | 101.60 | 97.38 | 118.92 | 2.84 | 110.34 |
| 6 in    | B | 152.40 | 146.86 | 166.88 | 5.59 | 156.87 |

---

## 3. Comparison: `ferrule_data.py` (current) vs DT-5-2

Legend: ✅ matches · ⚠️ minor (rounding / reference dim) · ❌ wrong — needs fix.

| Nominal | Type | Field | Current (mm) | DT-5-2 (mm) | Status |
|---------|------|-------|--------------|-------------|--------|
| 1/4–3/4 | A | A,B,D,E,F | as table | as table | ✅ |
| 1 in | A | e | 2.84 | 3.63 | ❌ flange thickness wrong (should be 0.143″) |
| 1 in | A | d | 34.00 | 34.01 | ✅ |
| 1 in | B | all | — | — | ✅ |
| 1-1/2 | B | all | — | — | ✅ |
| 2 in | B | d | 50.39 | **63.91** | ❌ reused 1½″ flange family |
| 2 in | B | f | 43.64 | **56.34** | ❌ reused 1½″ groove dia |
| 2 in | B | e | 2.84 | 2.84 | ✅ |
| 2-1/2 | B | f | 69.00 | 70.64 | ⚠️ ~1.6 mm low |
| 2-1/2 | B | e | 3.38 | 2.84 | ❌ |
| 3 in | B | d | 77.39 | **90.91** | ❌ reused 2½″ flange family |
| 3 in | B | f | 69.00 | **83.34** | ❌ |
| 3 in | B | e | 3.38 | 2.84 | ❌ |
| 4 in | B | d | 116.00 | 118.92 | ⚠️ ~3 mm low |
| 4 in | B | f | 106.00 | 110.34 | ⚠️ |
| 4 in | B | e | 3.38 | 2.84 | ❌ |
| 6 in | B | — | (absent) | present | ❌ size row missing entirely |

### Summary of required corrections
1. **Add the 6 in Type B row** (A=152.40, B=146.86, D=166.88, E=5.59, F=156.87).
2. **Fix Type B flange OD (D)** for 2″ (63.91), 3″ (90.91), 4″ (118.92) — the
   current table wrongly reuses the next-smaller flange family.
3. **Fix Type B groove diameter (F)** for 2″ (56.34), 3″ (83.34), 4″ (110.34),
   and nudge 2½″ to 70.64.
4. **Fix flange thickness (E)**: Type A rows are 3.63 mm (0.143″); Type B rows
   are 2.84 mm (0.112″) except 6″ which is 5.59 mm (0.220″). The current table
   mixes 2.84/3.38 incorrectly.
5. **1 in Type A `e`** should be 3.63 mm, not 2.84.

---

## 4. Profile interpretation (not fully pinned by DT-5-2)

The six published dimensions (A, B, C, D, E, F) do **not** alone define the
revolved cross-section. The groove-detail callouts (R1–R4, A1, G, H) and the
hub/taper geometry are an engineering interpretation exposed as
`ProfileParams` in `lib/ferrule_geometry.py`:

| Param | Default (mm) | Maps to |
|-------|--------------|---------|
| hub_taper_len | 6.0 | hub run from flange face to tube OD |
| weld_land | 3.0 | flat land before the weld-end chamfer |
| weld_chamfer | 1.0 | weld-end lead-in |
| groove_depth | 0.0 (derived) | radial depth of the gasket groove |
| groove_width | 1.6 | axial width of the gasket groove |

The flange angle **C = 20°** from the standard should drive the hub taper; the
current `hub_taper_len` default is a fixed length rather than a 20°-derived
run. Recommend deriving the hub taper from C so the modeled seat angle matches
the standard.

---

## 5. Tolerances carried for downstream drawing callouts

| Dimension | Tolerance (in) | Tolerance (mm) |
|-----------|----------------|----------------|
| A | ±0.005 | ±0.13 |
| B | ±0.005 | ±0.13 |
| C | ±0.5 (≤1A) / ±1.0 (B) | deg |
| D | +0.008 / −0.005 (B) | +0.20 / −0.13 |
| E | ±0.005 (ref) | ±0.13 |
| F | ±0.005 | ±0.13 |

These are nominal-limit tolerances from the table; verify against a licensed
copy of ASME BPE before releasing a manufacturing drawing.

## 6. Implementation status

Both metallic ferrule tables are now selectable in the dialog via the **Standard**
dropdown (`lib/ferrule_data.py` → `STANDARDS`):

- **ASME BPE-2019 DT-7-1** (`DT71_SIZES`) — default; DN-labelled sizes, ¼″–4″.
- **ASME BPE-2009 DT-5-2** (`DT52_SIZES`) — inch-labelled, ¼″–6″, with the
  corrected Type B flange OD / groove diameters and the 6″ row.

Selecting a standard repopulates the Nominal Size list and the info-box title.
The `flange_angle` (C = 20°) is carried per size but the hub taper is still
modelled from `hub_taper_len` rather than derived from C — see §4 follow-up.

Later editions (BPE-2022/2024 **DT-7.1-1**) carry the same metallic dimensional
content as DT-7-1, so they are represented by the DT-7-1 table. Polymeric
ferrules (DT-7.1-2) are a separate profile family and not yet implemented.
