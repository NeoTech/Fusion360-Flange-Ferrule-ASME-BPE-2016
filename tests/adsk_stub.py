"""A minimal in-memory stub of the ``adsk.core`` / ``adsk.fusion`` API surface
used by :mod:`lib.ferrule_modeler`.

It records every call so tests can assert that the correct sketch geometry and
revolve feature are produced, without a running Fusion instance.

Install it before importing the modeler::

    import adsk_stub
    adsk_stub.install()
"""

import sys
import types


# --------------------------------------------------------------------------- #
# Recording primitives
# --------------------------------------------------------------------------- #
class Recorder:
    def __init__(self):
        self.calls = []

    def record(self, name, **kwargs):
        self.calls.append((name, kwargs))

    def names(self):
        return [c[0] for c in self.calls]


_REC = Recorder()


def recorder():
    return _REC


def reset():
    _REC.calls = []
    reset_design()


class Point3D:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    @staticmethod
    def create(x, y, z=0):
        _REC.record('Point3D.create', x=x, y=y, z=z)
        return Point3D(x, y, z)

    def __repr__(self):
        return f'Point3D({self.x}, {self.y}, {self.z})'


class ValueInput:
    def __init__(self, real):
        self.real = real

    @staticmethod
    def createByReal(real):
        _REC.record('ValueInput.createByReal', real=real)
        return ValueInput(real)


class SketchLine:
    def __init__(self, p1, p2):
        self._p1, self._p2 = p1, p2
        self.isConstruction = False
        self.isCenterLine = False
        self.geometry = object()


class SketchLines:
    def addByTwoPoints(self, p1, p2):
        _REC.record('sketchLines.addByTwoPoints', p1=(p1.x, p1.y), p2=(p2.x, p2.y))
        return SketchLine(p1, p2)


class SketchCurves:
    def __init__(self):
        self.sketchLines = SketchLines()


class Profile:
    pass


class Profiles:
    def __init__(self, count):
        self.count = count

    def item(self, i):
        return Profile()


class Sketch:
    def __init__(self, plane, profile_count=1):
        self.plane = plane
        self.sketchCurves = SketchCurves()
        self._profiles = Profiles(profile_count)

    @property
    def profiles(self):
        return self._profiles


class Sketches:
    def __init__(self, root):
        self._root = root

    def add(self, plane):
        _REC.record('sketches.add', plane=plane.name)
        sk = Sketch(plane, profile_count=self._root.profile_count)
        self._root.sketch = sk
        return sk


class RevolveFeatureInput:
    def __init__(self, profile, axis, solid):
        self.profile = profile
        self.axis = axis
        self.solid = solid
        self.angle = None

    def setAngleExtent(self, symmetric, angle):
        # Real API takes a ValueInput; unwrap so tests can assert the float.
        raw = angle.real if isinstance(angle, ValueInput) else angle
        self.angle = raw
        _REC.record('revolve.setAngleExtent', symmetric=symmetric, angle=raw)


class RevolveFeature:
    def __init__(self, rfi, root):
        self._rfi = rfi
        self.name = ''
        self._root = root

    def deleteMe(self):
        _REC.record('revolve.deleteMe', name=self.name)
        self._root.features._remove(self)


class RevolveFeatures:
    def __init__(self, root):
        self._root = root

    def createInput(self, profile, axis, solid):
        _REC.record('revolve.createInput', solid=solid)
        return RevolveFeatureInput(profile, axis, solid)

    def add(self, rfi):
        _REC.record('revolve.add')
        feat = RevolveFeature(rfi, self._root)
        self._root.features._add(feat)
        return feat


class FeatureList:
    def __init__(self):
        self._items = []

    def _add(self, feat):
        self._items.append(feat)

    def _remove(self, feat):
        if feat in self._items:
            self._items.remove(feat)

    @property
    def count(self):
        return len(self._items)

    def item(self, i):
        return self._items[i]


class Features:
    def __init__(self, root):
        self._root = root
        self.revolveFeatures = RevolveFeatures(root)
        self._list = FeatureList()

    @property
    def count(self):
        return self._list.count

    def item(self, i):
        return self._list.item(i)


class Plane:
    def __init__(self, name):
        self.name = name


class Component:
    def __init__(self, profile_count=1):
        # Real API exposes origin planes directly on Component (note capital Z).
        self.yZConstructionPlane = Plane('yz')
        self.xZConstructionPlane = Plane('xz')
        self.xyConstructionPlane = Plane('xy')
        self.features = Features(self)
        self.sketches = Sketches(self)
        self.profile_count = profile_count
        self.sketch = None


class Product:
    pass


# A single cached design so repeated create_ferrule calls in one test share the
# same root component (matching how a real open document behaves).
_DESIGN = None


class Design:
    @staticmethod
    def cast(product):
        global _DESIGN
        if product is None:
            return None
        if _DESIGN is None:
            _DESIGN = Design()
            _DESIGN.rootComponent = Component()
        return _DESIGN


def reset_design():
    """Discard the cached design so the next cast builds a fresh component."""
    global _DESIGN
    _DESIGN = None


class Application:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = Application()
        return cls._instance

    def __init__(self):
        self.activeProduct = Product()
        self.userInterface = UserInterface()
        self.activeView = _View()


class _View:
    def fit(self):
        _REC.record('view.fit')


class UserInterface:
    def messageBox(self, msg):
        _REC.record('ui.messageBox', msg=msg)


# --------------------------------------------------------------------------- #
# Module installation
# --------------------------------------------------------------------------- #
def install():
    """Register this stub as the ``adsk``, ``adsk.core`` and ``adsk.fusion``
    packages in ``sys.modules``."""
    core = types.ModuleType('adsk.core')
    fusion = types.ModuleType('adsk.fusion')

    core.Point3D = Point3D
    core.ValueInput = ValueInput
    core.Application = Application
    core.UserInterface = UserInterface

    fusion.Design = Design
    fusion.Component = Component
    fusion.Sketch = Sketch
    fusion.RevolveFeature = RevolveFeature

    adsk = types.ModuleType('adsk')
    adsk.core = core
    adsk.fusion = fusion

    sys.modules['adsk'] = adsk
    sys.modules['adsk.core'] = core
    sys.modules['adsk.fusion'] = fusion
    return adsk
