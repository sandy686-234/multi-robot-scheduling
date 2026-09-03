(set-logic QF_LIA)

; Unsat because an incapable robot is forced to execute the task.
(declare-const assign_robot_1_task_1 Bool)

(assert (= assign_robot_1_task_1 false))
(assert assign_robot_1_task_1)

(check-sat)

