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
