INSERT INTO users (full_name, email, password_hash, role, phone)
VALUES
('System Admin', 'admin@ritor.school', 'hashed_password_placeholder', 'admin', '+998900000001'),
('Aziz Teacher', 'aziz.teacher@ritor.school', 'hashed_password_placeholder', 'teacher', '+998900000002'),
('Madina Teacher', 'madina.teacher@ritor.school', 'hashed_password_placeholder', 'teacher', '+998900000003'),
('Ali Student', 'ali.student@ritor.school', 'hashed_password_placeholder', 'student', '+998900000004'),
('Laylo Student', 'laylo.student@ritor.school', 'hashed_password_placeholder', 'student', '+998900000005')
ON CONFLICT (email) DO NOTHING;

INSERT INTO courses (title, description, level, duration_weeks)
VALUES
('English Beginner', 'Basic English course for beginners', 'Beginner', 12),
('IELTS Preparation', 'IELTS exam preparation course', 'Intermediate', 16),
('Programming Basics', 'Introduction to programming concepts', 'Beginner', 10);

INSERT INTO groups (course_id, teacher_id, name, start_date, end_date, schedule)
VALUES
(1, 2, 'English Beginner Group A', '2026-05-01', '2026-07-31', 'Monday, Wednesday, Friday 18:00'),
(2, 3, 'IELTS Group A', '2026-05-01', '2026-08-31', 'Tuesday, Thursday 18:00');

INSERT INTO group_students (group_id, student_id)
VALUES
(1, 4),
(1, 5),
(2, 4);

INSERT INTO lessons (group_id, title, topic, lesson_date)
VALUES
(1, 'Lesson 1', 'Introduction and alphabet review', '2026-05-05 18:00:00'),
(1, 'Lesson 2', 'Basic grammar', '2026-05-07 18:00:00'),
(2, 'Lesson 1', 'IELTS overview', '2026-05-06 18:00:00');

INSERT INTO assignments (group_id, teacher_id, title, description, due_date, max_score)
VALUES
(1, 2, 'Homework 1', 'Write 10 simple English sentences.', '2026-05-10 23:59:00', 100),
(2, 3, 'IELTS Writing Task 1', 'Write one Task 1 report.', '2026-05-12 23:59:00', 100);

INSERT INTO submissions (assignment_id, student_id, answer_text)
VALUES
(1, 4, 'My name is Ali. I am a student. I like English.'),
(1, 5, 'My name is Laylo. I study at Ritor School.');

INSERT INTO grades (submission_id, teacher_id, score, feedback)
VALUES
(1, 2, 90, 'Good work. Check small grammar mistakes.'),
(2, 2, 95, 'Excellent work.');

INSERT INTO attendance (lesson_id, student_id, status, comment)
VALUES
(1, 4, 'present', 'On time'),
(1, 5, 'late', 'Came 10 minutes late'),
(2, 4, 'present', 'On time');

INSERT INTO chat_rooms (group_id, name)
VALUES
(1, 'English Beginner Group A Chat'),
(2, 'IELTS Group A Chat');

INSERT INTO chat_messages (chat_room_id, sender_id, message)
VALUES
(1, 4, 'Hello teacher, when is the homework deadline?'),
(1, 2, 'The deadline is Sunday 23:59.');

INSERT INTO weekly_reports (
    student_id,
    group_id,
    week_start,
    week_end,
    attendance_percentage,
    average_score,
    submitted_assignments,
    total_assignments
)
VALUES
(4, 1, '2026-05-04', '2026-05-10', 100.00, 90.00, 1, 1),
(5, 1, '2026-05-04', '2026-05-10', 50.00, 95.00, 1, 1);