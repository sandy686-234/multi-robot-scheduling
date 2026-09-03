(set-logic QF_LRA)

; Integrated miniature schedule with an explicit precedence violation:
; task_5 ends at 54.50 while task_7 starts at 53.01.
(declare-const st_task_5 Real)
(declare-const et_task_5 Real)
(declare-const st_task_7 Real)
(declare-const et_task_7 Real)
(declare-const assign_robot_1_task_5 Bool)
(declare-const assign_robot_1_task_7 Bool)

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

; Phi_prec
(assert (>= st_task_7 et_task_5))

; Concrete runtime-observed values that violate task_5 -> task_7.
(assert (= et_task_5 54.50))
(assert (= st_task_7 53.01))

(check-sat)

