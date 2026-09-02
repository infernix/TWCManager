"""Regression tests for Tesla BLE command result handling."""

from unittest.mock import Mock

from TWCManager.Vehicle.TeslaBLE import TeslaBLE


def make_ble(command_result):
    ble = TeslaBLE.__new__(TeslaBLE)
    ble.master = Mock()
    ble.master.settings = {"Vehicles": {"TESTVIN": {"configured": True}}}
    ble.binaryPath = "/bin/true"
    ble.commandTimeout = 5
    ble.isDocker = Mock(return_value=False)
    ble.sendPrivateKey = Mock(return_value=True)
    ble._ensure_pipe_closed = Mock()
    ble._run_command_with_timeout = Mock(return_value=command_result)
    return ble


def test_nonzero_exit_is_a_failed_command():
    ble = make_ble((b"", b"device or resource busy", 1))

    result = ble._sendCommand_internal("TESTVIN", "charging-stop")

    assert result is None


def test_empty_success_output_is_accepted():
    ble = make_ble((b"", b"", 0))

    result = ble._sendCommand_internal("TESTVIN", "charging-set-amps", 6)

    assert result == "ok"
    command = ble._run_command_with_timeout.call_args.args[0]
    assert "-debug" not in command


def test_command_timeout_override_is_forwarded_to_runner():
    ble = make_ble((b"", b"", 0))

    result = ble._sendCommand_internal("TESTVIN", "charging-stop", timeout=3)

    assert result == "ok"
    assert ble._run_command_with_timeout.call_args.kwargs["timeout"] == 3


def test_set_charge_rate_converts_vehicle_object_to_vin():
    ble = TeslaBLE.__new__(TeslaBLE)
    ble.wakeVehicle = Mock(return_value=True)
    ble.sendCommand = Mock(return_value="ok")
    ble.parseCommandOutput = Mock(return_value=True)
    vehicle = Mock()
    vehicle.VIN = "TESTVIN"

    result = ble.setChargeRate(16, vehicle)

    assert result is True
    ble.wakeVehicle.assert_called_once_with("TESTVIN")
    ble.sendCommand.assert_called_once_with("TESTVIN", "charging-set-amps", 16)


def test_stop_uses_one_short_ble_attempt_before_api_fallback():
    ble = TeslaBLE.__new__(TeslaBLE)
    ble.stopCommandTimeout = 15
    ble.sendCommand = Mock(return_value="ok")
    ble.parseCommandOutput = Mock(return_value=True)

    result = ble.stopCharging("TESTVIN")

    assert result is True
    ble.sendCommand.assert_called_once_with(
        "TESTVIN", "charging-stop", retries=0, timeout=15
    )


def test_untargeted_stop_fails_when_any_vehicle_stop_fails():
    ble = TeslaBLE.__new__(TeslaBLE)
    ble.master = Mock()
    ble.master.settings = {"Vehicles": {"VIN_A": {}, "VIN_B": {}}}
    ble._stopAskingToStartCharging = {}
    ble.stopCharging = Mock(side_effect=[True, False])

    result = ble.car_api_charge({"charge": False})

    assert result is False
    assert ble.stopCharging.call_count == 2
