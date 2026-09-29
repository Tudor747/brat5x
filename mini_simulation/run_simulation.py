"""Run the conceptual Matplotlib animation."""

from __future__ import annotations

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from demo_sequence import interpolate_sequence
from scene import SceneData, SimulationScene


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", type=Path, help="Optionally save as GIF (requires Pillow)")
    parser.add_argument("--no-show", action="store_true", help="Build the animation without opening a window")
    parser.add_argument("--frames-per-stage", type=int, default=24)
    args = parser.parse_args()

    data = SceneData.from_configs(ROOT / "config" / "robot.yaml", ROOT / "config" / "printers.yaml")
    target_x = data.printer(data.serviced_printer).x_mm
    frames = interpolate_sequence(data.rail_min_mm, target_x, args.frames_per_stage)
    figure, axes = plt.subplots(figsize=(12, 5.5))
    scene = SimulationScene(axes, data)
    animation = FuncAnimation(figure, scene.update, frames=frames, interval=55, blit=True, repeat=True)

    if args.save:
        animation.save(args.save, writer="pillow", fps=18)
    if not args.no_show:
        plt.show()
    else:
        # Render once so headless smoke runs validate the scene and update path.
        scene.update(frames[-1])
        plt.close(figure)


if __name__ == "__main__":
    main()
