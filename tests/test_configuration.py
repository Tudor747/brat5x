from pathlib import Path
import pytest

from config_loader import load_printer_configs
from motion.taught_pose import load_taught_poses


ROOT = Path(__file__).resolve().parents[1]


def test_taught_pose_loading_converts_degrees_and_validates(robot):
    poses = load_taught_poses(ROOT / "config" / "taught_poses.yaml", robot)
    assert poses["PRINTER_2_APPROACH"].rail_mm == 1200
    assert poses["PRINTER_2_APPROACH"].joints_deg == pytest.approx((20.0, 35.0, -40.0, 15.0, 90.0))


def test_printer_configuration_supports_arbitrary_count():
    printers = load_printer_configs(ROOT / "config" / "printers.yaml")
    assert len(printers) == 3
    assert printers[1].position_mm == (1200.0, 400.0, 0.0)
    assert not printers[2].enabled
