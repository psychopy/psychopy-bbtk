from psychopy import hardware
from psychopy_bbtk.tpad import TPad, TPadPhotodiodeGroup, TPadButtonGroup, TPadVoiceKey
import pytest

def getTestTPad():
    """
    Get the handle of the test suite's TPad object.

    Returns
    -------
    psychopy_bbtk.tpad.TPad
        The TPad object for the test suite
    """
    # look for any TPad with the correct name
    pad = hardware.DeviceManager.getDevice("TestTPad")
    # if there isn't one, try setting one up
    for profile in hardware.DeviceManager.getAvailableDevices("psychopy_bbtk.tpad.TPad"):
        profile['deviceName'] = "TestTPad"
        pad = hardware.DeviceManager.addDevice(
            **profile
        )
        return pad
    # if we didn't find a device, skip current test
    if pad is None:
        pytest.skip()

def getTestTPadPhotodiode():
    """
    Get the photodiode node of the test suite's TPad.

    Returns
    -------
    psychopy_bbtk.tpad.TPadPhotodiodeGroup
        The TPadPhotodiodeGroup object for the test suite
    """
    # get TPad
    pad = getTestTPad()
    # if there is none, skip
    if pad is None:
        pytest.skip()
    # get its photodiode node
    for node in pad.nodes:
        if isinstance(node,TPadPhotodiodeGroup):
            return node
    # if it has no photodiode node, try making one
    for profile in hardware.DeviceManager.getAvailableDevices("psychopy_bbtk.tpad.TPadPhotodiodeGroup"):
        profile['deviceName'] = "TestTPadPhotodiode"
        node = hardware.DeviceManager.addDevice(
            **profile
        )
        # we only need one
        return node
    # if we didn't find a device, skip current test
    if pad is None:
        pytest.skip()

def getTestTPadButtons():
    """
    Get the buttons node of the test suite's TPad.

    Returns
    -------
    psychopy_bbtk.tpad.TPadButtonGroup
        The TPadButtonGroup object for the test suite
    """
    # get TPad
    pad = getTestTPad()
    # if there is none, skip
    if pad is None:
        pytest.skip()
    # get its buttons node
    for node in pad.nodes:
        if isinstance(node,TPadButtonGroup):
            return node
    # if it has no buttons node, try making one
    for profile in hardware.DeviceManager.getAvailableDevices("psychopy_bbtk.tpad.TPadButtonGroup"):
        profile['deviceName'] = "TestTPadButtons"
        node = hardware.DeviceManager.addDevice(
            **profile
        )
        # we only need one
        return node
    # if we didn't find a device, skip current test
    if pad is None:
        pytest.skip()
