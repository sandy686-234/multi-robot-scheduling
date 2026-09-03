(set-logic QF_LRA)

; Phi_resource mutex:
; two intervals on the same resource must not overlap.
(declare-const res_start_task_1 Real)
(declare-const res_end_task_1 Real)
(declare-const res_start_task_2 Real)
(declare-const res_end_task_2 Real)
(declare-const res_before_task_1_task_2 Bool)

(assert (= res_start_task_1 10.0))
(assert (= res_end_task_1 20.0))
(assert (= res_start_task_2 20.0))
(assert (= res_end_task_2 30.0))

(assert
  (or
    (and res_before_task_1_task_2
         (<= res_end_task_1 res_start_task_2))
    (and (not res_before_task_1_task_2)
         (<= res_end_task_2 res_start_task_1))
  )
)

(check-sat)
(get-model)

