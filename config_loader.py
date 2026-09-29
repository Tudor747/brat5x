"""Centralized YAML loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import math
import yaml

from printers.printer_base import PrinterConfig
from robot.joint import Joint, JointType
from robot.limits import JointLimits
from robot.robot_model import JointKinematicSpec, RobotModel


def _read_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def _vector(mapping: dict[str, Any], key: str) -> tuple[float, float, float]:
    values = mapping.get(key, [0.0, 0.0, 0.0])
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError(f"{key} must be a three-element list")
    return tuple(float(value) for value in values)  # type: ignore[return-value]


def _rpy(mapping: dict[str, Any]) -> tuple[float, float, float]:
    return tuple(math.radians(value) for value in _vector(mapping, "rpy_deg"))  # type: ignore[return-value]


def load_robot_config(path: str | Path) -> RobotModel:
    root = _read_yaml(path).get("robot")
    if not isinstance(root, dict):
        raise ValueError("robot configuration requires a 'robot' mapping")

    rail = root["rail"]
    rail_motor = rail.get("motor", {})
    joints = [
        Joint(
            name=str(rail.get("name", "J0")),
            joint_type=JointType.PRISMATIC,
            limits=JointLimits(float(rail["min_mm"]), float(rail["max_mm"])),
            home_position=float(rail.get("home_mm", 0.0)),
            current_position=float(rail.get("home_mm", 0.0)),
            gear_ratio=rail_motor.get("gear_ratio"),
            steps_per_revolution=rail_motor.get("steps_per_revolution"),
            microstepping=rail_motor.get("microstepping"),
        )
    ]
    rotary = root["joints"]
    for name in ("J1", "J2", "J3", "J4", "J5"):
        item = rotary[name]
        motor = item.get("motor", {})
        home = math.radians(float(item.get("home_deg", 0.0)))
        joints.append(
            Joint(
                name=name,
                joint_type=JointType(item["type"]),
                limits=JointLimits(math.radians(float(item["min_deg"])), math.radians(float(item["max_deg"]))),
                home_position=home,
                current_position=home,
                gear_ratio=motor.get("gear_ratio"),
                steps_per_revolution=motor.get("steps_per_revolution"),
                microstepping=motor.get("microstepping"),
            )
        )

    kinematics = root["kinematics"]
    chain: list[JointKinematicSpec] = []
    for item in kinematics["rotary_chain"]:
        before, after = item["pre_transform"], item["post_transform"]
        chain.append(
            JointKinematicSpec(
                joint_name=str(item["joint"]),
                axis=str(item["axis"]),
                pre_translation_mm=_vector(before, "translation_mm"),
                pre_rpy_rad=_rpy(before),
                post_translation_mm=_vector(after, "translation_mm"),
                post_rpy_rad=_rpy(after),
            )
        )
    tcp = kinematics["tcp_transform"]
    return RobotModel(
        name=str(root["name"]),
        joints=joints,
        kinematic_chain=chain,
        tcp_translation_mm=_vector(tcp, "translation_mm"),
        tcp_rpy_rad=_rpy(tcp),
        metadata={"source": str(path), "placeholder_geometry": True},
    )


def load_printer_configs(path: str | Path) -> list[PrinterConfig]:
    configured = _read_yaml(path).get("printers")
    if not isinstance(configured, dict):
        raise ValueError("printer configuration requires a 'printers' mapping")
    result: list[PrinterConfig] = []
    for name, item in configured.items():
        position = item["position"]
        result.append(
            PrinterConfig(
                name=str(name),
                enabled=bool(item.get("enabled", True)),
                host=str(item["host"]),
                interface=str(item["interface"]),
                position_mm=(float(position["x_mm"]), float(position["y_mm"]), float(position["z_mm"])),
                safe_bed_temperature_c=float(item["safe_bed_temperature_c"]),
            )
        )
    return result
