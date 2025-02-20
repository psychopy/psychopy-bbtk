from psychopy.tests.test_liaison import TestLiaison, runInLiaison


class TestBBTKLiaison(TestLiaison):
    def test_tpad_lightsensor(self):
        """
        Test that a TPadLightSensorGroup can be set up and calibrated via Liaison
        """
        runInLiaison(
            self.server, self.protocol, "DeviceManager", "addDevice",
            "psychopy_bbtk.tpad.TPadLightSensorGroup", "diode",
            "COM6", "2"
        )
        runInLiaison(
            self.server, self.protocol, "DeviceManager", "callDeviceMethod",
            "diode", "findThreshold",
            "session.win", "1"
        )
        runInLiaison(
            self.server, self.protocol, "DeviceManager", "callDeviceMethod",
            "diode", "findSensor",
            "session.win", "1"
        )
