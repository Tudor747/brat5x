# Mini conceptual simulation

This folder is deliberately separate from the controller. It visualizes workflow,
not robot physics, collision, reachability, timing, or the eventual CAD geometry.

From the repository root:

```bash
python mini_simulation/run_simulation.py
```

The scene reads rail and enabled-printer positions from the main YAML files. Add a
printer there and it appears automatically. `demo_sequence.py` owns the state
keyframes, `simple_robot.py` owns the deliberately schematic arm, and `scene.py`
owns drawing. Use `--no-show` for a headless smoke check or `--save demo.gif` to
save an animation when Pillow is installed.
