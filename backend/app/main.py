import os
from typing import Any

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException


app = FastAPI(
    title="Ritor School LMS-lite API",
    description="Backend API for Ritor School LMS-lite Learning Center Management System",
    version="1.0.0",
)


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "ritor_lms"),
        user=os.getenv("DB_USER", "ritor_user"),
        password=os.getenv("DB_PASSWORD", "ritor_password"),
        row_factory=dict_row,
    )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Ritor School LMS-lite API is running"
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok"
    }


@app.get("/db-check")
def db_check() -> dict[str, Any]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database() AS database_name;")
                result = cur.fetchone()

        return {
            "status": "database connected",
            "database": result["database_name"],
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/courses")
def get_courses() -> list[dict[str, Any]]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, description, level, duration_weeks, is_active, created_at
                    FROM courses
                    ORDER BY id;
                    """
                )
                courses = cur.fetchall()

        return courses

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/users")
def get_users() -> list[dict[str, Any]]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, full_name, email, role, phone, is_active, created_at
                    FROM users
                    ORDER BY id;
                    """
                )
                users = cur.fetchall()

        return users

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))