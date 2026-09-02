import json
from unittest.mock import Mock, patch


def make_vehicle(vin):
    vehicle = Mock()
    vehicle.VIN = vin
    vehicle.name = vin
    vehicle.ready.return_value = True
    vehicle.update_charge.return_value = True
    vehicle.update_location.return_value = True
    vehicle.batteryLevel = 70
    vehicle.chargeLimit = 80
    vehicle.atHome = True
    vehicle.chargingState = "Charging"
    vehicle.scheduledChargingPending = False
    vehicle.stopAskingToStartCharging = False
    vehicle.firstChargeNeededTime = 1
    vehicle.firstWakeAttemptTime = 1
    vehicle.delayNextWakeAttempt = 1
    return vehicle


def make_api(vehicles, last_command_time=0):
    from TWCManager.Vehicle.TeslaAPI import TeslaAPI

    api = TeslaAPI.__new__(TeslaAPI)
    api.getLastStartOrStopChargeTime = Mock(return_value=last_command_time)
    api.car_api_available = Mock(return_value=True)
    api.getCarApiVehicles = Mock(return_value=vehicles)
    api.minChargeLevel = 20
    api.lastChargeLimitApplied = -1
    api.updateLastStartOrStopChargeTime = Mock()
    api.baseURL = "https://fleet-api.example/vehicles"
    api.getCarApiBearerToken = Mock(return_value="token")
    api.verifyCert = True
    api.config = {"config": {"respectVehicleSchedule": True}}
    api.resetCarApiLastErrorTime = Mock()
    api.updateCarApiLastErrorTime = Mock()
    return api


def test_stop_targets_only_requested_vin_and_bypasses_start_cooldown():
    target = make_vehicle("VIN_A")
    other = make_vehicle("VIN_B")
    api = make_api([target, other], last_command_time=90)
    response = Mock(text=json.dumps({"response": {"result": True, "reason": ""}}))

    with patch("TWCManager.Vehicle.TeslaAPI.time.time", return_value=100), patch(
        "TWCManager.Vehicle.TeslaAPI.time.sleep"
    ), patch("TWCManager.Vehicle.TeslaAPI.requests.post", return_value=response) as post:
        result = api.car_api_charge(
            {"cmd": "charge", "charge": False, "vin": "VIN_A"}
        )

    assert result == "success"
    api.car_api_available.assert_called_once_with(charge=False, vin="VIN_A")
    post.assert_called_once()
    assert "/VIN_A/command/charge_stop" in post.call_args.args[0]
    target.update_charge.assert_called_once()
    other.update_charge.assert_not_called()
    assert target.firstChargeNeededTime == 0
    assert other.firstChargeNeededTime == 1


def test_targeted_stop_fails_when_api_has_no_matching_vin():
    api = make_api([make_vehicle("VIN_B")])

    with patch("TWCManager.Vehicle.TeslaAPI.time.time", return_value=100):
        result = api.car_api_charge(
            {"cmd": "charge", "charge": False, "vin": "VIN_A"}
        )

    assert result == "error"


def test_targeted_stop_reports_error_when_vehicle_is_not_ready():
    target = make_vehicle("VIN_A")
    target.ready.return_value = False
    api = make_api([target])

    with patch("TWCManager.Vehicle.TeslaAPI.time.time", return_value=100):
        result = api.car_api_charge(
            {"cmd": "charge", "charge": False, "vin": "VIN_A"}
        )

    assert result == "error"
