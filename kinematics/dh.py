"""Optional standard Denavit-Hartenberg primitive.

The prototype FK intentionally uses explicit transforms. This utility is kept for
future comparison with a CAD-derived DH model.
"""

from __future__ import annotations

import math
import numpy as np
from numpy.typing import NDArray


def standard_dh(a_mm: float, alpha_rad: float, d_mm: float, theta_rad: float) -> NDArray[np.float64]:
    ct, st = math.cos(theta_rad), math.sin(theta_rad)
    ca, sa = math.cos(alpha_rad), math.sin(alpha_rad)
    return np.asarray(
        [
            [ct, -st * ca, st * sa, a_mm * ct],
            [st, ct * ca, -ct * sa, a_mm * st],
            [0.0, sa, ca, d_mm],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
