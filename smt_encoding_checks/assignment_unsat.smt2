(set-logic QF_LIA)

; Unsat because exactly-one assignment conflicts with both robots being true.
(declare-const assign_robot_1_task_1 Bool)
(declare-const assign_robot_2_task_1 Bool)

(assert
  (=
    (+
      (ite assign_robot_1_task_1 1 0)
      (ite assign_robot_2_task_1 1 0)
    )
    1
  )
)

(assert assign_robot_1_task_1)
(assert assign_robot_2_task_1)

(check-sat)

