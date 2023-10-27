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


class TPadPhotodiode(photodiode.BasePhotodiode):
    def __init__(self, pad, number):
        # initialise base class
        photodiode.BasePhotodiode.__init__(self, pad)
        # store number
        self.number = number

    def setThreshold(self, threshold):
        self._threshold = threshold
        self.parent.setMode(0)
        self.parent.sendMessage(f"AAO{self.number} {threshold}")
        self.parent.pause()
        self.parent.setMode(3)

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
        self.parent.setMode(3)
        self.parent.pause()
        # continue as normal
        return photodiode.BasePhotodiode.findPhotodiode(self, win)

    def findThreshold(self, win):
        # set mode to 3
        self.parent.setMode(3)
        self.parent.pause()
        # continue as normal
        return photodiode.BasePhotodiode.findThreshold(self, win)


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
        # get/make device
        if name in DeviceManager.devices:
            # if no matching device is in DeviceManager, make a new one
            self.device = deviceManager.addTPad(
                name=name, port=port, pauseDuration=pauseDuration
            )
        else:
            # otherwise, use the existing device
            self.device = deviceManager.getTPad(name)

    def addListener(self, listener):
        self.device.addListener(listener=listener)

    def dispatchMessages(self):
        self.device.dispatchMessages()

    def setMode(self, mode):
        self.device.setMode(mode=mode)

    def resetTimer(self, clock=logging.defaultClock):
        self.device.resetTimer(clock=clock)


class TPadDevice(sd.SerialDevice, base.BaseDevice):
    def __init__(
            self, port=None, baudrate=9600,
            byteSize=8, stopBits=1,
            parity="N",  # 'N'one, 'E'ven, 'O'dd, 'M'ask,
            eol=b"\n",
            maxAttempts=1, pauseDuration=0.1,
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
        self.photodiodes = {i + 1: TPadPhotodiode(self, i + 1) for i in range(2)}
        self.buttons = {i + 1: TPadButton(self, i + 1) for i in range(10)}
        self.voicekeys = {i + 1: TPadVoicekey(self, i + 1) for i in range(1)}

        # dict of responses by timestamp
        self.messages = {}
        # reset timer
        self._lastTimerReset = None
        self.resetTimer()

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

    @property
    def nodes(self):
        """
        Returns
        -------
        list
            List of nodes (photodiodes, buttons and voicekeys) managed by this TPad.
        """
        return list(self.photodiodes.values()) + list(self.buttons.values()) + list(self.voicekeys.values())

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


# register some aliases for the TPadDevice class with DeviceManager
DeviceManager.registerAlias("tpad", deviceClass="psychopy_bbtk.tpad.TPadDevice")
DeviceManager.registerAlias("psychopy_bbtk.tpad.TPad", deviceClass="psychopy_bbtk.tpad.TPadDevice")
