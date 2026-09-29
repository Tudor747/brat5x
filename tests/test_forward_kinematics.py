import numpy as np

from kinematics.forward_kinematics import ForwardKinematics


def test_fk_returns_full_homogeneous_transform(robot):
    transform = ForwardKinematics(robot).transform(robot.home_q)
    assert transform.shape == (4, 4)
    assert np.allclose(transform[3], [0, 0, 0, 1])
    assert np.allclose(transform[:3, :3].T @ transform[:3, :3], np.eye(3))


def test_fk_is_deterministic_and_does_not_mutate_robot(robot):
    fk = ForwardKinematics(robot)
    q = np.asarray([250.0, 0.2, -0.3, 0.4, -0.1, 0.5])
    before = robot.q.copy()
    assert np.allclose(fk.transform(q), fk.transform(q))
    assert np.allclose(robot.q, before)


def test_rail_axis_translates_tcp_only_along_world_x(robot):
    fk = ForwardKinematics(robot)
    at_home = fk.transform(robot.home_q)
    displaced = robot.home_q.copy()
    displaced[0] = 321.0
    delta = displaced[0] - robot.home_q[0]
    assert np.allclose(fk.transform(displaced)[:3, 3] - at_home[:3, 3], [delta, 0, 0])
