import adsk.core
import adsk.fusion
import os
import traceback
from ...lib import fusionAddInUtils as futil
from ...lib.ferrule_data import (
    SIZES, size_labels, find_size, standard_titles, standard_keys,
)
from ...lib.ferrule_geometry import ProfileParams, build_profile, validate_profile
from ...lib.ferrule_modeler import create_ferrule, _delete_preview
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
CMD_NAME = 'ASME BPE Ferrule'
CMD_Description = 'Generate an ASME BPE-2016 hygienic clamp ferrule (revolved profile).'

IS_PROMOTED = True

# Promote the button into the Solid workspace "Create" panel, placed right after
# the Pipe command (real id: PrimitivePipe).
WORKSPACE_ID = 'FusionSolidEnvironment'
TAB_ID = 'SolidTab'
PANEL_ID = 'SolidCreatePanel'
COMMAND_BESIDE_ID = 'PrimitivePipe'

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

local_handlers = []

# ---- Command input IDs -------------------------------------------------
IN_STANDARD = 'ferrule_standard'
IN_SIZE = 'ferrule_size'
IN_LENGTH = 'ferrule_length'
IN_WELD_CHAMFER = 'weld_chamfer'
IN_GROOVE_DEPTH = 'groove_depth'
IN_GROOVE_WIDTH = 'groove_width'
IN_INFO = 'ferrule_info'

LENGTH_VARIANTS = ('short', 'medium', 'long')

# Tracks whether a preview feature is currently sitting in the model so we can
# remove it if the user cancels the dialog.
_preview_active = False

# Once the user edits the gasket groove depth by hand we stop overwriting it with
# the standard's G value when the size changes. Reset each time the dialog opens.
_groove_edited = False


def _get_create_panel():
    """Return the Solid 'Create' toolbar panel (it lives under the tab)."""
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    tab = workspace.toolbarTabs.itemById(TAB_ID)
    return tab.toolbarPanels.itemById(PANEL_ID)


# Executed when add-in is run.
def start():
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)

    panel = _get_create_panel()
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    panel = _get_create_panel()
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()


def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')
    inputs = args.command.commandInputs

    # Standard dropdown (which ASME BPE dimensional table to use).
    std_dd: adsk.core.DropDownCommandInput = inputs.addDropDownCommandInput(
        IN_STANDARD, 'Standard', adsk.core.DropDownStyles.TextListDropDownStyle)
    for i, title in enumerate(standard_titles()):
        std_dd.listItems.add(title, i == 0, standard_keys()[i])

    # Size dropdown (label per size/type), populated for the active standard.
    size_dd: adsk.core.DropDownCommandInput = inputs.addDropDownCommandInput(
        IN_SIZE, 'Nominal Size', adsk.core.DropDownStyles.TextListDropDownStyle)
    _populate_sizes(inputs)

    # Length variant dropdown.
    len_dd: adsk.core.DropDownCommandInput = inputs.addDropDownCommandInput(
        IN_LENGTH, 'Length (L)', adsk.core.DropDownStyles.TextListDropDownStyle)
    for i, name in enumerate(LENGTH_VARIANTS):
        len_dd.listItems.add(name.capitalize(), name == 'medium', name)

    # Profile parameters (features the standard leaves open).
    _add_len(inputs, IN_WELD_CHAMFER, 'Weld chamfer', 0.5)
    _add_len(inputs, IN_GROOVE_DEPTH, 'Gasket groove depth', 0.75)
    _add_len(inputs, IN_GROOVE_WIDTH, 'Gasket groove width', 1.6)

    # Read-only info box showing the resolved standard dimensions.
    inputs.addTextBoxCommandInput(IN_INFO, 'Table DT-5-2', '', 3, True)

    global _groove_edited
    _groove_edited = False
    _sync_groove_depth(inputs)

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

    _refresh_info(inputs)


def _sync_groove_depth(inputs):
    """Set the groove-depth field to the selected size's standard G (mm).

    Skipped once the user has edited the field by hand so their value sticks.
    """
    if _groove_edited:
        return
    size = _selected_size(inputs)
    vi: adsk.core.ValueCommandInput = inputs.itemById(IN_GROOVE_DEPTH)
    vi.value = size.g * 0.1  # mm -> cm (internal)


def _add_len(inputs, id_, name, default_mm):
    vi = inputs.addValueInput(id_, name, 'mm', adsk.core.ValueInput.createByReal(default_mm * 0.1))
    vi.minimum = 0
    return vi


def _selected_index(dd: adsk.core.DropDownCommandInput) -> int:
    items = dd.listItems
    for i in range(items.count):
        if items.item(i).isSelected:
            return i
    return 0


def _selected_standard(inputs) -> str:
    dd: adsk.core.DropDownCommandInput = inputs.itemById(IN_STANDARD)
    keys = standard_keys()
    return keys[_selected_index(dd)]


def _populate_sizes(inputs, keep_index: int = 0):
    """Rebuild the Nominal Size dropdown for the currently selected standard."""
    dd: adsk.core.DropDownCommandInput = inputs.itemById(IN_SIZE)
    dd.listItems.clear()
    labels = size_labels(_selected_standard(inputs))
    for i, label in enumerate(labels):
        dd.listItems.add(label, i == keep_index, label)


def _selected_size(inputs):
    dd: adsk.core.DropDownCommandInput = inputs.itemById(IN_SIZE)
    name = dd.listItems.item(_selected_index(dd)).name
    return find_size(name, _selected_standard(inputs))


def _selected_length(inputs) -> str:
    dd: adsk.core.DropDownCommandInput = inputs.itemById(IN_LENGTH)
    return LENGTH_VARIANTS[_selected_index(dd)]


def _params(inputs) -> ProfileParams:
    def mm(id_):
        vi: adsk.core.ValueCommandInput = inputs.itemById(id_)
        return vi.value * 10.0  # cm -> mm
    return ProfileParams(
        weld_chamfer=mm(IN_WELD_CHAMFER),
        groove_depth=mm(IN_GROOVE_DEPTH),
        groove_width=mm(IN_GROOVE_WIDTH),
    )


def _build(inputs):
    size = _selected_size(inputs)
    length = _selected_length(inputs)
    params = _params(inputs)
    return size, length, params, build_profile(size, length, params)


def _refresh_info(inputs):
    size, length, params, profile = _build(inputs)
    info: adsk.core.TextBoxCommandInput = inputs.itemById(IN_INFO)
    L = size.lengths.get(length)
    dn = f'  DN={size.dn}' if size.dn else ''
    info.text = (
        f'<b>Table {_selected_standard(inputs)}</b><br>'
        f'A(tube OD)={size.a}  B(bore)={size.b}  D(flange OD)={size.d}<br>'
        f'E(flange thk)={size.e}  F(gasket dia)={size.f}  L({length})={L}<br>'
        f'wall={size.wall}  C(angle)={size.flange_angle}{dn}'
    )


def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    global _preview_active
    inputs = args.command.commandInputs
    try:
        size, length, params, _ = _build(inputs)
        # Commit: replaces the transient preview component with a permanent one.
        create_ferrule(size, length, params, preview=False)
        _preview_active = False
    except Exception:
        futil.handle_error(CMD_NAME, show_message_box=True)
        raise


def command_preview(args: adsk.core.CommandEventArgs):
    """Rebuild the ferrule feature in place so the user sees a live preview.

    ``create_ferrule`` deletes the previous generator feature before adding the
    new one, so repeated previews never stack bodies. The preview is real
    geometry; ``command_destroy`` removes it if the user cancels.
    """
    global _preview_active
    inputs = args.command.commandInputs
    try:
        size, length, params, _ = _build(inputs)
        create_ferrule(size, length, params, preview=True)
        _preview_active = True
        app.activeViewport.fit()
    except Exception:
        futil.log(f'{CMD_NAME} preview skipped: {traceback.format_exc()}')


def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed = args.input
    inputs = args.inputs
    if changed.id == IN_STANDARD:
        _populate_sizes(inputs)
        _sync_groove_depth(inputs)
        _refresh_info(inputs)
    elif changed.id == IN_SIZE:
        _sync_groove_depth(inputs)
        _refresh_info(inputs)
    elif changed.id == IN_GROOVE_DEPTH:
        global _groove_edited
        _groove_edited = True
    elif changed.id == IN_LENGTH:
        _refresh_info(inputs)


def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    inputs = args.inputs
    try:
        size, length, params, profile = _build(inputs)
        errors = validate_profile(profile)
        args.areInputsValid = len(errors) == 0
    except Exception:
        args.areInputsValid = False


def command_destroy(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Destroy Event')
    global local_handlers, _preview_active
    # If the user cancelled (preview still active, execute never ran), remove the
    # dangling preview feature so the model is left as it was.
    if _preview_active:
        try:
            design = adsk.fusion.Design.cast(app.activeProduct)
            _delete_preview(design.rootComponent)
        except Exception:
            futil.log(f'{CMD_NAME} preview cleanup skipped: {traceback.format_exc()}')
        _preview_active = False
    local_handlers = []
