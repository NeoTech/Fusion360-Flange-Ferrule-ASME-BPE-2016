# Copilot Instructions — Flange-Ferrule Add-in

## What this project is
A Fusion 360 Python add-in that generates **ASME BPE-2016 hygienic clamp ferrules**
(the tube-end connector used in brewery / bioprocessing / sanitary piping). The solid
is built by sketching a **2D revolved profile** (an axial half-section) and revolving
it 360° about the ferrule centerline.

> Important standard note: ASME BPE ferrules are *clamp* ferrules (two ferrules + a
> gasket + an external clamp), **not** bolted raised-face pipe flanges. The controlling
> reference is **Table DT-7-1** (Hygienic Clamp Ferrule dimensions & tolerances). The
> six published dimensions (A, B, D, E, F, L) do **not** fully define the revolved
> profile — gasket-groove depth/width, hub length, and weld-end chamfer are
> interpretation. Encode a defensible default and expose those as parameters.

## Dimension vocabulary (Table DT-7-1)
| Symbol | Meaning |
| --- | --- |
| `A` | Tube outside diameter (nominal size basis) |
| `B` | Bore diameter measured at the ferrule face |
| `D` | Flange outside diameter |
| `E` | Flange thickness (reference) |
| `F` | Gasket-groove / gasket-contact diameter |
| `L` | Overall ferrule length (short / medium / long variants) |
| wall | Tube weld-end wall thickness |

Sizes come in **Type A** and **Type B** families (e.g. 1 in: Type A `D=34.0`,
Type B `D=50.39`). Smaller sizes share `D=25.0`.

## Architecture / where things live
- `config.py` — global IDs, `COMPANY_NAME`, `ADDIN_NAME`, `DEBUG`.
- `Flange-Ferrule.py` — entry point (`run`/`stop`); do not restructure.
- `commands/__init__.py` — registers command modules; add new commands here.
- `commands/commandDialog/entry.py` — the ferrule generator dialog (main work).
- `lib/fusionAddInUtils/` — Autodesk boilerplate (`futil.log`, `futil.add_handler`,
  `futil.handle_error`). Reuse, don't reinvent.
- `lib/ferrule_data.py` — **(planned)** dimension table + size/type lookup.
- `lib/ferrule_geometry.py` — **(planned)** pure function that turns dimensions +
  parameters into an ordered profile vertex/segment list (no Fusion calls → unit-testable).

Keep geometry math **separate** from Fusion API calls. The geometry module returns
coordinates; the command module draws the sketch and revolves.

## Fusion API conventions (verified)
- Revolve:
  ```python
  rev = features.revolveFeatures
  rfi = rev.createInput(profiles, axis_line, False)   # False = solid
  rfi.setAngleExtent(False, math.pi * 2)
  rev.add(rfi)
  ```
  `profiles` is a `ProfileCollection`; `axis_line` is the sketch centerline
  (`SketchLine` with `geometry.centerline = True`) or the origin Y-axis.
- Sketch lines: `sketch.sketchCurves.sketchLines.addByTwoPoints(Point3D, Point3D)`.
  Arcs/fillets: `sketch.sketchCurves.addArc(...)` / `addArcByTangentPoint`.
- The closed profile is auto-computed: read `sketch.profiles.item(0)` after the loop closes.
- Build the sketch on a datum/origin plane whose **Y axis is the centerline**; place
  profile points at `(radius, axial_position)` in sketch space.

## Units gotcha (critical)
- A linear `ValueCommandInput.value` is in **cm** (Fusion internal). Multiply by **10**
  to get mm. Dimensionless inputs use unit string `""` so `.value` is the raw number.
- When creating sketch geometry, pass `Point3D` in **cm** (model/internal units), or use
  `ValueInput`/expressions. Be explicit about mm↔cm at the boundary.

## Command lifecycle gotcha
- `adsk.core.Command` has **no `preExecute`** event. Valid events: `execute`,
  `inputChanged`, `commandExecuting`, `select`, `destroy`, `executePreview`,
  `validateInputs`.
- There is **no "dialog about to open"** event. Populate dropdowns in `CommandCreated`
  and rebuild dependent state in `inputChanged`.
- `CommandCreated` fires once per command-definition lifetime; to refresh preset/dropdown
  data, reload the add-in (delete + recreate the command definition) or restart Fusion.

## Coding style
- Python 3, Fusion `adsk` API. Type-hint handler `args` with the `adsk.core.*EventArgs`
  types as the existing `entry.py` files do.
- Guard every command/UI element lookup with `itemById(...) is None` before use.
- Use `futil.add_handler(..., local_handlers=local_handlers)` so handlers are not GC'd.
- Clear `local_handlers` in `command_destroy`.
- Wrap top-level command bodies in `try/except` calling `futil.handle_error(name, True)`.
- Keep TODO/template cruft out of finished code; remove unused sample palette commands
  (`paletteShow`, `paletteSend`) if they are not part of the final feature.

## Testing
- Use the Fusion MCP service to probe the API and to run/exercise the generator against
  a live document. After a code change, reload the add-in and verify the revolved solid
  matches the expected profile (screenshot + dimension readback).
