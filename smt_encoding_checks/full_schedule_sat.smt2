(set-logic QF_LRA)

; Integrated miniature schedule:
; - two tasks
; - one robot
; - exact assignment
; - time constraints
; - precedence task_5 -> task_7
; - shared resource mutex
(declare-const st_task_5 Real)
(declare-const et_task_5 Real)
(declare-const st_task_7 Real)
(declare-const et_task_7 Real)
(declare-const assign_robot_1_task_5 Bool)
(declare-const assign_robot_1_task_7 Bool)
(declare-const order_robot_1_task_5_task_7 Bool)
(declare-const res_start_task_5 Real)
(declare-const res_end_task_5 Real)
(declare-const res_start_task_7 Real)
(declare-const res_end_task_7 Real)
(declare-const res_before_task_5_task_7 Bool)

; Phi_time
(assert (>= st_task_5 0))
(assert (>= st_task_7 0))
(assert (= et_task_5 (+ st_task_5 8.82)))
(assert (= et_task_7 (+ st_task_7 6.84)))
(assert (<= et_task_5 120.0))
(assert (<= et_task_7 120.0))

; Phi_assign for a single robot.
(assert assign_robot_1_task_5)
(assert assign_robot_1_task_7)

; Same-robot ordering with travel gap 1.0.
(assert
  (=>
    (and assign_robot_1_task_5 assign_robot_1_task_7)
    (or
      (and order_robot_1_task_5_task_7
           (>= st_task_7 (+ et_task_5 1.0)))
      (and (not order_robot_1_task_5_task_7)
           (>= st_task_5 (+ et_task_7 1.0)))
    )
  )
)

; Phi_prec
(assert (>= st_task_7 et_task_5))

; Phi_resource, with overhead 2.0.
(assert (= res_start_task_5 st_task_5))
(assert (= res_end_task_5 (+ et_task_5 2.0)))
(assert (= res_start_task_7 st_task_7))
(assert (= res_end_task_7 (+ et_task_7 2.0)))
(assert
  (or
    (and res_before_task_5_task_7
         (<= res_end_task_5 res_start_task_7))
    (and (not res_before_task_5_task_7)
         (<= res_end_task_7 res_start_task_5))
  )
)

; Concrete valid schedule: task_5 finishes at 49.96, task_7 starts at 53.01.
(assert (= st_task_5 41.14))
(assert (= st_task_7 53.01))

(check-sat)
(get-model)

