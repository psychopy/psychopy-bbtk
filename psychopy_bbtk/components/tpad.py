from psychopy.experiment import Param, getInitVals
from psychopy.localization import _translate
from psychopy.experiment.plugins import DeviceBackend, PluginDevicesMixin

# import Component/Routine classes in a version-safe way
try:
    from psychopy.experiment.components.buttonBox import ButtonBoxComponent
except ImportError:
    ButtonBoxComponent = PluginDevicesMixin
try:
    from psychopy.experiment.routines.visualValidator import VisualValidatorRoutine
except ImportError:
    VisualValidatorRoutine = PluginDevicesMixin
try:
    from psychopy.experiment.routines.audioValidator import AudioValidatorRoutine
except ImportError:
    AudioValidatorRoutine = PluginDevicesMixin
try:
    from psychopy.experiment.components.soundsensor import SoundSensorComponent
except ImportError:
    SoundSensorComponent = PluginDevicesMixin


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


class TPadVisualValidatorBackend(DeviceBackend):
    # which component is this backend for?
    component = VisualValidatorRoutine
    # what value should Builder use for this backend?
    key = "tpad"
    # what label should be displayed by Builder for this backend?
    label = _translate("BBTK TPad")
    # what hardware classes are relevant to this backend?
    deviceClasses = ["psychopy_bbtk.tpad.TPadLightSensorGroup"]

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
            "    deviceClass='psychopy_bbtk.tpad.TPadLightSensorGroup',\n"
            "    deviceName=%(deviceLabel)s,\n"
            "    pad=%(bbtkSerialPort)s,\n"
            "    channels=%(bbtkNChannels)s,\n"
            ")\n"
        )
        buff.writeOnceIndentedLines(code % inits)


class TPadAudioValidatorBackend(DeviceBackend):
    component = AudioValidatorRoutine
    key = "tpad"
    label = _translate("BBTK TPad")
    deviceClasses = ['psychopy_bbtk.tpad.TPadSoundSensorGroup']

    def getParams(self):
        # define order
        order = [
            "bbtkSerialPort",
            "bbtkChannels",
            "bbtkThreshold",
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
        params['bbtkChannels'] = Param(
            1, valType="code", inputType="single", categ="Device",
            label=_translate("Num. channels"),
            hint=_translate(
                "How many microphones are plugged into this device?"
            )
        )
        params[f'bbtkThreshold'] = Param(
            0, valType='code', inputType="single", categ='Device',
            label=_translate("Threshold"),
            hint=_translate(
                "Threshold volume (0 for min, 255 for max) above which to register a response"
            )
        )

        return params, order

    def addRequirements(self):
        """
        Add any required module/package imports for this backend
        """
        return
    
    def writeDeviceCode(self, buff):
        # get inits
        inits = getInitVals(self.params)
        # make SoundSensor object
        code = (
            f"deviceManager.addDevice(\n"
            f"    deviceClass='psychopy_bbtk.tpad.TPadSoundSensorGroup',\n"
            f"    deviceName=%(deviceLabel)s,\n"
            f"    pad=%(bbtkSerialPort)s,\n"
            f"    channels=%(bbtkChannels)s,\n"
            f"    threshold=%(bbtkThreshold)s,\n"
            f")\n"
        )
        buff.writeIndentedLines(code % inits)


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


class TPadSoundSensorBackend(DeviceBackend):
    key = "tpad"
    label = _translate("BBTK TPad")
    component = SoundSensorComponent
    deviceClasses = ['psychopy_bbtk.tpad.TPadSoundSensorGroup']

    def getParams(self):
        # define order
        order = [
            "bbtkSerialPort",
            "bbtkChannels",
            "bbtkThreshold",
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
        params['bbtkChannels'] = Param(
            1, valType="code", inputType="single", categ="Device",
            label=_translate("Num. channels"),
            hint=_translate(
                "How many microphones are plugged into this device?"
            )
        )
        params[f'bbtkThreshold'] = Param(
            0, valType='code', inputType="single", categ='Device',
            label=_translate("Threshold"),
            hint=_translate(
                "Threshold volume (0 for min, 255 for max) above which to register a response"
            )
        )

        return params, order

    def addRequirements(self):
        self.exp.requireImport(
            importName="tpad", importFrom="psychopy_bbtk"
        )

    def writeDeviceCode(self, buff):
        # get inits
        inits = getInitVals(self.params)
        # make SoundSensor object
        code = (
            f"deviceManager.addDevice(\n"
            f"    deviceClass='psychopy_bbtk.tpad.TPadSoundSensorGroup',\n"
            f"    deviceName=%(deviceLabel)s,\n"
            f"    pad=%(bbtkSerialPort)s,\n"
            f"    channels=%(bbtkChannels)s,\n"
            f"    threshold=%(bbtkThreshold)s,\n"
            f")\n"
        )
        buff.writeIndentedLines(code % inits)