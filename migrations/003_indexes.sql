CREATE INDEX IF NOT EXISTS idx_users_role
ON users(role);

CREATE INDEX IF NOT EXISTS idx_users_email
ON users(email);

CREATE INDEX IF NOT EXISTS idx_groups_course_id
ON groups(course_id);

CREATE INDEX IF NOT EXISTS idx_groups_teacher_id
ON groups(teacher_id);

CREATE INDEX IF NOT EXISTS idx_assignments_group_id
ON assignments(group_id);

CREATE INDEX IF NOT EXISTS idx_submissions_assignment_id
ON submissions(assignment_id);

CREATE INDEX IF NOT EXISTS idx_submissions_student_id
ON submissions(student_id);

CREATE INDEX IF NOT EXISTS idx_attendance_lesson_id
ON attendance(lesson_id);

CREATE INDEX IF NOT EXISTS idx_attendance_student_id
ON attendance(student_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_room_sent_at
ON chat_messages(chat_room_id, sent_at DESC);

CREATE INDEX IF NOT EXISTS idx_weekly_reports_student_group
ON weekly_reports(student_id, group_id);