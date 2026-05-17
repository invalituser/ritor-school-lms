import argparse
import os
from datetime import date, datetime, timedelta
from typing import Any

import psycopg
from psycopg.rows import dict_row


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "ritor_lms"),
        user=os.getenv("DB_USER", "ritor_user"),
        password=os.getenv("DB_PASSWORD", "ritor_password"),
        row_factory=dict_row,
    )


def get_default_week_start() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def parse_week_start(value: str | None) -> date:
    if value is None:
        return get_default_week_start()

    return datetime.strptime(value, "%Y-%m-%d").date()


def generate_weekly_reports(week_start: date) -> list[dict[str, Any]]:
    week_end = week_start + timedelta(days=6)
    next_week_start = week_start + timedelta(days=7)

    query = """
    WITH base AS (
        SELECT
            gs.student_id,
            gs.group_id
        FROM group_students gs
        WHERE gs.status = 'active'
    ),
    attendance_summary AS (
        SELECT
            b.student_id,
            b.group_id,
            COUNT(att.id) AS total_attendance_records,
            SUM(
                CASE
                    WHEN att.status IN ('present', 'late') THEN 1
                    ELSE 0
                END
            ) AS attended_records
        FROM base b
        JOIN lessons l ON l.group_id = b.group_id
        LEFT JOIN attendance att
            ON att.lesson_id = l.id
            AND att.student_id = b.student_id
        WHERE l.lesson_date >= %s
          AND l.lesson_date < %s
        GROUP BY b.student_id, b.group_id
    ),
    assignment_summary AS (
        SELECT
            b.student_id,
            b.group_id,
            COUNT(a.id) AS total_assignments
        FROM base b
        LEFT JOIN assignments a
            ON a.group_id = b.group_id
            AND a.due_date >= %s
            AND a.due_date < %s
        GROUP BY b.student_id, b.group_id
    ),
    submission_summary AS (
        SELECT
            b.student_id,
            b.group_id,
            COUNT(s.id) AS submitted_assignments
        FROM base b
        LEFT JOIN assignments a
            ON a.group_id = b.group_id
            AND a.due_date >= %s
            AND a.due_date < %s
        LEFT JOIN submissions s
            ON s.assignment_id = a.id
            AND s.student_id = b.student_id
        GROUP BY b.student_id, b.group_id
    ),
    grade_summary AS (
        SELECT
            b.student_id,
            b.group_id,
            ROUND(AVG(g.score), 2) AS average_score
        FROM base b
        LEFT JOIN assignments a
            ON a.group_id = b.group_id
            AND a.due_date >= %s
            AND a.due_date < %s
        LEFT JOIN submissions s
            ON s.assignment_id = a.id
            AND s.student_id = b.student_id
        LEFT JOIN grades g
            ON g.submission_id = s.id
        GROUP BY b.student_id, b.group_id
    )
    INSERT INTO weekly_reports (
        student_id,
        group_id,
        week_start,
        week_end,
        attendance_percentage,
        average_score,
        submitted_assignments,
        total_assignments,
        generated_at
    )
    SELECT
        b.student_id,
        b.group_id,
        %s AS week_start,
        %s AS week_end,
        COALESCE(
            CASE
                WHEN attendance_summary.total_attendance_records > 0
                THEN ROUND(
                    attendance_summary.attended_records::numeric
                    / attendance_summary.total_attendance_records::numeric
                    * 100,
                    2
                )
                ELSE 0
            END,
            0
        ) AS attendance_percentage,
        COALESCE(grade_summary.average_score, 0) AS average_score,
        COALESCE(submission_summary.submitted_assignments, 0) AS submitted_assignments,
        COALESCE(assignment_summary.total_assignments, 0) AS total_assignments,
        CURRENT_TIMESTAMP AS generated_at
    FROM base b
    LEFT JOIN attendance_summary
        ON attendance_summary.student_id = b.student_id
        AND attendance_summary.group_id = b.group_id
    LEFT JOIN assignment_summary
        ON assignment_summary.student_id = b.student_id
        AND assignment_summary.group_id = b.group_id
    LEFT JOIN submission_summary
        ON submission_summary.student_id = b.student_id
        AND submission_summary.group_id = b.group_id
    LEFT JOIN grade_summary
        ON grade_summary.student_id = b.student_id
        AND grade_summary.group_id = b.group_id
    ON CONFLICT (student_id, group_id, week_start, week_end)
    DO UPDATE SET
        attendance_percentage = EXCLUDED.attendance_percentage,
        average_score = EXCLUDED.average_score,
        submitted_assignments = EXCLUDED.submitted_assignments,
        total_assignments = EXCLUDED.total_assignments,
        generated_at = CURRENT_TIMESTAMP
    RETURNING
        id,
        student_id,
        group_id,
        week_start,
        week_end,
        attendance_percentage,
        average_score,
        submitted_assignments,
        total_assignments,
        generated_at;
    """

    params = (
        week_start,
        next_week_start,
        week_start,
        next_week_start,
        week_start,
        next_week_start,
        week_start,
        next_week_start,
        week_start,
        week_end,
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            reports = cur.fetchall()
            conn.commit()
            return reports


def main():
    parser = argparse.ArgumentParser(
        description="Generate weekly student performance reports."
    )
    parser.add_argument(
        "--week-start",
        help="Week start date in YYYY-MM-DD format. Example: 2026-05-04",
    )

    args = parser.parse_args()
    week_start = parse_week_start(args.week_start)

    reports = generate_weekly_reports(week_start)

    print("Weekly report batch pipeline completed successfully.")
    print(f"Week start: {week_start}")
    print(f"Week end: {week_start + timedelta(days=6)}")
    print(f"Generated reports: {len(reports)}")

    for report in reports:
        print(report)


if __name__ == "__main__":
    main()