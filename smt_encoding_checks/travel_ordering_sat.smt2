(set-logic QF_LRA)

; Same-robot ordering with travel:
; if both tasks are assigned to the robot, either task_1 precedes task_2
; with travel_1_2, or task_2 precedes task_1 with travel_2_1.
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

; Concrete valid order: task_1 then task_2.
(assert order_robot_1_task_1_task_2)
(assert (= st_task_1 0.0))
(assert (= st_task_2 7.0))

(check-sat)
(get-model)

