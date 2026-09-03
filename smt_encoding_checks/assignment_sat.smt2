(set-logic QF_LIA)

; Phi_assign for one task and two capable robots:
; exactly one assignment variable must be true.
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
(assert (not assign_robot_2_task_1))

(check-sat)
(get-model)

