(set-logic QF_LRA)

; Unsat because duration 5 from start 2 gives end 7,
; but the task deadline requires end <= 6.
(declare-const st_task_1 Real)
(declare-const et_task_1 Real)

(assert (>= st_task_1 0))
(assert (= et_task_1 (+ st_task_1 5.0)))
(assert (<= et_task_1 6.0))
(assert (= st_task_1 2.0))

(check-sat)

