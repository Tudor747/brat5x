import math
import numpy as np

from kinematics.transforms import (
    homogeneous_transform,
    rotation_x,
    rotation_y,
    rotation_z,
    transform_point,
    translation_x,
    translation_y,
    translation_z,
)


def test_translation_matrices_move_expected_axes():
    combined = translation_x(10) @ translation_y(20) @ translation_z(30)
    assert np.allclose(combined[:3, 3], [10, 20, 30])
    assert np.allclose(combined[3], [0, 0, 0, 1])


def test_rotation_matrices_are_right_handed_and_orthonormal():
    for rotation in (rotation_x(math.pi / 2), rotation_y(math.pi / 2), rotation_z(math.pi / 2)):
        assert np.allclose(rotation[:3, :3].T @ rotation[:3, :3], np.eye(3))
        assert np.isclose(np.linalg.det(rotation[:3, :3]), 1.0)
    assert np.allclose(transform_point(rotation_z(math.pi / 2), [1, 0, 0]), [0, 1, 0], atol=1e-12)


def test_homogeneous_transform_and_point_application():
    matrix = homogeneous_transform(rotation_z(math.pi / 2), [10, 20, 30])
    assert matrix.shape == (4, 4)
    assert np.allclose(transform_point(matrix, [1, 0, 0]), [10, 21, 30])
