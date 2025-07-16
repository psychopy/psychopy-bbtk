from psychopy.hardware import serialdevice as sd, lightsensor, button
from psychopy.hardware.base import BaseDevice, BaseResponseDevice
from psychopy.hardware.manager import DeviceManager, ManagedDeviceError
from psychopy import logging
from psychopy.tools import systemtools as st
import re
import sys
import time

# import hardware classes in a version-safe way
try:
    from psychopy.hardware.button import BaseButtonGroup, ButtonResponse
except ImportError:
    BaseButtonGroup = BaseDevice
    ButtonResponse = BaseResponseDevice
try:
    from psychopy.hardware.soundsensor import BaseSoundSensorGroup, SoundSensorResponse
except ImportError:
    BaseSoundSensorGroup = BaseDevice
    SoundSensorResponse = BaseResponseDevice
try:
    from psychopy.hardware.lightsensor import BaseLightSensorGroup, LightSensorResponse
except ImportError:
    BaseLightSensorGroup = BaseDevice
    LightSensorResponse = BaseResponseDevice


# DeviceNotFoundError is only available from 2025.1.0 onwards, so import with a safe fallback
try:
    from psychopy.hardware.exceptions import DeviceNotConnectedError
except ImportError:
    class DeviceNotConnectedError(ConnectionError):
        def __init__(self, msg, deviceClass=None, context=None, *args):
            ConnectionError.__init__(self, msg)

# check whether FTDI driver is installed
hasDriver = False
try:
    import ftd2xx
    hasDriver = True
except FileNotFoundError:
    pass


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
    r"([{channels}]) ([{states}]) ([{buttons}]) (\d\d*)\r\n"
).format(
    channels="".join(re.escape(key) for key in channelCodes),
    states="".join(re.escape(key) for key in stateCodes),
    buttons="".join(re.escape(key) for key in buttonCodes)
)


def splitTPadMessage(message):
    return re.match(messageFormat, message).groups()


class TPadLightSensorGroup(lightsensor.BaseLightSensorGroup):
    def __init__(self, pad, channels, threshold=None, pos=None, size=None, units=None):
        _requestedPad = pad
        # get associated tpad
        self.parent = TPad.resolve(pad)
        # reference self in pad
        self.parent.nodes.append(self)
        # initialise base class
        lightsensor.BaseLightSensorGroup.__init__(
            self, channels=channels, threshold=threshold, pos=pos, size=size, units=units
        )
        # set to data collection mode
        self.parent.setMode(3)

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical device as a given other object.

        Parameters
        ----------
        other : TPadLightSensorGroup, dict
            Other TPadLightSensorGroup to compare against, or a dict of params (which much include
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
                'deviceName': f"TPadLightSensorGroup@{profile['port']}",
                'deviceClass': "psychopy_bbtk.tpad.TPadLightSensorGroup",
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
        self.parent.sendMessage(f"AAO{channel+1} {int(threshold)}")
        # force a sleep for diode to settle
        time.sleep(0.1)
        # get 0 or 1 according to light level
        resp = self.parent.awaitResponse(timeout=0.1)
        # with this threshold, is the sensor returning True?
        measurement = None
        if resp is not None:
            if resp.strip() == "1":
                measurement = True
            if resp.strip() == "0":
                measurement = False
        # store threshold
        self.threshold[channel] = threshold
        # return to sampling mode
        self.parent.setMode(3)

        return measurement

    def resetTimer(self, clock=logging.defaultClock):
        self.parent.resetTimer(clock=clock)

    def dispatchMessages(self):
        """
        Dispatch messages from parent TPad to this light sensor group

        Returns
        -------
        bool
            True if request sent successfully
        """
        self.parent.dispatchMessages()
    
    def hasUnfinishedMessage(self):
        """
        Is the parent TPad waiting for an end-of-line character?
        
        Returns
        -------
        bool
            True if there is a partial message waiting for an end-of-line
        """
        return self.parent.hasUnfinishedMessage()

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
        # create LightSensorResponse object
        resp = lightsensor.LightSensorResponse(
            t=time, channel=channel-1, value=state, threshold=self.getThreshold(channel-1)
        )

        return resp

    def findSensor(self, win, channel=None, retryLimit=5):
        # set mode to 3
        self.parent.setMode(3)
        self.parent.pause()
        # continue as normal
        return lightsensor.BaseLightSensorGroup.findSensor(self, win, channel, retryLimit=5)

    def findThreshold(self, win, channel=None):
        # set mode to 0 and lock it so mode doesn't change during setThreshold calls
        self.parent.setMode(0)
        self.parent.lockMode()
        # continue as normal
        resp = lightsensor.BaseLightSensorGroup.findThreshold(self, win, channel)
        # set back to mode 3
        self.parent.unlockMode()
        self.parent.setMode(3)

        return resp


class TPadButtonGroup(button.BaseButtonGroup):
    def __init__(self, pad, channels=9):
        # get associated tpad
        self.parent = TPad.resolve(pad)
        # reference self in pad
        self.parent.nodes.append(self)
        # initialise base class
        button.BaseButtonGroup.__init__(self, channels=channels)
        # set to data collection mode
        self.parent.setMode(3)

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
    
    def hasUnfinishedMessage(self):
        """
        Is the parent TPad waiting for an end-of-line character?
        
        Returns
        -------
        bool
            True if there is a partial message waiting for an end-of-line
        """
        return self.parent.hasUnfinishedMessage()

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
        # convert channel to int
        channel = int(channel)
        
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
                'deviceName': f"TPadButtonGroup@{profile['port']}",
                'deviceClass': "psychopy_bbtk.tpad.TPadButtonGroup",
                'pad': profile['port'],
                'channels': 10,
            })

        return devices

    def resetTimer(self, clock=logging.defaultClock):
        self.parent.resetTimer(clock=clock)


class TPadSoundSensorGroup(BaseSoundSensorGroup):
    def __init__(self, pad, channels=1, threshold=None):
        _requestedPad = pad
        # get associated tpad
        self.parent = TPad.resolve(pad)
        # reference self in pad
        self.parent.nodes.append(self)
        # initialise base class
        BaseSoundSensorGroup.__init__(
            self, channels=channels, threshold=threshold
        )
        # set to data collection mode
        self.parent.setMode(3)
    
    def resetTimer(self, clock=logging.defaultClock):
        self.parent.resetTimer(clock=clock)
    
    def _setThreshold(self, threshold, channel=None):
        """
        Device-specific threshold setting method. This will be called by `setThreshold` and should 
        be overloaded by child classes of BaseSoundSensor.

        Parameters
        ----------
        threshold : int
            Threshold at which to register a SoundSensor response, with 0 being the lowest possible 
            volume and 255 being the highest.
        channel : int
            Channel to set the threshold for (if applicable to device)

        Returns
        ------
        bool
            True if current decibel level is above the threshold.
        """
        if threshold is None:
            return
        # enter command mode
        self.parent.setMode(0)
        # send command to set threshold
        self.parent.sendMessage(f"AAVK{channel+1} {int(threshold)}")
        # force a sleep for diode to settle
        time.sleep(0.1)
        # get 0 or 1 according to light level
        resp = self.parent.awaitResponse(timeout=0.1)
        # with this threshold, is the sensor returning True?
        measurement = None
        if resp is not None:
            if resp.strip() == "1":
                measurement = True
            if resp.strip() == "0":
                measurement = False
        # store threshold
        self.threshold[channel] = threshold
        # return to sampling mode
        self.parent.setMode(3)

        return measurement
    
    def dispatchMessages(self):
        self.parent.dispatchMessages()
    
    def hasUnfinishedMessage(self):
        """
        Is the parent TPad waiting for an end-of-line character?
        
        Returns
        -------
        bool
            True if there is a partial message waiting for an end-of-line
        """
        return self.parent.hasUnfinishedMessage()
    
    def parseMessage(self, message):
        # if given a string, split according to regex
        if isinstance(message, str):
            message = splitTPadMessage(message)
        device, state, channel, time = message
        # convert state to bool
        if state == "P":
            state = True
        elif state == "R":
            state = False
        # create SoundSensorResponse object
        resp = SoundSensorResponse(
            t=time, channel=channel-1, value=state, threshold=self.getThreshold(channel-1)
        )

        return resp
    
    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical device as a given other object.

        Parameters
        ----------
        other : TPadSoundSensorGroup, dict
            Other TPadSoundSensorGroupGroup to compare against, or a dict of params (which much include
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
                'deviceName': f"TPadSoundSensorGroup@{profile['port']}",
                'deviceClass': "psychopy_bbtk.tpad.TPadSoundSensorGroup",
                'pad': profile['port'],
                'channels': 1,
            })

        return devices


class TPad(sd.SerialDevice):
    name = b"TPad"

    def __init__(
            self, port=None, baudrate=115200,
            byteSize=8, stopBits=1,
            parity="N",  # 'N'one, 'E'ven, 'O'dd, 'M'ask,
            eol=b"\r\n",
            maxAttempts=1, pauseDuration=1/1000,
            checkAwake=True
    ):
        # error if there's no ftdi driver
        if not hasDriver:
            raise ModuleNotFoundError(
                "Could not connect to BBTK device as your computer is missing a necessary "
                "hardware driver. You should be able to find the correct driver for your operating "
                "system here: https://ftdichip.com/drivers/vcp-drivers/"
            )
        # get ports with a TPad connected
        possiblePorts = self._detectComPort()
        # error if there are none
        if not possiblePorts:
            raise DeviceNotConnectedError(
                (
                    "Could not find any connected TPad. Try checking the USB cable or restarting "
                    "your PC."
                ),
                deviceClass=TPad
            )
        # if no port given, take first valid one
        if port is None:
            port = possiblePorts[0]
        # if port doesn't have a TPad on, error
        if port not in possiblePorts:
            raise DeviceNotConnectedError(
                (
                    "Could not find a TPad on {port}, but did find TPad(s) on: {possiblePorts}.",
                ).format(port=port, possiblePorts=possiblePorts),
                deviceClass=TPad
            )
        # initial value for last timer reset
        self._lastTimerReset = logging.defaultClock._timeAtLastReset
        # dict of responses by timestamp
        self.messages = {}
        # indicator that a message dispatch is currently in progress (prevents threaded 
        # dispatch loops from tripping over one another)
        self._dispatchInProgress = False
        # attribute to store last line in case of splicing
        self._lastLine = ""
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

    @staticmethod
    def getAvailableDevices():
        import serial.tools.list_ports

        profiles = []

        # iterate through serial devices via pyserial
        for device in serial.tools.list_ports.comports():
            print(device.pid, device.vid)
            # filter only for those which look like a tpad
            if device.vid == 1027 and device.pid in (1000, 1001, 1002, 1003, 1004):
                # construct profile
                profiles.append({
                    'deviceName': f"TPad@{device.device}",
                    'deviceClass': "psychopy_bbtk.tpad.TPad",
                    'port': device.device
                })
        
        return profiles

    @classmethod
    def resolve(cls, requested):
        """
        Take a value given to a device which has a TPad as its parent and, from it, 
        find/make the associated TPad object.

        Parameters
        ----------
        requested : str, int or TPad
            Value to resolve
        """
        # if requested is already a handle, return as is
        if isinstance(requested, cls):
            return requested
        # try to get by name
        if isinstance(requested, str):
            pad = DeviceManager.getDevice(requested)
            # if found, return
            if pad is not None:
                return pad
        # if requested looks like a port number, turn it into a port string
        if isinstance(requested, int):
            requested = f"COM{requested}"
        # try to get by port
        if isinstance(requested, str):
            pad = DeviceManager.getDeviceBy("portString", requested, deviceClass="psychopy_bbtk.tpad.TPad")
            # if found, return
            if pad is not None:
                return pad
        # if given port of a not-yet setup device, set one up
        if requested is None or isinstance(requested, str):
            return DeviceManager.addDevice(
                deviceClass="psychopy_bbtk.tpad.TPad",
                deviceName=f"TPad@{requested}",
                port=requested
            )
        # if still not found, raise error
        raise ManagedDeviceError(f"Could not find/create any {cls.__name__} object from the value {requested}")

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
    
    def sendMessage(self, message, autoLog=True):
        # dispatch any messages on the buffer to completion before sending message
        maxIter = 5
        while maxIter >= 0 and (self.com.in_waiting or self._lastLine):
            self.dispatchMessages()
            self.pause()
        
        return sd.SerialDevice.sendMessage(self, message, autoLog)

    def dispatchMessages(self):
        # do nothing if there's already a dispatch in progress
        if self._dispatchInProgress:
            return
        # mark that a dispatch has begun
        self._dispatchInProgress = True
        # get data from box
        data = self.getResponse(length=-1, timeout=1/10000)
        # handle line splicing
        if data:
            # split into lines
            data = data.splitlines(keepends=True)
            # prepend last unfinished line to first line of this dispatch
            data[0] = self._lastLine + data[0]
            # if last line wasn't finished, store it for next dispatch
            if not data[-1].endswith("\r\n"):
                self._lastLine = data.pop(-1)
            else:
                self._lastLine = ""
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
                    # if device is C, dispatch only to sensors
                    if device == "C" and not isinstance(node, TPadLightSensorGroup):
                        continue
                    # if device is M, dispatch only to voice keys
                    if device == "M" and not isinstance(node, TPadSoundSensorGroup):
                        continue
                    # dispatch to node
                    message = node.parseMessage(parts)
                    node.receiveMessage(message)
            else:
                logging.debug(f"Received unparsable message from TPad: {repr(line)}")
        # mark that a dispatch has finished
        self._dispatchInProgress = False
    
    def hasUnfinishedMessage(self):
        """
        We don't wait for an end-of-line from the TPad device before continuing, as 
        dispatchMessages is often called in a frame loop so waiting for messages would 
        ruin the frame rate. If just the start of a message has been received, this 
        function will return True.

        Usage
        -----
        If you want to be certain that all events have been dispatched, you can do:
        ```
        timeout = Clock()
        while myTPad.hasUnfinishedMessage() and timeout.getTime() < 0.1:
            myTPad.dispatchMessages()
        ```
        (the purpose of the `timeout` clock is to avoid getting into an infinite loop 
        if the TPad sends anything unexpected)
        
        Returns
        -------
        bool
            True if there is a partial message waiting for an end-of-line
        """
        return bool(self._lastLine)

    @staticmethod
    def _detectComPort():
        # find available devices
        available = TPad.getAvailableDevices()
        # get all available ports
        return [profile['port'] for profile in available]

    def setMode(self, mode):
        self.dispatchMessages()
        # skip if mode is locked
        if self._modeLock:
            return
        # skip if already in desired mode
        if self._mode == mode:
            return
        # store requested mode
        self._mode = mode
        # exit out of whatever mode we're in (effectively set it to 0)
        self.com.write(b"X")
        self.awaitResponse(timeout=0.1)
        if mode > 0:
            # set mode
            self.sendMessage(f"MOD{mode}")
            self.awaitResponse(timeout=0.1)

    def getMode(self):
        if self._mode is None:
            # if mode not set before, get it from device
            self.com.write(b"Z")
            resp = self.awaitResponse(timeout=0.1)
            # try to get mode from response
            try:
                self._mode = int(resp.strip())
            except:
                # if this fails, just warn and keep as None
                logging.warn(
                    "Could not get current mode from TPad, expected a 0, 1, 2 or 3 but got: {}. "
                    "Reverting to None."
                    .format(resp)
                )
                pass
        
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
        # call FIRM (firmware version) and get response
        self.sendMessage("FIRM")
        resp = self.awaitResponse(multiline=True)
        logging.info(
            f"TPad device on {self.portString} is awake, it reports its firmware version as: {resp}"
        )

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
            resp = self.awaitResponse()
            # how long did it take?
            dur = time.time() - start
            # if we got a response, store how long
            if resp is not None:
                times.append(dur)
            else:
                # print warning that we got no response
                logging.warn(
                    f"Repeatedly sent `FIRM` to TPad and got no response on attempt {n+1}. "
                )
            # give the box time to rest
            time.sleep(0.01)
        # average times
        avg = sum(times) / len(times)
        # return to data mode
        self.setMode(3)
        self.awaitResponse()
        # are we below the target?
        valid = avg <= target
        # warn if we are
        if not valid:
            logging.warn(
                f"Expected TPad to respond to `FIRM` within {target}s, but average response time "
                f"was {avg}s."
            )

        return valid, avg

    def resetTimer(self, clock=logging.defaultClock):
        if self.getMode() == 3:
            # if in mode 3, set using R so as not to disrupt data collection
            self.sendMessage("R")
        else:
            # otherwise, switch to mode 0 and use REST
            self.setMode(0)
            self.sendMessage("REST")
        # store time
        self._lastTimerReset = clock.getTime(format=float)
        # get returned val
        self.awaitResponse(timeout=0.1)
