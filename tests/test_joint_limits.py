import math
import pytest

from robot.joint import Joint, JointType
from robot.limits import JointLimitError, JointLimits


def test_joint_accepts_inclusive_limits():
    joint = Joint("J1", JointType.REVOLUTE, JointLimits(-math.pi, math.pi))
    joint.set_position(math.pi)
    assert joint.current_degrees == pytest.approx(180.0)


def test_joint_rejects_target_outside_limits():
    joint = Joint("J0", JointType.PRISMATIC, JointLimits(0, 2000))
    with pytest.raises(JointLimitError, match="J0 target"):
        joint.set_position(2000.1)
