from psychopy.tests.test_liaison import TestLiaison, runInLiaison
from .utils import getTestTPadPhotodiode


class TestBBTKLiaison(TestLiaison):
    def test_tpad_photodiode(self):
        """
        Test that a TPadPhotodiodeGroup can be set up and calibrated via Liaison
        """
        # setup a photodiode
        diode = getTestTPadPhotodiode()
        # find threshold
        runInLiaison(
            self.server, self.protocol, "DeviceManager", "callDeviceMethod",
            "TestTPadPhotodiode", "findThreshold",
            "session.win", "1"
        )
        # find photodiode
        runInLiaison(
            self.server, self.protocol, "DeviceManager", "callDeviceMethod",
            "TestTPadPhotodiode", "findPhotodiode",
            "session.win", "1"
        )
