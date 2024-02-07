from psychopy.hardware import base, serialdevice as sd, photodiode, button
from psychopy.hardware.manager import deviceManager, DeviceManager
from psychopy import logging, layout
from psychopy.tools import systemtools as st
import serial
import re
import sys

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
    r"([{channels}]) ([{states}]) ([{buttons}]) (\d\d*)"
).format(
    channels="".join(re.escape(key) for key in channelCodes),
    states="".join(re.escape(key) for key in stateCodes),
    buttons="".join(re.escape(key) for key in buttonCodes)
)


def splitTPadMessage(message):
    return re.match(messageFormat, message).groups()


class TPadPhotodiodeGroup(photodiode.BasePhotodiodeGroup):
    def __init__(self, pad, channels, threshold=None, pos=None, size=None, units=None):
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
        self.parent = pad
        photodiode.BasePhotodiodeGroup.__init__(
            self, channels=channels, threshold=threshold, pos=pos, size=size, units=units
        )

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical device as a given other object.

        Parameters
        ----------
        other : TPadPhotodiodeGroup, dict
            Other TPadPhotodiodeGroup to compare against, or a dict of params (which much include
            `port` or `pad` as a key)

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        if isinstance(other, type(self)):
            # if given another TPadButtonGroup, compare parent boxes
            other = other.parent
        elif isinstance(other, dict) and "pad" in other:
            # create copy of dict so we don't affect the original
            other = other.copy()
            # if given a dict, make sure we have a `port` rather than a `pad`
            other['port'] = other['pad']
        # use parent's comparison method
        return self.parent.isSameDevice(other)

    @staticmethod
    def getAvailableDevices():
        devices = []
        # iterate through profiles of all serial port devices
        for profile in TPad.getAvailableDevices():
            devices.append({
                'deviceName': profile['deviceName'] + "_photodiodes",
                'pad': profile['port'],
                'channels': 2,
            })

        return devices

    def _setThreshold(self, threshold, channel):
        if threshold is None:
            return
        # enter command mode
        self.parent.setMode(0)
        # send command to set threshold
        self.parent.sendMessage(f"AAO{channel+1} {threshold}")
        resp = self.parent.awaitResponse()
        # with this threshold, is the photodiode returning True?
        measurement = None
        if resp is not None:
            if resp.strip() == "1":
                measurement = True
            if resp.strip() == "0":
                measurement = False
        # return to sampling mode
        self.parent.setMode(3)

        return measurement

    def resetTimer(self, clock=logging.defaultClock):
        self.parent.resetTimer(clock=clock)

    def dispatchMessages(self):
        """
        Dispatch messages from parent TPad to this photodiode group

        Returns
        -------
        bool
            True if request sent successfully
        """
        self.parent.dispatchMessages()

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
            t=time, channel=channel-1, value=state, threshold=self.getThreshold(channel-1)
        )

        return resp

    def findPhotodiode(self, win, channel):
        # set mode to 3
        self.parent.setMode(3)
        self.parent.pause()
        # continue as normal
        return photodiode.BasePhotodiodeGroup.findPhotodiode(self, win, channel)

    def findThreshold(self, win, channel):
        # set mode to 0 and lock it so mode doesn't change during setThreshold calls
        self.parent.setMode(0)
        self.parent.lockMode()
        # continue as normal
        resp = photodiode.BasePhotodiodeGroup.findThreshold(self, win, channel)
        self._setThreshold(0, channel=1)
        # set back to mode 3
        self.parent.unlockMode()
        self.parent.setMode(3)

        return resp


class TPadButtonGroup(button.BaseButtonGroup):
    def __init__(self, pad, channels=9):
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
        button.BaseButtonGroup.__init__(self, channels=channels)
        self.parent = pad

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical device as a given other object.

        Parameters
        ----------
        other : TPadButtonGroup, dict
            Other TPadButtonGroup to compare against, or a dict of params (which must include
            `port` or `pad` as a key)

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        if isinstance(other, type(self)):
            # if given another TPadButtonGroup, compare parent boxes
            other = other.parent
        elif isinstance(other, dict) and "pad" in other:
            # create copy of dict so we don't affect the original
            other = other.copy()
            # if given a dict, make sure we have a `port` rather than a `pad`
            other['port'] = other['pad']
        # use parent's comparison method
        return self.parent.isSameDevice(other)

    def dispatchMessages(self):
        """
        Dispatch messages from parent TPad to this button group

        Returns
        -------
        bool
            True if request sent successfully
        """
        self.parent.dispatchMessages()

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
        # convert channel to zero-indexed int
        channel = int(channel) - 1
        
        resp = button.ButtonResponse(
            t=time, channel=channel, value=state
        )

        return resp
    
    @staticmethod
    def getAvailableDevices():
        devices = []
        # iterate through profiles of all serial port devices
        for profile in TPad.getAvailableDevices():
            devices.append({
                'deviceName': profile['deviceName'] + "_buttons",
                'pad': profile['port'],
                'channels': 10,
            })

        return devices

    def resetTimer(self, clock=logging.defaultClock):
        self.parent.resetTimer(clock=clock)


class TPadVoicekey:
    def __init__(self, *args, **kwargs):
        pass


class TPad(sd.SerialDevice):
    def __init__(
            self, port=None, baudrate=115200,
            byteSize=8, stopBits=1,
            parity="N",  # 'N'one, 'E'ven, 'O'dd, 'M'ask,
            eol=b"\n",
            maxAttempts=1, pauseDuration=1/1000,
            checkAwake=True
    ):
        # get port if not given
        if port is None:
            port = self._detectComPort()[0]
        # initial value for last timer reset
        self._lastTimerReset = logging.defaultClock._timeAtLastReset
        # dict of responses by timestamp
        self.messages = {}
        # nodes
        self.nodes = []
        # attribute to keep track of mode state
        self._mode = None
        self._modeLock = False
        # initialise serial
        sd.SerialDevice.__init__(
            self, port=port, baudrate=baudrate,
            byteSize=byteSize, stopBits=stopBits,
            parity=parity,  # 'N'one, 'E'ven, 'O'dd, 'M'ask,
            eol=eol,
            maxAttempts=maxAttempts, pauseDuration=pauseDuration,
            checkAwake=checkAwake
        )
        # reset timer
        self.resetTimer()

    def close(self):
        # set mode to 0 on exit
        self.setMode(0)
        # close
        sd.SerialDevice.close(self)

    @staticmethod
    def getAvailableDevices():
        devices = []
        if sys.platform == "win32":  
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
        else:
            for profile in sd.SerialDevice.getAvailableDevices():
                devices.append({
                    'deviceName': profile['deviceName'],
                    'port': profile['port'],
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
        self.dispatchMessages()
        # skip if mode is locked
        if self._modeLock:
            return
        # store requested mode
        self._mode = mode
        # exit out of whatever mode we're in (effectively set it to 0)
        self.sendMessage("X")
        self.awaitResponse()
        if mode > 0:
            # set mode
            self.sendMessage(f"MOD{mode}")
            self.awaitResponse()

    def getMode(self):
        return self._mode

    def lockMode(self):
        """
        Temporarily lock to the current mode, meaning that subsequent called to `setMode` will
        return with no effect until `unlockMode` is called.

        Returns
        -------
        int
            Current mode
        """
        self._modeLock = True

        return self.getMode()

    def unlockMode(self):
        """
        Unlock the mode, allowing `setMode` to be called and to have an effect.

        Returns
        -------
        int
            Current mode
        """
        self._modeLock = False

        return self.getMode()

    def isAwake(self):
        self.setMode(0)
        # call help and get response
        self.sendMessage("HELP")
        resp = self.awaitResponse(multiline=True)
        # set to mode 3
        self.setMode(3)
        return bool(resp)

    def checkSpeed(self, target=5/1000):
        """
        Parameters
        ----------
        target : float
            Target time (s) which a single request should take to return.

        Returns
        -------
        bool
            True if average time to return was less than the target time
        float
            Average time taken to return
        """
        import time
        # enter command mode
        self.setMode(0)
        # repeat 25 times...
        times = []
        for n in range(25):
            # start timing
            start = time.time()
            # send commands
            self.sendMessage("FIRM")
            # what did we get?
            self.awaitResponse()
            # how long did it take?
            times.append(time.time() - start)
        # average times
        avg = sum(times) / len(times)
        # return to data mode
        self.setMode(3)
        self.awaitResponse()
        # are we below the target?
        valid = avg <= target

        return valid, avg

    def resetTimer(self, clock=logging.defaultClock):
        # make sure we're in mode 3
        if self.getMode() != 3:
            self.setMode(3)
        # send reset command
        self.sendMessage("R")
        # store time
        self._lastTimerReset = clock.getTime(format=float)
