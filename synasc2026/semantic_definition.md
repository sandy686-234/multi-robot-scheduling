Semantic Definition: Unified Travel-Time Model

Definition 1: Travel-Time Calculation


travel_time(p₁, p₂, v_max) = euclidean_distance(p₁, p₂) / max(v_max, ε)


where:
1. p₁, p₂: 2D coordinates in meters
2. v_max: Robot maximum speed in m/s  
3. ε = 1e-9 m/s: Numerical safety bound (prevents division by zero)

Output:Travel time in seconds (non-negative real number)

Definition 2: Resource Overhead


resource_hold_time = task.duration + resource.traversal_time


Mutual Exclusion Constraint:

For tasks A, B on shared resource r:
  end(A) + overhead(r) ≤ start(B)  OR  end(B) + overhead(r) ≤ start(A)


This ensures no overlap in resource usage, including overhead time.



Task Scheduling Semantics:

For task T assigned to robot R:

1. Travel to task:
   t_travel = travel_time(R.position, T.location, R.speed)

2. Compute start time (respecting resource and deadline constraints):
   t_start = max(
       previous_end + t_travel,      [robot travel time]
       resource_free_time            [resource availability]
   )

3. Execute task:
   t_end = t_start + T.duration

4. Update resource state (if task uses resource):
   resource_free_time = t_end + resource_overhead

5. Verify constraints:
   t_end ≤ T.deadline       [task deadline satisfied]
   t_end ≤ global_deadline  [project deadline satisfied]



Time Units and Dimensions:

  Location:          (x, y) in meters [m]
  Robot Speed:       meters per second [m/s]
  Task Duration:     seconds [s]
  Task Deadline:     seconds [s]
  Resource Overhead: seconds [s]
  Travel Time:       seconds [s]
  Makespan:          seconds [s]
  Time Windows:      seconds [s]

Key Insight

Definition 1 ensures that the **symbolic representation (SMT constraints) and numeric implementation (schedule verification) are semantically identical, eliminating the symbolic-numeric gap that previously caused most scheduling failures.




