from pathlib import Path
import pytest

from config_loader import load_printer_configs
from controller.safety import SafetyManager, SafetyViolation
from controller.state_machine import RobotState, RobotStateMachine
from hardware.mock_controller import MockController
from motion.taught_pose import load_taught_poses
from printers.mock_printer import MockPrinter
from printers.printer_manager import PrinterManager


ROOT = Path(__file__).resolve().parents[1]


def make_machine(robot):
    config = load_printer_configs(ROOT / "config" / "printers.yaml")[1]
    printer = MockPrinter(config)
    controller = MockController(robot)
    poses = load_taught_poses(ROOT / "config" / "taught_poses.yaml", robot)
    machine = RobotStateMachine(PrinterManager([printer]), controller, SafetyManager(robot), poses)
    return machine, printer, controller


def test_finished_printer_waits_for_cooling_then_completes_workflow(robot):
    machine, printer, _ = make_machine(robot)
    printer.start_print("test.gcode")
    printer.finish_print(60.0)
    printer.begin_cooling()
    assert machine.tick() is RobotState.WAITING_FOR_JOB
    assert machine.tick() is RobotState.PRINT_FINISHED
    assert machine.tick() is RobotState.WAITING_FOR_BED_COOLING
    assert machine.tick() is RobotState.WAITING_FOR_BED_COOLING
    printer.cool_to(34.0)
    assert machine.tick() is RobotState.MOVING_TO_PRINTER
    visited = set()
    for _ in range(10):
        visited.add(machine.tick())
        if machine.state is RobotState.IDLE:
            break
    assert RobotState.PUSHING_PRINT in visited
    assert RobotState.RETURNING_HOME in visited
    assert machine.state is RobotState.IDLE
    assert printer.print_name is None
    assert robot.q.tolist() == robot.home_q.tolist()


def test_emergency_stop_latches_and_refuses_motion(robot):
    machine, _, controller = make_machine(robot)
    machine.emergency_stop()
    assert machine.state is RobotState.EMERGENCY_STOP
    with pytest.raises(SafetyViolation, match="emergency stop"):
        machine.safety.validate_motion(robot.home_q, controller)
    assert machine.tick() is RobotState.EMERGENCY_STOP


def test_busy_controller_refuses_second_movement(robot):
    machine, _, controller = make_machine(robot)
    controller.set_simulated_busy(True)
    with pytest.raises(SafetyViolation, match="another movement"):
        machine.safety.validate_motion(robot.home_q, controller)
