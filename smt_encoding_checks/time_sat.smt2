(set-logic QF_LRA)

; Phi_time for one task:
; s_i >= 0, e_i = s_i + d_i, e_i <= D_i, e_i <= D_global
(declare-const st_task_1 Real)
(declare-const et_task_1 Real)

(assert (>= st_task_1 0))
(assert (= et_task_1 (+ st_task_1 5.0)))
(assert (<= et_task_1 10.0))
(assert (<= et_task_1 12.0))

; A concrete valid timing assignment.
(assert (= st_task_1 2.0))

(check-sat)
(get-model)

