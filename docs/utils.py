import inspect
import shutil
from pathlib import Path
from collections import OrderedDict
from psychopy.experiment import Experiment


def titleize(name):
    """
    Convert a class name in PascalCase to Capital Case
    """
    # Get indices of capital letters
    capitalIndices = [i for i, c in enumerate(name) if c.isupper()]
    # Don't add space at the start
    if name[0].isupper():
        del capitalIndices[0]
    # Convert string to list
    name = list(name)
    # Add spaces at each index
    for offset, i in enumerate(capitalIndices):
        name.insert(i + offset, " ")
    # Turn back into a string
    name = "".join(name)

    return name


def createModuleDocs(module):
    # Start off with a blank string to append content to
    content = ""
    # Go through everything in the module namespace
    for modname in dir(module):
        # Skip private / protected attributes
        if modname.startswith("_"):
            continue
        # Get object
        obj = getattr(module, modname)

        # --- Class ---
        if inspect.isclass(obj):
            cls = obj
            # Write class rst
            content += (
                ":class:`%(name)s`\n"
                "============================================================\n"
                "\n"
                "Attributes\n"
                "------------------------------------------------------------\n"
                "\n"
                ".. currentmodule:: %(module)s\n"
                "\n"
                ".. autosummary::\n"
                "\n"
                "   %(name)s\n"
                "\n"
                "Details\n"
                "------------------------------------------------------------\n"
                "\n"
                ".. autoclass:: %(name)s\n"
                "   :members:\n"
                "   :undoc-members:\n"
                "   :inherited-members:\n"
                "\n"
            ) % {'module': module.__name__,'name': cls.__name__}
        
        # --- Function ---
    
    return content


def createComponentDocs(cls, params=None):
    """
    Given a component class, auto-generate documentation from its Param objects. This should be more of a
    starting point than a final product - there will doubtless be aspects you want to edit after creation.

    Parameters
    ----------
    cls : class
        The Component class (used by Builder to write code, as in `psychopy.experiment.components`)
    params : dict
        Dict of parameter names / values to create the example component with. `exp`, `parentName` and `name` are
        supplied automatically, so if the component can be initialised with no other inputs then you
        can leave this blank.
    """
    # If no params given, make it a blank dict
    if params is None:
        params = {}
    # Create dummy experiment
    exp = Experiment()
    # Create component with whatever params are given
    comp = cls(exp, parentName="noRoutine", name=cls.__name__, **params)
    # Start off with a blank string to append content to
    content = ""
    # Find icon
    cls.icon = Path(cls.iconFile)
    icon = cls.icon.parent / "light" / (cls.icon.stem + "@2x" + cls.icon.suffix)
    # # Move icon to images folder
    # src = Path(__file__).parent
    # dest = src / "_static" / icon.name
    # shutil.copy(str(icon), str(dest))
    

    # Create title
    content += (
        ".. rst-class:: component-bio\n"
        "%s\n"
        "============================================================\n"
    ) % titleize(cls.__name__)
    # Create description
    content += (
        "%s\n"
    ) % cls.__doc__
    # Create contents page
    content += (
        ".. toctree::\n"
        "  :maxdepth: 2\n"
        "\n"
    )
    # Sort params by category
    sortedParams = OrderedDict()
    for name, param in comp.params.items():
        if param.categ not in sortedParams:
            sortedParams[param.categ] = OrderedDict()
        sortedParams[param.categ][name] = param
    # Move high priority categs to the front
    for categ in reversed(['Basic', 'Layout', 'Appearance', 'Formatting', 'Texture']):
        if categ in sortedParams:
            sortedParams.move_to_end(categ, last=False)
    # Move low priority categs to the end
    for categ in ['Data', 'Custom', 'Hardware', 'Testing']:
        if categ in sortedParams:
            sortedParams.move_to_end(categ, last=True)
    # Order params
    for categ in sortedParams:
        for name in reversed(comp.order):
            if name in sortedParams[categ]:
                sortedParams[categ].move_to_end(name, last=False)
    # Create entry for each category
    for categ, params in sortedParams.items():
        if categ != "Basic":
            # Create category heading
            content += (
                "%s\n"
                "------------------------------------------------------------\n"
            ) % categ
        # Create entry for each param in category
        for param in params.values():
            content += (
                "%(label)s : %(valType)s\n"
                "    %(hint)s\n"
                "\n"
            ) % param.__dict__

    return content