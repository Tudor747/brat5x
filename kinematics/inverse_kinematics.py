"""Future inverse-kinematics interface."""

from __future__ import annotations

from collections.abc import Sequence

from robot.pose import Pose


def solve_ik(target_pose: Pose, initial_guess: Sequence[float]) -> list[float]:
    """Solve for q once geometry has been validated against CAD.

    Future implementations may use a Jacobian pseudo-inverse, damped least
    squares, or bounded numerical optimization. No solution is fabricated now.
    """
    raise NotImplementedError("inverse kinematics is intentionally deferred")
