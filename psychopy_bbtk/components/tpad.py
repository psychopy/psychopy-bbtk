from psychopy.experiment import Param, getInitVals
from psychopy.localization import _translate
from psychopy.experiment.components.buttonBox import ButtonBoxBackend


class TPadButtonBoxBackend(ButtonBoxBackend, key="tpad", label="BBTK TPad"):
    """
    Adds backend parameters for the BBTK TPad to the ButtonBoxComponent
    """
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
        ]
        # define params
        params = {}

        def getPorts():
            """
            Get a list of ports which have TPad devices connected.
            """
            from psychopy_bbtk.tpad import TPad
            ports = []
            # iterate through available button boxes
            for profile in TPad.getAvailableDevices():
                # add this box's port
                ports.append(
                    profile['port']
                )

            return ports

        params['bbtkSerialPort'] = Param(
            "", valType="str", inputType="choice", categ="Device",
            allowedVals=getPorts,
            label=_translate("COM port"),
            hint=_translate(
                "Serial port to connect to"
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
            "    deviceName=%(deviceName)s,\n"
            "    pad=%(serialPort)s,\n"
            "    channels=%(nButtons)s,\n"
            ")\n"
        )
        buff.writeOnceIndentedLines(code % inits)
