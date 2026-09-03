(set-logic QF_LRA)

; Unsat because observed task_5 finishes after task_7 starts.
(declare-const et_task_5 Real)
(declare-const st_task_7 Real)

(assert (= et_task_5 54.50))
(assert (= st_task_7 53.01))
(assert (>= st_task_7 et_task_5))

(check-sat)

