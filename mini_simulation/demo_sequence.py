"""Conceptual state keyframes, independent of Matplotlib."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoFrame:
    state: str
    carriage_x_mm: float
    arm_extension: float
    part_offset_mm: float


@dataclass(frozen=True)
class Keyframe:
    state: str
    carriage_x_mm: float
    arm_extension: float
    part_offset_mm: float


def interpolate_sequence(home_x: float, printer_x: float, frames_per_stage: int = 24) -> list[DemoFrame]:
    if frames_per_stage < 2:
        raise ValueError("frames_per_stage must be at least 2")
    keyframes = [
        Keyframe("HOME", home_x, 0.0, 0.0),
        Keyframe("MOVING_TO_PRINTER", printer_x, 0.0, 0.0),
        Keyframe("MOVING_TO_APPROACH", printer_x, 0.80, 0.0),
        Keyframe("PUSHING_PRINT", printer_x, 1.0, 150.0),
        Keyframe("RETRACTING", printer_x, 0.0, 150.0),
        Keyframe("RETURNING_HOME", home_x, 0.0, 150.0),
        Keyframe("IDLE", home_x, 0.0, 150.0),
    ]
    frames: list[DemoFrame] = []
    for start, end in zip(keyframes, keyframes[1:]):
        for index in range(frames_per_stage):
            alpha = index / (frames_per_stage - 1)
            frames.append(
                DemoFrame(
                    end.state,
                    start.carriage_x_mm + alpha * (end.carriage_x_mm - start.carriage_x_mm),
                    start.arm_extension + alpha * (end.arm_extension - start.arm_extension),
                    start.part_offset_mm + alpha * (end.part_offset_mm - start.part_offset_mm),
                )
            )
    return frames
