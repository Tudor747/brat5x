from __future__ import annotations

from pathlib import Path
import pytest

from config_loader import load_robot_config


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def robot():
    return load_robot_config(ROOT / "config" / "robot.yaml")
