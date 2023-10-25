from psychopy.hardware import base, serialdevice as sd, photodiode, button
from psychopy.hardware.manager import deviceManager, DeviceManager, DeviceMethod
from psychopy import logging, layout
from psychopy.tools import systemtools as st
import serial
import re

# possible values for self.channel
channelCodes = {
    'A': "Buttons",
    'C': "Optos",
    'M': "Voice key",
    'T': "TTL in",
}
# possible values for self.state
stateCodes = {
    'P': "Pressed/On",
    'R': "Released/Off",
}
# possible values for self.button
buttonCodes = {
    '1': "Button 1",
    '2': "Button 2",
    '3': "Button 2",
    '4': "Button 2",
    '5': "Button 2",
    '6': "Button 2",
    '7': "Button 2",
    '8': "Button 2",
    '9': "Button 2",
    '0': "Button 2",
    '[': "Opto 1",
    ']': "Opto 2",
}

# define format for messages
messageFormat = (
    r"([{channels}]) ([{states}]) ([{buttons}]) (\d*)"
).format(
    channels="".join(re.escape(key) for key in channelCodes),
    states="".join(re.escape(key) for key in stateCodes),
    buttons="".join(re.escape(key) for key in buttonCodes)
)


def splitTPadMessage(message):
    return re.match(messageFormat, message).groups()


class TPadManagerPlugin(DeviceManager):
    """
    Class which plugs in to DeviceManager and adds methods for managing BBTK TPad devices
    """
    @DeviceMethod("tpad", "add")
    def addTPad(self, name=None, port=None, pauseDuration=1/240):
        """
        Add a BBTK TPad.

        Parameters
        ----------
        name : str or None
            Arbitrary name to refer to this TPad by. Use None to generate a unique name.
        port : str, optional
            COM port to which the TPad is conencted. Use None to search for port.
        pauseDuration : int, optional
            How long to wait after sending a serial command to the TPad

        Returns
        -------
        TPad
            TPad object.
        """
        # make unique name if none given
        if name is None:
            name = DeviceManager.makeUniqueName(self, "tpad")
        self._assertDeviceNameUnique(name)
        # take note of ports already initialised
        takenPorts = {dev.portString: nm for nm, dev in self.getTPads().items()}
        # make/get device
        if port not in takenPorts:
            self._devices['tpad'][name] = TPadDevice(port=port, pauseDuration=pauseDuration)
        else:
            self._devices['tpad'][name] = takenPorts[port]
        # return created TPad
        return self._devices['tpad'][name]

    @DeviceMethod("tpad", "remove")
    def removeTPad(self, name):
        """
        Remove a TPad.

        Parameters
        ----------
        name : str
            Name of the TPad.
        """
        del self._devices['tpad'][name]

    @DeviceMethod("tpad", "get")
    def getTPad(self, name):
        """
        Get a TPad by name.

        Parameters
        ----------
        name : str
            Arbitrary name given to the TPad when it was `add`ed.

        Returns
        -------
        TPad
            The requested TPad
        """
        return self._devices['tpad'].get(name, None)

    @DeviceMethod("tpad", "getall")
    def getTPads(self):
        """
        Get a mapping of TPads that have been initialized.

        Returns
        -------
        dict
            Dictionary of TPads that have been initialized. Where the keys
            are the names of the keyboards and the values are the keyboard
            objects.

        """
        return self._devices['tpad']

    @DeviceMethod("tpad", "available")
    def getAvailableTPads(self):
        """
        Get details of all available TPad devices.

        Returns
        -------
        dict
            Dictionary of information about available TPads connected to the system.
        """

        # error to raise if this fails
        err = ConnectionError(
            "Could not detect COM port for TPad device. Try supplying a COM port directly."
        )

        foundDevices = []
        # look for all serial devices
        for profile in st.systemProfilerWindowsOS(connected=True, classname="Ports"):
            # skip non-TPads
            if "BBTKTPAD" not in profile['Instance ID']:
                continue
            # find "COM" in profile description
            desc = profile['Device Description']
            start = desc.find("COM") + 3
            end = desc.find(")", start)
            # if there's no reference to a COM port, fail
            if -1 in (start, end):
                raise err
            # get COM port number
            num = desc[start:end]
            # if COM port number doesn't look numeric, fail
            if not num.isnumeric():
                raise err
            # append
            foundDevices.append(
                {'port': f"COM{num}"}
            )

        return foundDevices


class TPadPhotodiode(photodiode.BasePhotodiode):
    def __init__(self, pad, number):
        # initialise base class
        photodiode.BasePhotodiode.__init__(self, pad)
        # store number
        self.number = number
        # store device
        self.device = self.parent.device

    def setThreshold(self, threshold):
        self._threshold = threshold
        self.device.setMode(0)
        self.device.sendMessage(f"AAO{self.number} {threshold}")
        self.device.pause()
        self.device.setMode(3)

    def parseMessage(self, message):
        # if given a string, split according to regex
        if isinstance(message, str):
            message = splitTPadMessage(message)
        # split into variables
        # assert isinstance(message, (tuple, list)) and len(message) == 4
        channel, state, number, time = message
        # convert state to bool
        if state == "P":
            state = True
        elif state == "R":
            state = False
        # # validate
        # assert channel == "C", (
        #     "TPadPhotometer {} received non-photometer message: {}"
        # ).format(self.number, message)
        # assert number == str(self.number), (
        #     "TPadPhotometer {} received message intended for photometer {}: {}"
        # ).format(self.number, number, message)
        # create PhotodiodeResponse object
        resp = photodiode.PhotodiodeResponse(
            time, state, threshold=self.getThreshold()
        )

        return resp

    def findPhotodiode(self, win):
        # set mode to 3
        self.device.setMode(3)
        self.device.pause()
        # continue as normal
        return photodiode.BasePhotodiode.findPhotodiode(self, win)


class TPadButton(button.BaseButton):
    def __init__(self, pad, number):
        # initialise base class
        button.BaseButton.__init__(self, parent=pad)
        # store number
        self.number = number

    def parseMessage(self, message):
        # if given a string, split according to regex
        if isinstance(message, str):
            message = splitTPadMessage(message)
        # split into variables
        # assert isinstance(message, (tuple, list)) and len(message) == 4
        channel, state, number, time = message
        # convert state to bool
        if state == "P":
            state = True
        elif state == "R":
            state = False
        # create PhotodiodeResponse object
        resp = button.ButtonResponse(
            time, state
        )

        return resp


class TPadVoicekey:
    def __init__(self, *args, **kwargs):
        pass


class TPad:
    def __init__(self, name=None, port=None, pauseDuration=1/240):
        # get port if not given
        if port is None:
            port = self._detectComPort()
        # get/make device
        if deviceManager.checkDeviceNameAvailable(name):
            # if no matching device is in DeviceManager, make a new one
            self.device = deviceManager.addTPad(
                name=name, port=port, pauseDuration=pauseDuration
            )
        else:
            # otherwise, use the existing device
            self.device = deviceManager.getTPad(name)

        # dict of responses by timestamp
        self.messages = {}
        # inputs
        self.photodiodes = {i + 1: TPadPhotodiode(self, i + 1) for i in range(2)}
        self.buttons = {i + 1: TPadButton(self, i + 1) for i in range(10)}
        self.voicekeys = {i + 1: TPadVoicekey(self, i + 1) for i in range(1)}
        # reset timer
        self._lastTimerReset = None
        self.resetTimer()

    @property
    def nodes(self):
        """
        Returns
        -------
        list
            List of nodes (photodiodes, buttons and voicekeys) managed by this TPad.
        """
        return list(self.photodiodes.values()) + list(self.buttons.values()) + list(self.voicekeys.values())

    @staticmethod
    def _detectComPort():
        # find available devices
        available = deviceManager.getAvailableTPadDevices()
        # error if there are none
        if not available:
            raise ConnectionError(
                "Could not find any TPad."
            )
        # get all available ports
        return [profile['port'] for profile in available]

    def addListener(self, listener):
        """
        Add a listener, which will receive all the messages dispatched by this TPad.

        Parameters
        ----------
        listener : hardware.listener.BaseListener
            Object to duplicate messages to when dispatched by this TPad.
        """
        # add listener to all nodes
        for node in self.nodes:
            node.addListener(listener)

    def setMode(self, mode):
        # dispatch messages now to clear buffer
        self.dispatchMessages()
        # exit out of whatever mode we're in (effectively set it to 0)
        try:
            self.device.sendMessage("X")
            self.device.pause()
        except serial.serialutil.SerialException:
            pass
        # set mode
        self.device.sendMessage(f"MOD{mode}")
        self.device.pause()
        # clear messages
        self.device.getResponse()

    def resetTimer(self, clock=logging.defaultClock):
        # enter settings mode
        self.setMode(0)
        # send reset command
        self.device.sendMessage(f"REST")
        # store time
        self._lastTimerReset = clock.getTime(format=float)
        # allow time to process
        self.device.pause()
        # reset mode
        self.setMode(3)

    def isAwake(self):
        self.setMode(0)
        # call help and get response
        self.device.sendMessage("HELP")
        resp = self.device.getResponse()
        # set to mode 3
        self.setMode(3)

        return bool(resp)

    def dispatchMessages(self, timeout=None):
        # if timeout is None, use pause duration
        if timeout is None:
            timeout = self.device.pauseDuration
        # get data from box
        self.device.pause()
        data = sd.SerialDevice.getResponse(self.device, length=2, timeout=timeout)
        self.device.pause()
        # parse lines
        for line in data:
            if re.match(messageFormat, line):
                # if line fits format, split into attributes
                channel, state, number, time = splitTPadMessage(line)
                # integerise number
                number = int(number)
                # get time in s using defaultClock units
                time = float(time) / 1000 + self._lastTimerReset
                # store in array
                parts = (channel, state, button, time)
                # store message
                self.messages[time] = line
                # choose object to dispatch to
                node = None
                if channel == "A" and number in self.buttons:
                    node = self.buttons[number]
                if channel == "C" and number in self.photodiodes:
                    node = self.photodiodes[number]
                if channel == "M" and number in self.voicekeys:
                    node = self.voicekeys[number]
                # dispatch to node
                if node is not None:
                    message = node.parseMessage(parts)
                    node.receiveMessage(message)

    def calibratePhotodiode(self, level=127):
        # set to mode 0
        self.setMode(0)
        # call help and get response
        self.device.sendMessage(f"AAO1 {level}")
        self.device.sendMessage(f"AAO2 {level}")
        self.device.getResponse()
        # set to mode 3
        self.setMode(3)


class TPadDevice(sd.SerialDevice, base.BaseDevice):
    def __init__(self, port=None, pauseDuration=1/240):
        # initialise as a SerialDevice
        sd.SerialDevice.__init__(self, port=port, baudrate=115200, pauseDuration=pauseDuration)
