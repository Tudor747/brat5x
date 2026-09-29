"""Geometry-independent numerical Jacobian."""

from __future__ import annotations

from collections.abc import Sequence
import numpy as np
from numpy.typing import NDArray

from kinematics.forward_kinematics import ForwardKinematics


def numerical_jacobian(
    fk: ForwardKinematics,
    q: Sequence[float],
    epsilon: float = 1e-6,
) -> NDArray[np.float64]:
    """Return a 6xN central-difference geometric Jacobian.

    Rows 0:3 are TCP translation and rows 3:6 are the small-angle rotation
    vector. Columns use each joint's native unit (mm for J0, radians otherwise).
    """
    q_array = np.asarray(q, dtype=float)
    result = np.zeros((6, len(q_array)), dtype=float)
    for index in range(len(q_array)):
        plus, minus = q_array.copy(), q_array.copy()
        plus[index] += epsilon
        minus[index] -= epsilon
        t_plus, t_minus = fk.transform(plus), fk.transform(minus)
        result[:3, index] = (t_plus[:3, 3] - t_minus[:3, 3]) / (2.0 * epsilon)
        r_dot = (t_plus[:3, :3] - t_minus[:3, :3]) / (2.0 * epsilon)
        omega_hat = r_dot @ fk.transform(q_array)[:3, :3].T
        result[3:, index] = (omega_hat[2, 1], omega_hat[0, 2], omega_hat[1, 0])
    return result
