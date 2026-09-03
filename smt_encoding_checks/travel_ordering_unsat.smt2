(set-logic QF_LRA)

; Unsat because two tasks on the same robot overlap and neither ordering
; can satisfy the required travel gap.
(declare-const assign_robot_1_task_1 Bool)
(declare-const assign_robot_1_task_2 Bool)
(declare-const order_robot_1_task_1_task_2 Bool)
(declare-const st_task_1 Real)
(declare-const et_task_1 Real)
(declare-const st_task_2 Real)
(declare-const et_task_2 Real)

(assert (= et_task_1 (+ st_task_1 5.0)))
(assert (= et_task_2 (+ st_task_2 4.0)))
(assert assign_robot_1_task_1)
(assert assign_robot_1_task_2)

(assert
  (=>
    (and assign_robot_1_task_1 assign_robot_1_task_2)
    (or
      (and order_robot_1_task_1_task_2
           (>= st_task_2 (+ et_task_1 2.0)))
      (and (not order_robot_1_task_1_task_2)
           (>= st_task_1 (+ et_task_2 2.0)))
    )
  )
)

(assert (= st_task_1 0.0))
(assert (= st_task_2 3.0))

(check-sat)

