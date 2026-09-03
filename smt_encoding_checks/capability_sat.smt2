(set-logic QF_LIA)

; Phi_cap disables assignments for incapable robots.
(declare-const assign_robot_1_task_1 Bool)
(declare-const assign_robot_2_task_1 Bool)

; robot_1 is incapable for task_1.
(assert (= assign_robot_1_task_1 false))

; exactly one capable candidate remains.
(assert
  (=
    (+
      (ite assign_robot_1_task_1 1 0)
      (ite assign_robot_2_task_1 1 0)
    )
    1
  )
)

(check-sat)
(get-model)

