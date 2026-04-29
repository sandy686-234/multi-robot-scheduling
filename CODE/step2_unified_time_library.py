#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from typing import Tuple, Union, Optional
from dataclasses import dataclass


# ============================================================
# CONSTANTS
# ============================================================

class TimeUnits:
    UNIT_NAME = "seconds"
    EPSILON = 1e-9  # epsilon for floating point comparisons

    @staticmethod
    def validate_unit(description: str) -> None:
        print(f"[TIME UNIT] {description} (unit: {TimeUnits.UNIT_NAME})")


class SpatialUnits:
    UNIT_NAME = "meters"

    @staticmethod
    def validate_unit(description: str) -> None:
        print(f"[SPATIAL UNIT] {description} (unit: {SpatialUnits.UNIT_NAME})")


class SpeedUnits:
    UNIT_NAME = "meters_per_second"  # m/s

    @staticmethod
    def validate_unit(description: str) -> None:
        print(f"[SPEED UNIT] {description} (unit: {SpeedUnits.UNIT_NAME})")


# ============================================================
# TIME COMPARISON
# ============================================================

class TimeComparison:
    """
    All time comparisons should use this class to ensure consistency.

    Per semantic definition §Numerical Precision:
    "Do NOT round intermediate results"
    "For time comparisons always use epsilon = 1e-9"
    """

    EPS = TimeUnits.EPSILON  # 1e-9 seconds

    @staticmethod
    def leq(t1: float, t2: float, eps: float = EPS) -> bool:
        """Check t1 <= t2 (with epsilon tolerance).

        Returns:
            bool: t1 <= t2 + eps

        Usage:
            if TimeComparison.leq(task_end_time, deadline):
                print("Task meets deadline")
        """
        return t1 <= t2 + eps

    @staticmethod
    def geq(t1: float, t2: float, eps: float = EPS) -> bool:
        """Check t1 >= t2 (with epsilon tolerance)."""
        return t1 >= t2 - eps

    @staticmethod
    def eq(t1: float, t2: float, eps: float = EPS) -> bool:
        """Check t1 == t2 (with epsilon tolerance)."""
        return abs(t1 - t2) <= eps

    @staticmethod
    def gt(t1: float, t2: float, eps: float = EPS) -> bool:
        """Check t1 > t2 (with epsilon tolerance)."""
        return t1 > t2 + eps

    @staticmethod
    def lt(t1: float, t2: float, eps: float = EPS) -> bool:
        """Check t1 < t2 (with epsilon tolerance)."""
        return t1 < t2 - eps


# ============================================================
# TRAVEL TIME CALCULATION
# ============================================================

class TravelTimeCalculator:
    """
    Unified travel time calculator.

    Function Signature: travel_time(p1: Location, p2: Location, robot: Robot) -> Time

    DEFINITION:
      Travel time is the minimum time required for a robot to move from
      location p1 to location p2, given the robot's maximum speed.

    COMPUTATION:
      distance = sqrt((p2.x - p1.x)^2 + (p2.y - p1.y)^2)  [meters]
      speed = max(robot.max_speed, EPSILON)  [m/s]
      travel_time = distance / speed  [seconds]

    OUTPUT:
      float: Pure travel time, WITHOUT any setup/service/overhead
      Units: seconds
      Precision: IEEE 754 double precision
    """

    EPSILON_SPEED = 1e-9  # m/s, prevent division by zero

    @staticmethod
    def euclidean_distance(p1: Tuple[float, float],
                           p2: Tuple[float, float]) -> float:
        """Compute Euclidean distance between two points.

        Args:
            p1: (x, y) position in meters
            p2: (x, y) position in meters

        Returns:
            float: distance in meters
        """
        dx = p2[0] - p1[0]  # Δx in meters
        dy = p2[1] - p1[1]  # Δy in meters
        return math.sqrt(dx * dx + dy * dy)  # distance in meters

    @staticmethod
    def safe_speed(max_speed: float) -> float:
        """Get a safe speed value (avoids division by zero).

        Args:
            max_speed: robot maximum speed (m/s)

        Returns:
            float: max(max_speed, EPSILON_SPEED) in m/s
        """
        return max(max_speed, TravelTimeCalculator.EPSILON_SPEED)

    @staticmethod
    def compute(p1: Tuple[float, float],
                p2: Tuple[float, float],
                max_speed: float) -> float:
        """Compute travel time for a robot to move from p1 to p2.

        Args:
            p1: start position (x, y) in meters
            p2: target position (x, y) in meters
            max_speed: robot maximum speed in m/s

        Returns:
            float: travel time in seconds

        Example:
            >>> p1 = (0.0, 0.0)
            >>> p2 = (5.0, 0.0)
            >>> speed = 0.5      # m/s
            >>> tt = TravelTimeCalculator.compute(p1, p2, speed)
            >>> print(f"Travel time: {tt:.2f}s")
            Travel time: 10.00s

        Verification:
            distance = 5.0 m
            speed = 0.5 m/s
            time = 5.0 / 0.5 = 10.0 s ✓
        """
        if not isinstance(p1, (tuple, list)) or len(p1) != 2:
            raise ValueError(f"p1 must be (x, y), got {p1}")
        if not isinstance(p2, (tuple, list)) or len(p2) != 2:
            raise ValueError(f"p2 must be (x, y), got {p2}")
        if max_speed < 0:
            raise ValueError(f"max_speed must be >= 0, got {max_speed}")

        distance = TravelTimeCalculator.euclidean_distance(p1, p2)  # meters
        safe_v = TravelTimeCalculator.safe_speed(max_speed)  # m/s
        travel_time = distance / safe_v  # seconds

        return travel_time

    @staticmethod
    def compute_between_tasks(task_end_location: Tuple[float, float],
                              next_task_location: Tuple[float, float],
                              robot_max_speed: float) -> float:
        """Compute travel time between two task locations.

        Convenience wrapper; semantics identical to compute().
        """
        return TravelTimeCalculator.compute(
            task_end_location,
            next_task_location,
            robot_max_speed
        )


# ============================================================
# RESOURCE OVERHEAD CALCULATION
# ============================================================

class ResourceOverheadCalculator:
    """
    Resource overhead calculator.

    DEFINITION:
      Resource overhead is the additional time required when a task uses
      a shared resource. This is SEPARATE from travel_time.

    USAGE:
      When a task uses a resource:
      resource_hold_time = task.duration + resource.traversal_time

    IMPORTANT:
      overhead is part of the resource lock period,
      NOT something that happens after the robot leaves.
    """

    @staticmethod
    def compute(resource_traversal_time: float) -> float:
        """Get resource overhead value.

        Args:
            resource_traversal_time: traversal_time from resource config (seconds)

        Returns:
            float: resource overhead in seconds
        """
        if resource_traversal_time < 0:
            raise ValueError(
                f"resource_traversal_time must be >= 0, "
                f"got {resource_traversal_time}"
            )
        return float(resource_traversal_time)

    @staticmethod
    def get_resource_hold_duration(task_duration: float,
                                   resource_overhead: float) -> float:
        """Compute total duration a task holds a resource.

        Formula:
            resource_hold_duration = task_duration + resource_overhead

        Example:
            >>> task_dur = 15  # task executes for 15s
            >>> resource_oh = 10  # resource overhead 10s
            >>> total = ResourceOverheadCalculator.get_resource_hold_duration(
            ...     task_dur, resource_oh)
            >>> print(f"Resource held for {total}s")
            Resource held for 25s
        """
        return task_duration + resource_overhead


# ============================================================
# TIME CONSTRAINT VALIDATION
# ============================================================

class TimeConstraintValidator:
    """Time constraint validator."""

    @staticmethod
    def check_deadline_compliance(task_end_time: float,
                                  task_deadline: float) -> Tuple[bool, float]:
        """Check whether a task meets its deadline.

        Returns:
            Tuple[bool, float]: (complies, violation_amount)
        """
        complies = TimeComparison.leq(task_end_time, task_deadline)
        violation = max(0.0, task_end_time - task_deadline)
        return complies, violation

    @staticmethod
    def check_global_deadline_compliance(makespan: float,
                                         global_deadline: float) -> Tuple[bool, float]:
        """Check whether the system meets the global deadline.

        Returns:
            Tuple[bool, float]: (complies, violation_amount)
        """
        complies = TimeComparison.leq(makespan, global_deadline)
        violation = max(0.0, makespan - global_deadline)
        return complies, violation

    @staticmethod
    def check_resource_mutex(resource_allocations: list) -> bool:
        """Check resource mutual exclusion constraints.

        Args:
            resource_allocations: list of resource usage entries,
                each with {"robot": robot_id, "start_time": t_start, "end_time": t_end}

        Returns:
            bool: True if no overlaps detected
        """
        if len(resource_allocations) <= 1:
            return True

        sorted_allocs = sorted(resource_allocations,
                               key=lambda x: x["start_time"])

        for i in range(len(sorted_allocs) - 1):
            curr = sorted_allocs[i]
            next_alloc = sorted_allocs[i + 1]

            # curr.end_time should be <= next.start_time
            if not TimeComparison.leq(curr["end_time"], next_alloc["start_time"]):
                return False

        return True


# ============================================================
# TYPED VALUE WRAPPERS
# ============================================================

@dataclass
class TimeValue:
    """Time value with explicit unit declaration."""
    value: float  # seconds
    unit: str = "seconds"

    def __post_init__(self):
        if self.unit != "seconds":
            raise ValueError(
                f"Only 'seconds' unit is supported, got {self.unit}"
            )
        if self.value < 0:
            raise ValueError(f"Time value cannot be negative, got {self.value}")

    def __float__(self):
        return float(self.value)


@dataclass
class SpatialValue:
    """Spatial value with explicit unit declaration."""
    value: Tuple[float, float]  # (x, y)
    unit: str = "meters"

    def __post_init__(self):
        if self.unit != "meters":
            raise ValueError(
                f"Only 'meters' unit is supported, got {self.unit}"
            )
        if len(self.value) != 2:
            raise ValueError(
                f"Spatial value must be (x, y), got {self.value}"
            )

    def __iter__(self):
        return iter(self.value)


# ============================================================
# USAGE EXAMPLES AND TESTS
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("UNIFIED TIME CALCULATION LIBRARY - TESTS")
    print("=" * 70)

    # Test 1: Basic travel time calculation
    print("\n[Test 1] Basic Travel Time Calculation")
    p1 = (0.0, 0.0)
    p2 = (5.0, 0.0)
    speed = 0.5
    tt = TravelTimeCalculator.compute(p1, p2, speed)
    print(f"  Distance: 5.0 m, Speed: {speed} m/s")
    print(f"  Travel time: {tt:.4f} s")
    print(f"  Expected: 10.0 s, Got: {tt:.4f} s")
    assert abs(tt - 10.0) < 1e-9, "Travel time calculation failed"
    print("  ✓ PASS")

    # Test 2: Travel time with very small speed
    print("\n[Test 2] Travel Time with Very Small Speed")
    speed_small = 0.00001
    tt_small = TravelTimeCalculator.compute(p1, p2, speed_small)
    print(f"  Distance: 5.0 m, Speed: {speed_small} m/s")
    print(f"  Travel time: {tt_small:.4f} s")
    expected = 5.0 / TravelTimeCalculator.EPSILON_SPEED
    print(f"  Expected (with epsilon): {expected:.4e} s")
    print(f"  ✓ Calculation complete")

    # Test 3: Resource overhead
    print("\n[Test 3] Resource Overhead Calculation")
    task_dur = 15.0
    resource_oh = 10.0
    total_hold = ResourceOverheadCalculator.get_resource_hold_duration(
        task_dur, resource_oh
    )
    print(f"  Task duration: {task_dur} s")
    print(f"  Resource overhead: {resource_oh} s")
    print(f"  Total hold time: {total_hold} s")
    print(f"  Expected: 25.0 s, Got: {total_hold} s")
    assert abs(total_hold - 25.0) < 1e-9, "Resource overhead calculation failed"
    print("  ✓ PASS")

    # Test 4: Time comparison with epsilon
    print("\n[Test 4] Time Comparison with Epsilon")
    t1 = 10.0
    t2 = 10.0 + 1e-10  # Difference smaller than epsilon
    t3 = 10.0 + 1e-8   # Difference larger than epsilon

    print(f"  t1 = {t1}")
    print(f"  t2 = {t2} (difference: 1e-10, < epsilon=1e-9)")
    print(f"  t3 = {t3} (difference: 1e-8, > epsilon=1e-9)")

    result_eq = TimeComparison.eq(t1, t2)
    result_neq = TimeComparison.eq(t1, t3)
    print(f"  t1 == t2 (with epsilon): {result_eq}")
    print(f"  t1 == t3 (with epsilon): {result_neq}")
    assert result_eq == True, "Small difference should be equal"
    assert result_neq == False, "Large difference should not be equal"
    print("  ✓ PASS")

    # Test 5: Deadline compliance
    print("\n[Test 5] Deadline Compliance Check")
    end_time = 59.999999
    deadline = 60.0
    complies, violation = TimeConstraintValidator.check_deadline_compliance(
        end_time, deadline
    )
    print(f"  End time: {end_time} s")
    print(f"  Deadline: {deadline} s")
    print(f"  Complies: {complies}")
    print(f"  Violation: {violation} s")
    assert complies == True, "Should comply with deadline"
    assert abs(violation) < 1e-9, "Violation should be 0"
    print("  ✓ PASS")

    # Test 6: Resource mutex check
    print("\n[Test 6] Resource Mutual Exclusion Check")
    allocations = [
        {"robot": "A", "start_time": 0.0, "end_time": 10.0},
        {"robot": "B", "start_time": 10.0, "end_time": 20.0},
        {"robot": "C", "start_time": 20.0, "end_time": 30.0},
    ]
    mutex_ok = TimeConstraintValidator.check_resource_mutex(allocations)
    print(f"  Allocations: {len(allocations)} tasks")
    print(f"  Mutex check: {mutex_ok}")
    assert mutex_ok == True, "Should have no overlap"
    print("  ✓ PASS")

    # Test 7: Overlapping allocations should fail
    print("\n[Test 7] Resource Mutex Check with Overlap")
    allocations_overlap = [
        {"robot": "A", "start_time": 0.0, "end_time": 15.0},
        {"robot": "B", "start_time": 10.0, "end_time": 20.0},  # Overlaps!
    ]
    mutex_overlap = TimeConstraintValidator.check_resource_mutex(
        allocations_overlap
    )
    print(f"  Allocations: {len(allocations_overlap)} tasks")
    print(f"  Task A: [0.0, 15.0]")
    print(f"  Task B: [10.0, 20.0]")
    print(f"  Mutex check: {mutex_overlap}")
    assert mutex_overlap == False, "Should detect overlap"
    print("  ✓ PASS")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
