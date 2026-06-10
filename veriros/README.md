# VeriROS Runtime Structure

VeriROS connects offline SMT schedules to runtime assurance evidence in ROS 2.
The directories in this package mirror the paper architecture.

## Components

- `ros2_nodes/`: integration notes for ROS 2 nodes.
- `schedule_follower/`: executes `schedule.json` task assignments.
- `resource_manager/`: enforces SMT-proven shared-resource ordering.
- `safety_fence/`: stops robots before entering configured hazard zones.
- `stl_monitor/`: evaluates runtime STL properties and robustness values.
- `audit/`: records schedules, traces, mutex logs, solver outputs, and violation reports.

The current repository contains the scheduling and artifact-generation core.
The ROS 2 directories document the runtime decomposition and provide stable
locations for implementation files as the prototype is expanded.

