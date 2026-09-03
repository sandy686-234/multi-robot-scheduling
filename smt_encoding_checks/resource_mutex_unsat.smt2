(set-logic QF_LRA)

; Unsat because the two resource intervals overlap on the same mutex resource.
(declare-const res_start_task_1 Real)
(declare-const res_end_task_1 Real)
(declare-const res_start_task_2 Real)
(declare-const res_end_task_2 Real)
(declare-const res_before_task_1_task_2 Bool)

(assert (= res_start_task_1 10.0))
(assert (= res_end_task_1 20.0))
(assert (= res_start_task_2 15.0))
(assert (= res_end_task_2 25.0))

(assert
  (or
    (and res_before_task_1_task_2
         (<= res_end_task_1 res_start_task_2))
    (and (not res_before_task_1_task_2)
         (<= res_end_task_2 res_start_task_1))
  )
)

(check-sat)

