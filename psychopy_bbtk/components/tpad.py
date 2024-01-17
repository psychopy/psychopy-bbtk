from psychopy.experiment import Param, getInitVals
from psychopy.localization import _translate
from psychopy.experiment.plugins import DeviceBackend
from psychopy.experiment.components.buttonBox import ButtonBoxComponent
from psychopy.experiment.routines.photodiodeValidator import PhotodiodeValidatorRoutine


def getTPadPorts():
    """
    Get a list of ports which have TPad devices connected.
    """
    from psychopy_bbtk.tpad import TPad
    ports = [""]
    # iterate through available button boxes
    for profile in TPad.getAvailableDevices():
        # add this box's port
        ports.append(
            profile['port']
        )

    return ports


class TPadPhotodiodeValidatorBackend(DeviceBackend):
    # which component is this backend for?
    component = PhotodiodeValidatorRoutine
    # what value should Builder use for this backend?
    key = "tpad"
    # what label should be displayed by Builder for this backend?
    label = _translate("BBTK TPad")
    # what hardware classes are relevant to this backend?
    deviceClasses = ["psychopy_bbtk.tpad.TPadPhotodiodeGroup"]

    def getParams(self):
        """
        Get parameters from this backend to add to each new instance of ButtonBoxComponent

        Returns
        -------
        dict[str:Param]
            Dict of Param objects, which will be added to any Button Box Component's params, along with a dependency
            to only show them when this backend is selected
        list[str]
            List of param names, defining the order in which params should appear
        """
        # define order
        order = [
            "serialPort",
            "bbtkNButtons"
        ]
        # define params
        params = {}

        params['bbtkSerialPort'] = Param(
            "", valType="str", inputType="choice", categ="Device",
            allowedVals=getTPadPorts,
            label=_translate("COM port"),
            hint=_translate(
                "Serial port to connect to"
            )
        )
        params['bbtkNChannels'] = Param(
            2, valType="code", inputType="single", categ="Device",
            label=_translate("Num. diodes"),
            hint=_translate(
                "How many diodes this device has."
            )
        )

        return params, order

    def addRequirements(self):
        """
        Add any required module/package imports for this backend
        """
        self.exp.requireImport(
            importName="tpad",
            importFrom="psychopy_bbtk"
        )

    def writeDeviceCode(self, buff):
        # get inits
        inits = getInitVals(self.params)
        # make ButtonGroup object
        code = (
            "deviceManager.addDevice(\n"
            "    deviceClass='psychopy_bbtk.tpad.TPadPhotodiodeGroup',\n"
            "    deviceName=%(deviceLabel)s,\n"
            "    pad=%(bbtkSerialPort)s,\n"
            "    channels=%(bbtkNChannels)s,\n"
            ")\n"
        )
        buff.writeOnceIndentedLines(code % inits)


class TPadButtonBoxBackend(DeviceBackend):
    """
    Adds backend parameters for the BBTK TPad to the ButtonBoxComponent
    """

    # which component is this backend for?
    component = ButtonBoxComponent
    # what value should Builder use for this backend?
    key = "tpad"
    # what label should be displayed by Builder for this backend?
    label = _translate("BBTK TPad")
    # what hardware classes are relevant to this backend?
    deviceClasses = ["psychopy_bbtk.tpad.TPadButtonGroup"]

    def getParams(self):
        """
        Get parameters from this backend to add to each new instance of ButtonBoxComponent

        Returns
        -------
        dict[str:Param]
            Dict of Param objects, which will be added to any Button Box Component's params, along with a dependency
            to only show them when this backend is selected
        list[str]
            List of param names, defining the order in which params should appear
        """
        # define order
        order = [
            "bbtkSerialPort",
            "bbtkNButtons"
        ]
        # define params
        params = {}

        params['bbtkSerialPort'] = Param(
            "", valType="str", inputType="choice", categ="Device",
            allowedVals=getTPadPorts,
            label=_translate("COM port"),
            hint=_translate(
                "Serial port to connect to"
            )
        )
        params['bbtkNButtons'] = Param(
            10, valType="code", inputType="single", categ="Device",
            label=_translate("Num. buttons"),
            hint=_translate(
                "How many buttons this button box has."
            )
        )

        return params, order

    def addRequirements(self):
        """
        Add any required module/package imports for this backend
        """
        self.exp.requireImport(
            importName="tpad",
            importFrom="psychopy_bbtk"
        )

    def writeDeviceCode(self, buff):
        # get inits
        inits = getInitVals(self.params)
        # make ButtonGroup object
        code = (
            "deviceManager.addDevice(\n"
            "    deviceClass='psychopy_bbtk.tpad.TPadButtonGroup',\n"
            "    deviceName=%(deviceLabel)s,\n"
            "    pad=%(bbtkSerialPort)s,\n"
            "    channels=%(bbtkNButtons)s,\n"
            ")\n"
        )
        buff.writeOnceIndentedLines(code % inits)
