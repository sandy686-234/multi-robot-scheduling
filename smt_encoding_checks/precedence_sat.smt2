(set-logic QF_LRA)

; Phi_prec for task_5 -> task_7:
; s_task_7 >= e_task_5.
(declare-const et_task_5 Real)
(declare-const st_task_7 Real)

(assert (= et_task_5 49.96))
(assert (= st_task_7 53.01))
(assert (>= st_task_7 et_task_5))

(check-sat)
(get-model)

