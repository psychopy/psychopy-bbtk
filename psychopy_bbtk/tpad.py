from psychopy.hardware import base, serialdevice as sd, photodiode, button
from psychopy.hardware.manager import deviceManager, DeviceManager
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


class TPadPhotodiodeGroup(photodiode.BasePhotodiodeGroup):
    def __init__(self, pad, channels):
        _requestedPad = pad
        # try to get associated tpad
        if isinstance(_requestedPad, str):
            # try getting by name
            pad = DeviceManager.getDevice(pad)
            # if failed, try getting by port
            if pad is None:
                pad = DeviceManager.getDeviceBy("portString", _requestedPad, deviceClass="psychopy_bbtk.tpad.TPad")
        # if still failed, make one
        if pad is None:
            pad = DeviceManager.addDevice(
                deviceClass="psychopy_bbtk.tpad.TPad",
                deviceName=_requestedPad,
                port=_requestedPad
            )

        # reference self in pad
        pad.nodes.append(self)
        # initialise base class
        photodiode.BasePhotodiodeGroup.__init__(self, pad, channels=channels)

    @staticmethod
    def getAvailableDevices():
        devices = []
        # iterate through profiles of all serial port devices
        for profile in TPad.getAvailableDevices():
            devices.append({
                'deviceName': profile['Instance ID'] + "_photodiodes",
                'pad': profile['port'],
                'channels': 2,
            })

        return devices

    def setThreshold(self, threshold, channels=(1, 2)):
        self._threshold = threshold
        self.parent.setMode(0)
        for n in channels:
            self.parent.sendMessage(f"AAO{n} {threshold}")
            self.parent.pause()
        self.parent.setMode(3)

    def parseMessage(self, message):
        # if given a string, split according to regex
        if isinstance(message, str):
            message = splitTPadMessage(message)
        # split into variables
        # assert isinstance(message, (tuple, list)) and len(message) == 4
        device, state, channel, time = message
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
            time, channel, state, threshold=self.getThreshold()
        )

        return resp

    def findPhotodiode(self, win, channel):
        # set mode to 3
        self.parent.setMode(3)
        self.parent.pause()
        # continue as normal
        return photodiode.BasePhotodiodeGroup.findPhotodiode(self, win, channel)

    def findThreshold(self, win, channel):
        # set mode to 3
        self.parent.setMode(3)
        self.parent.pause()
        # continue as normal
        return photodiode.BasePhotodiodeGroup.findThreshold(self, win, channel)


class TPadButtonGroup(button.BaseButtonGroup):
    def __init__(self, pad, channels=1):
        _requestedPad = pad
        # try to get associated tpad
        if isinstance(_requestedPad, str):
            # try getting by name
            pad = DeviceManager.getDevice(pad)
            # if failed, try getting by port
            if pad is None:
                pad = DeviceManager.getDeviceBy("portString", _requestedPad, deviceClass="psychopy_bbtk.tpad.TPad")
        # if still failed, make one
        if pad is None:
            pad = DeviceManager.addDevice(
                deviceClass="psychopy_bbtk.tpad.TPad",
                deviceName=_requestedPad,
                port=_requestedPad
            )

        # reference self in pad
        pad.nodes.append(self)
        # initialise base class
        button.BaseButtonGroup.__init__(self, parent=pad, channels=channels)

    def parseMessage(self, message):
        # if given a string, split according to regex
        if isinstance(message, str):
            message = splitTPadMessage(message)
        # split into variables
        # assert isinstance(message, (tuple, list)) and len(message) == 4
        device, state, channel, time = message
        # convert state to bool
        if state == "P":
            state = True
        elif state == "R":
            state = False
        
        resp = button.ButtonResponse(
            time, channel, state
        )

        return resp
    
    @staticmethod
    def getAvailableDevices():
        devices = []
        # iterate through profiles of all serial port devices
        for profile in TPad.getAvailableDevices():
            devices.append({
                'deviceName': profile['Instance ID'] + "_buttons",
                'pad': profile['port'],
                'channels': 10,
            })

        return devices


class TPadVoicekey:
    def __init__(self, *args, **kwargs):
        pass


class TPad(sd.SerialDevice):
    def __init__(
            self, port=None, baudrate=115200,
            byteSize=8, stopBits=1,
            parity="N",  # 'N'one, 'E'ven, 'O'dd, 'M'ask,
            eol=b"\n",
            maxAttempts=1, pauseDuration=1/240,
            checkAwake=True
    ):
        # get port if not given
        if port is None:
            port = self._detectComPort()[0]
        # initialise serial
        sd.SerialDevice.__init__(
            self, port=port, baudrate=baudrate,
            byteSize=byteSize, stopBits=stopBits,
            parity=parity,  # 'N'one, 'E'ven, 'O'dd, 'M'ask,
            eol=eol,
            maxAttempts=maxAttempts, pauseDuration=pauseDuration,
            checkAwake=checkAwake
        )
        # nodes
        self.nodes = []

        # dict of responses by timestamp
        self.messages = {}
        # reset timer
        self._lastTimerReset = None
        self.resetTimer()

    @staticmethod
    def getAvailableDevices():
        devices = []
        # iterate through profiles of all serial port devices
        for profile in st.systemProfilerWindowsOS(
            classid="{4d36e978-e325-11ce-bfc1-08002be10318}",
            connected=True
        ):
            # skip non-bbtk profiles
            if "BBTKTPAD" not in profile['Instance ID']:
                continue
            # find "COM" in profile description
            desc = profile['Device Description']
            start = desc.find("COM") + 3
            end = desc.find(")", start)
            # if there's no reference to a COM port, skip
            if -1 in (start, end):
                continue
            # get COM port number
            num = desc[start:end]

            devices.append({
                'deviceName': profile['Instance ID'],
                'port': f"COM{num}",
            })

        return devices

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

    def dispatchMessages(self):
        # get data from box
        self.pause()
        data = self.getResponse(length=2)
        self.pause()
        # parse lines
        for line in data:
            if re.match(messageFormat, line):
                # if line fits format, split into attributes
                device, state, channel, time = splitTPadMessage(line)
                # integerise number
                channel = int(channel)
                # get time in s using defaultClock units
                time = float(time) / 1000 + self._lastTimerReset
                # store in array
                parts = (device, state, channel, time)
                # store message
                self.messages[time] = line
                # choose object to dispatch to
                for node in self.nodes:
                    # if device is A, dispatch only to buttons
                    if device == "A" and not isinstance(node, TPadButtonGroup):
                        continue
                    # if device is C, dispatch only to photodiodes
                    if device == "C" and not isinstance(node, TPadPhotodiodeGroup):
                        continue
                    # if device is M, dispatch only to voice keys
                    if device == "M" and not isinstance(node, TPadVoicekey):
                        continue
                    # dispatch to node
                    message = node.parseMessage(parts)
                    node.receiveMessage(message)

    @staticmethod
    def _detectComPort():
        # find available devices
        available = TPad.getAvailableDevices()
        # error if there are none
        if not available:
            raise ConnectionError(
                "Could not find any TPad."
            )
        # get all available ports
        return [profile['port'] for profile in available]

    def setMode(self, mode):
        self.getResponse()
        # exit out of whatever mode we're in (effectively set it to 0)
        self.sendMessage("X")
        self.pause()
        # set mode
        self.sendMessage(f"MOD{mode}")
        self.pause()
        # clear messages
        self.getResponse()

    def isAwake(self):
        self.setMode(0)
        self.pause()
        # call help and get response
        self.sendMessage("HELP")
        self.pause()  # or response won't be ready
        resp = self.getResponse()  # get all chars (a usage message)
        # set to mode 3
        self.setMode(3)
        return bool(resp)

    def resetTimer(self, clock=logging.defaultClock):
        # enter settings mode
        self.setMode(0)
        # send reset command
        self.sendMessage(f"REST")
        # store time
        self._lastTimerReset = clock.getTime(format=float)
        # allow time to process
        self.pause()
        # reset mode
        self.setMode(3)
