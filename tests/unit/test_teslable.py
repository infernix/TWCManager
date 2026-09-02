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
