"""Text demonstration of the phase-one robotic print-farm workflow."""

from __future__ import annotations

import logging
from pathlib import Path

from config_loader import load_printer_configs, load_robot_config
from controller.safety import SafetyManager
from controller.state_machine import RobotState, RobotStateMachine
from hardware.mock_controller import MockController
from kinematics.forward_kinematics import ForwardKinematics
from motion.taught_pose import load_taught_poses
from printers.mock_printer import MockPrinter
from printers.printer_manager import PrinterManager


ROOT = Path(__file__).resolve().parent


def build_demo() -> tuple[RobotStateMachine, dict[str, MockPrinter], ForwardKinematics]:
    robot = load_robot_config(ROOT / "config" / "robot.yaml")
    poses = load_taught_poses(ROOT / "config" / "taught_poses.yaml", robot)
    printer_list = [MockPrinter(config) for config in load_printer_configs(ROOT / "config" / "printers.yaml")]
    printers = {printer.config.name: printer for printer in printer_list}
    manager = PrinterManager(printer_list)
    controller = MockController(robot)
    machine = RobotStateMachine(manager, controller, SafetyManager(robot), poses)
    return machine, printers, ForwardKinematics(robot)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    machine, printers, fk = build_demo()

    printers["printer_1"].start_print("printer-bracket.gcode")
    printers["printer_1"].set_progress(42.0)
    printers["printer_2"].start_print("robot-gripper.gcode")
    printers["printer_2"].finish_print(bed_temperature_c=58.0)
    printers["printer_2"].begin_cooling()

    # Reach the cooling wait, then simulate the bed crossing its safe threshold.
    for _ in range(4):
        machine.tick()
    printers["printer_2"].cool_to(34.5)

    for _ in range(20):
        machine.tick()
        if machine.state is RobotState.IDLE and printers["printer_2"].print_name is None:
            break

    pose = fk.pose()
    logging.info("[FK] Final TCP position = (%.1f, %.1f, %.1f) mm", pose.x, pose.y, pose.z)
    logging.info("[DEMO] Printer 1 continues printing; printer 2 was serviced")


if __name__ == "__main__":
    main()
