# Rail-Mounted Robotic Print Farm — Phase 1

This repository is the initial high-level software foundation for a five-rotary-
joint arm carried by a linear rail. It demonstrates configuration, forward
kinematics (FK), taught joint poses, printer abstraction, supervisory safety,
mock motion, a service state machine, tests, and a separate conceptual animation.

It is **not a production robot controller**. All current geometry, joint limits,
printer locations, temperatures, and taught poses are explicitly placeholder
values. Nothing here establishes that a physical pose is reachable or collision-
free. Do not connect this code directly to stepper drivers.

## Repository layout

```text
.
├── README.md
├── requirements.txt
├── main.py
├── config_loader.py
├── config/
│   ├── robot.yaml
│   ├── printers.yaml
│   └── taught_poses.yaml
├── robot/
│   ├── joint.py
│   ├── limits.py
│   ├── pose.py
│   └── robot_model.py
├── kinematics/
│   ├── transforms.py
│   ├── forward_kinematics.py
│   ├── inverse_kinematics.py
│   ├── jacobian.py
│   └── dh.py
├── motion/
│   ├── motion_command.py
│   ├── taught_pose.py
│   └── trajectory.py
├── controller/
│   ├── state_machine.py
│   ├── scheduler.py
│   └── safety.py
├── printers/
│   ├── printer_base.py
│   ├── mock_printer.py
│   └── printer_manager.py
├── hardware/
│   ├── controller_interface.py
│   └── mock_controller.py
├── tests/
│   ├── conftest.py
│   ├── test_configuration.py
│   ├── test_forward_kinematics.py
│   ├── test_joint_limits.py
│   ├── test_state_machine.py
│   └── test_transforms.py
└── mini_simulation/
    ├── README.md
    ├── requirements.txt
    ├── run_simulation.py
    ├── simple_robot.py
    ├── scene.py
    └── demo_sequence.py
```

`config_loader.py` is intentionally centralized: YAML schema interpretation and
degree-to-radian conversion should not leak into kinematics, control, or hardware
code. `inverse_kinematics.py` is present as a documented seam and deliberately
raises `NotImplementedError`.

## Architecture and responsibility boundary

```text
  3D Printers (mock now; Moonraker / OctoPrint / Marlin later)
                              |
                              v
                     Printer Manager
                              |
                              v
                     Printer Scheduler
                              |
                              v
                    Robot State Machine
                    /        |         \
                   v         v          v
          Safety Manager  Taught Poses  Kinematics
                   \         |          /
                    \        v         /
                     Controller Interface
                              |
                        MockController now
                              |
                    Serial / CAN adapter later
                              |
                              v
                       MCU real-time layer
                              |
                              v
                    STEP/DIR motor drivers
```

The PC or Raspberry Pi layer owns configuration, printer status, service policy,
FK/IK, future trajectory planning, logging, and supervisory safety decisions. A
future STM32, Teensy, or ESP32 must own deterministic STEP/DIR timing,
acceleration profiles, homing, endstop sampling, emergency-stop inputs, and joint
position counters. The `ControllerInterface` is the boundary between these two
timing domains.

The mock controller completes each MOVEJ synchronously and updates joint state.
It does not model time, dynamics, backlash, missed steps, or communication.

## Coordinates, units, and joints

The world convention is:

- +X: along the rail
- +Y: from the rail toward the printers
- +Z: vertical

The generalized coordinate vector is:

```text
q = [rail_mm, J1_rad, J2_rad, J3_rad, J4_rad, J5_rad]
```

J0 is prismatic on world X. J1–J5 are revolute. Internal distances are
millimetres and internal angles are radians. Configuration and taught poses allow
degrees for convenient human editing and convert them exactly once when loaded.

Each `Joint` holds its type, current/home positions, limits, and optional motor
metadata. Gear ratio, motor steps/revolution, and microstepping are intentionally
not referenced by FK; encoder/step conversion belongs in a future low-level
controller adapter.

## Forward kinematics

FK evaluates the configured chain:

```text
T_world_tcp = T_rail
            * T_pre_J1 * R_J1 * T_post_J1
            * ...
            * T_pre_J5 * R_J5 * T_post_J5
            * T_tcp
```

The result is a 4×4 homogeneous transform and can be exposed as a `Pose` with a
millimetre position and 3×3 rotation matrix. The implementation uses explicit
fixed transforms and configured joint axes instead of making DH parameters the
primary model. At this stage explicit frames are easier to compare directly with
CAD assemblies, preserve arbitrary mounting rotations, and avoid silently
choosing incompatible DH frame conventions. A standard-DH matrix utility remains
available for later model comparison.

Every pre/post frame, joint axis, and TCP transform lives in `config/robot.yaml`.
The current numbers are examples only. The numerical Jacobian is a small,
independent diagnostic building block; it is not yet an IK solver.

## Why inverse kinematics is postponed

IK depends on correct joint axes, zero conventions, link transforms, TCP, limits,
and reachability. Those are not known until the CAD model is measured and the FK
model is experimentally validated. Returning a plausible-looking solution now
would create false confidence. The existing `solve_ik(target_pose,
initial_guess)` interface explicitly raises `NotImplementedError`; a later phase
can implement bounded damped least squares or numerical optimization and validate
it against FK and hardware.

## Taught poses and motion commands

`config/taught_poses.yaml` provides HOME plus RAIL, APPROACH, PUSH_START, and
PUSH_END joint configurations per printer. This makes a first prototype possible
without Cartesian IK. Each pose is converted to native units and checked against
joint limits during loading; commands are checked again before execution.

MOVEJ has a concrete joint-target command and a basic joint interpolation
container. MOVEL is only a declaration because safe Cartesian motion needs valid
IK, trajectory limits, singularity handling, and collision checking.

## Printer abstraction and scheduling

`PrinterInterface` exposes state, progress, temperature, print name, refresh, and
removal acknowledgement. `MockPrinter` implements the interface with these
states: IDLE, PRINTING, FINISHED, COOLING, READY_FOR_REMOVAL, and ERROR. A future
Moonraker, OctoPrint, or serial-Marlin adapter can implement the same interface
without changing the robot state machine.

The printer YAML is a mapping with no hard-coded count. Disabled entries are
loaded but omitted from `PrinterManager`. The current scheduler selects the first
configured waiting printer. Priority, fairness, travel-cost optimization, and
job awareness belong in a later scheduler implementation.

## State machine

The supervisory sequence is:

```text
IDLE -> WAITING_FOR_JOB -> PRINT_FINISHED
                              |
                              v
                  WAITING_FOR_BED_COOLING
                              |
                              v
MOVING_TO_PRINTER -> MOVING_TO_APPROACH -> PUSHING_PRINT
                                                |
                                                v
                  IDLE <- RETURNING_HOME <- RETRACTING
```

ERROR and EMERGENCY_STOP are terminal until an explicit recovery/reset action.
Each tick performs at most one state action, except PUSHING_PRINT issues the
configured synchronous PUSH_START and PUSH_END MOVEJ pair. That simplification
must change when the controller becomes asynchronous.

Before motion, `SafetyManager` checks limits, the emergency-stop latch, and the
controller busy flag. It separately refuses a push unless the printer reports
READY_FOR_REMOVAL and its bed is at or below the configured safe temperature.
Transitions, printer changes, motion commands, rejections, and safety events use
Python logging.

Software checks are not safety-rated. A physical machine needs, at minimum, a
hardwired emergency stop, hardware endstops, mechanical stops, motor-current
limits, a power-disconnect path, suitable guarding/interlocks, and a documented
risk assessment. These cannot be replaced by Python.

## Install and run

Python 3.11 or newer is required.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest
.venv\Scripts\python main.py
.venv\Scripts\python mini_simulation\run_simulation.py
```

On macOS/Linux, replace `.venv\Scripts\python` with `.venv/bin/python`.

The text demo leaves printer 1 printing, moves printer 2 through finished and
cooling states, makes it safe, services it through taught poses, returns HOME,
and prints the final placeholder FK position.

The Matplotlib mini simulation is a top-view educational sketch. It shows the
rail, carriage, schematic arm, enabled printers and beds, end effector, and a
printed part moving off printer 2. It reuses configured rail/printer positions
but makes no claim about CAD geometry or physics. See `mini_simulation/README.md`.

## Current assumptions and technical debt

- All configured mechanics and poses are placeholders and are uncalibrated.
- Mock motion is instantaneous and blocking; a real transport needs command IDs,
  acknowledgement, timeouts, progress, cancellation, and reconnect behavior.
- The push is two MOVEJ targets, not a straight Cartesian/tool-normal path.
- Printer readiness trusts one reported state and temperature; production logic
  needs sensor validity, stale-data timeouts, printer motion/bed-clear checks, and
  recovery rules.
- The scheduler is deterministic first-ready selection and is not persistent.
- There is no velocity/acceleration/jerk enforcement, singularity analysis,
  collision model, payload model, calibration database, or safety PLC.
- The YAML loader validates required structure and limits but does not yet use a
  versioned formal schema.
- The numerical Jacobian uses finite differences and is intended for diagnostics,
  not real-time control.
- State recovery from ERROR is intentionally undefined until failure modes and
  physical reset procedures are known.

## CAD data required before accurate FK

Provide the following in one consistent coordinate system, ideally as both a CAD
assembly and a table of transforms:

1. **World and rail datum:** the world origin, rail centerline, +X direction,
   carriage home/zero location, usable travel, and transform from rail carriage
   mounting face to the robot-base mounting frame.
2. **Every rotary joint frame at mechanical zero:** J1–J5 origin XYZ and rotation
   relative to its parent frame, plus the positive rotation direction. A joint
   axis unit vector and a recognizable datum plane/feature are especially useful.
3. **Zero-angle definition:** physical witness marks or CAD configurations that
   define q=0 for every joint, including encoder/step home offsets. Motor shaft
   zero is not necessarily kinematic zero.
4. **Full inter-frame transforms:** translations and rotations between successive
   joint frames—not only scalar link lengths. Include lateral offsets, axis
   twists, bracket thicknesses, eccentricities, and wrist/flange offsets.
5. **TCP/tool geometry:** transform from J5/tool flange to the intended TCP,
   pusher contact edge/face, tool orientation, and any interchangeable-tool
   mounting repeatability.
6. **Limits:** verified hard-stop limits, usable software limits with margin,
   homing direction, and any configuration-dependent restrictions. Supply angles
   in a named convention and rail positions from the declared datum.
7. **Printer frames:** transform from world to each printer base and bed frame;
   bed plane, usable bed polygon/corners, build-surface height, door/frame
   obstructions, and expected part-removal direction.
8. **Collision envelopes:** simplified meshes or bounding geometry for robot
   links, carriage, rail, tool, printers, beds, guarding, cable chains, and other
   fixed obstacles, including desired clearance margins.
9. **Validation poses:** several non-singular measured joint configurations with
   corresponding TCP positions/orientations measured independently. These are
   needed to catch frame sign, axis, and zero-offset mistakes.
10. **Tolerance context:** CAD units, nominal versus as-built dimensions, joint
    backlash/compliance estimates, and the required TCP position/orientation
    accuracy for a successful push.

Gear ratios, pulley pitch, steps/revolution, microstepping, encoder scaling, and
motion limits will be required for hardware actuation, but they do not determine
FK geometry.

## Roadmap

- **Phase 2:** import real CAD dimensions/frames and validate FK.
- **Phase 3:** numerical IK, Jacobian validation, and damped least squares.
- **Phase 4:** Cartesian trajectory planning and a real MOVEL.
- **Phase 5:** MCU protocol, serial/CAN adapter, homing, and endstop integration.
- **Phase 6:** Moonraker/Klipper and OctoPrint adapters.
- **Phase 7:** persistent multi-printer scheduling and recovery.
- **Phase 8:** self/environment collision checking.
- **Phase 9:** evaluate ROS 2/MoveIt once geometry and operational needs justify it.
- **Phase 10:** experimental validation, uncertainty analysis, and scientific
  documentation.
