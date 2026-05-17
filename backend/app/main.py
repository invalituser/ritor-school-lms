import json
import os
import time
from typing import Any, Optional
from datetime import date, datetime

import psycopg
import redis
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from app.rate_limiter import TokenBucketRateLimiter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(
    title="Ritor School LMS-lite API",
    description="REST API for Ritor School LMS-lite Learning Center Management System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True,
)

CACHE_TTL_SECONDS = 60

COURSES_QUERY = """
SELECT id, title, description, level, duration_weeks, is_active, created_at
FROM courses
ORDER BY id;
"""
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, chat_room_id: int, websocket: WebSocket):
        await websocket.accept()

        if chat_room_id not in self.active_connections:
            self.active_connections[chat_room_id] = []

        self.active_connections[chat_room_id].append(websocket)

    def disconnect(self, chat_room_id: int, websocket: WebSocket):
        if chat_room_id in self.active_connections:
            if websocket in self.active_connections[chat_room_id]:
                self.active_connections[chat_room_id].remove(websocket)

    async def broadcast(self, chat_room_id: int, message: dict[str, Any]):
        connections = self.active_connections.get(chat_room_id, [])

        for connection in connections:
            await connection.send_json(message)


manager = ConnectionManager()

chat_rate_limiter = TokenBucketRateLimiter(
    capacity=5,
    refill_rate_per_second=0.5,
)

def fetch_all(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


def fetch_one(query: str, params: tuple = ()) -> dict[str, Any]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()

                if result is None:
                    raise HTTPException(status_code=404, detail="Record not found")

                return result
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


def execute_returning(query: str, params: tuple = ()) -> dict[str, Any]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()
                conn.commit()
                return result
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


class UserCreate(BaseModel):
    full_name: str
    email: str
    password_hash: str
    role: str
    phone: Optional[str] = None


class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    level: Optional[str] = None
    duration_weeks: Optional[int] = None


class GroupCreate(BaseModel):
    course_id: int
    teacher_id: int
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    schedule: Optional[str] = None


class AssignmentCreate(BaseModel):
    group_id: int
    teacher_id: int
    title: str
    description: Optional[str] = None
    due_date: datetime
    max_score: int = 100


class SubmissionCreate(BaseModel):
    assignment_id: int
    student_id: int
    answer_text: Optional[str] = None
    file_url: Optional[str] = None


class GradeCreate(BaseModel):
    submission_id: int
    teacher_id: int
    score: int
    feedback: Optional[str] = None


class AttendanceCreate(BaseModel):
    lesson_id: int
    student_id: int
    status: str
    comment: Optional[str] = None


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
    return fetch_one("SELECT current_database() AS database_name;")

@app.get("/cache-check")
def cache_check() -> dict[str, str]:
    try:
        redis_client.ping()
        return {
            "status": "redis connected"
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

@app.get("/users")
def get_users() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, full_name, email, role, phone, is_active, created_at
        FROM users
        ORDER BY id;
        """
    )


@app.get("/users/{user_id}")
def get_user(user_id: int) -> dict[str, Any]:
    return fetch_one(
        """
        SELECT id, full_name, email, role, phone, is_active, created_at
        FROM users
        WHERE id = %s;
        """,
        (user_id,),
    )


@app.post("/users", status_code=201)
def create_user(user: UserCreate) -> dict[str, Any]:
    return execute_returning(
        """
        INSERT INTO users (full_name, email, password_hash, role, phone)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, full_name, email, role, phone, is_active, created_at;
        """,
        (user.full_name, user.email, user.password_hash, user.role, user.phone),
    )


@app.get("/courses")
def get_courses() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, title, description, level, duration_weeks, is_active, created_at
        FROM courses
        ORDER BY id;
        """
    )

@app.get("/courses-no-cache")
def get_courses_no_cache() -> dict[str, Any]:
    start_time = time.perf_counter()

    courses = fetch_all(COURSES_QUERY)

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "source": "postgres",
        "elapsed_ms": elapsed_ms,
        "count": len(courses),
        "data": courses,
    }


@app.get("/courses-cached")
def get_courses_cached() -> dict[str, Any]:
    start_time = time.perf_counter()
    cache_key = "courses:list"

    try:
        cached_courses = redis_client.get(cache_key)
    except Exception:
        cached_courses = None

    if cached_courses:
        courses = json.loads(cached_courses)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "source": "redis_cache",
            "elapsed_ms": elapsed_ms,
            "count": len(courses),
            "data": courses,
        }

    courses = fetch_all(COURSES_QUERY)

    try:
        redis_client.setex(
            cache_key,
            CACHE_TTL_SECONDS,
            json.dumps(courses, default=str),
        )
    except Exception:
        pass

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "source": "postgres",
        "elapsed_ms": elapsed_ms,
        "count": len(courses),
        "data": courses,
    }

@app.get("/courses/{course_id}")
def get_course(course_id: int) -> dict[str, Any]:
    return fetch_one(
        """
        SELECT id, title, description, level, duration_weeks, is_active, created_at
        FROM courses
        WHERE id = %s;
        """,
        (course_id,),
    )


@app.post("/courses", status_code=201)
def create_course(course: CourseCreate) -> dict[str, Any]:
    return execute_returning(
        """
        INSERT INTO courses (title, description, level, duration_weeks)
        VALUES (%s, %s, %s, %s)
        RETURNING id, title, description, level, duration_weeks, is_active, created_at;
        """,
        (course.title, course.description, course.level, course.duration_weeks),
    )


@app.get("/groups")
def get_groups() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            g.id,
            g.name,
            g.course_id,
            c.title AS course_title,
            g.teacher_id,
            u.full_name AS teacher_name,
            g.start_date,
            g.end_date,
            g.schedule,
            g.status,
            g.created_at
        FROM groups g
        JOIN courses c ON c.id = g.course_id
        JOIN users u ON u.id = g.teacher_id
        ORDER BY g.id;
        """
    )


@app.get("/groups/{group_id}")
def get_group(group_id: int) -> dict[str, Any]:
    return fetch_one(
        """
        SELECT
            g.id,
            g.name,
            g.course_id,
            c.title AS course_title,
            g.teacher_id,
            u.full_name AS teacher_name,
            g.start_date,
            g.end_date,
            g.schedule,
            g.status,
            g.created_at
        FROM groups g
        JOIN courses c ON c.id = g.course_id
        JOIN users u ON u.id = g.teacher_id
        WHERE g.id = %s;
        """,
        (group_id,),
    )


@app.post("/groups", status_code=201)
def create_group(group: GroupCreate) -> dict[str, Any]:
    return execute_returning(
        """
        INSERT INTO groups (course_id, teacher_id, name, start_date, end_date, schedule)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, course_id, teacher_id, name, start_date, end_date, schedule, status, created_at;
        """,
        (
            group.course_id,
            group.teacher_id,
            group.name,
            group.start_date,
            group.end_date,
            group.schedule,
        ),
    )


@app.get("/assignments")
def get_assignments() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            a.id,
            a.group_id,
            g.name AS group_name,
            a.teacher_id,
            u.full_name AS teacher_name,
            a.title,
            a.description,
            a.due_date,
            a.max_score,
            a.created_at
        FROM assignments a
        JOIN groups g ON g.id = a.group_id
        JOIN users u ON u.id = a.teacher_id
        ORDER BY a.id;
        """
    )


@app.get("/assignments/{assignment_id}")
def get_assignment(assignment_id: int) -> dict[str, Any]:
    return fetch_one(
        """
        SELECT
            a.id,
            a.group_id,
            g.name AS group_name,
            a.teacher_id,
            u.full_name AS teacher_name,
            a.title,
            a.description,
            a.due_date,
            a.max_score,
            a.created_at
        FROM assignments a
        JOIN groups g ON g.id = a.group_id
        JOIN users u ON u.id = a.teacher_id
        WHERE a.id = %s;
        """,
        (assignment_id,),
    )


@app.post("/assignments", status_code=201)
def create_assignment(assignment: AssignmentCreate) -> dict[str, Any]:
    return execute_returning(
        """
        INSERT INTO assignments (group_id, teacher_id, title, description, due_date, max_score)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, group_id, teacher_id, title, description, due_date, max_score, created_at;
        """,
        (
            assignment.group_id,
            assignment.teacher_id,
            assignment.title,
            assignment.description,
            assignment.due_date,
            assignment.max_score,
        ),
    )


@app.get("/submissions")
def get_submissions() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            s.id,
            s.assignment_id,
            a.title AS assignment_title,
            s.student_id,
            u.full_name AS student_name,
            s.answer_text,
            s.file_url,
            s.submitted_at,
            s.status
        FROM submissions s
        JOIN assignments a ON a.id = s.assignment_id
        JOIN users u ON u.id = s.student_id
        ORDER BY s.id;
        """
    )


@app.post("/submissions", status_code=201)
def create_submission(submission: SubmissionCreate) -> dict[str, Any]:
    return execute_returning(
        """
        INSERT INTO submissions (assignment_id, student_id, answer_text, file_url)
        VALUES (%s, %s, %s, %s)
        RETURNING id, assignment_id, student_id, answer_text, file_url, submitted_at, status;
        """,
        (
            submission.assignment_id,
            submission.student_id,
            submission.answer_text,
            submission.file_url,
        ),
    )


@app.get("/grades")
def get_grades() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            gr.id,
            gr.submission_id,
            gr.teacher_id,
            u.full_name AS teacher_name,
            gr.score,
            gr.feedback,
            gr.graded_at
        FROM grades gr
        JOIN users u ON u.id = gr.teacher_id
        ORDER BY gr.id;
        """
    )


@app.post("/grades", status_code=201)
def create_grade(grade: GradeCreate) -> dict[str, Any]:
    return execute_returning(
        """
        INSERT INTO grades (submission_id, teacher_id, score, feedback)
        VALUES (%s, %s, %s, %s)
        RETURNING id, submission_id, teacher_id, score, feedback, graded_at;
        """,
        (grade.submission_id, grade.teacher_id, grade.score, grade.feedback),
    )


@app.get("/attendance")
def get_attendance() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            att.id,
            att.lesson_id,
            l.title AS lesson_title,
            att.student_id,
            u.full_name AS student_name,
            att.status,
            att.comment,
            att.marked_at
        FROM attendance att
        JOIN lessons l ON l.id = att.lesson_id
        JOIN users u ON u.id = att.student_id
        ORDER BY att.id;
        """
    )


@app.post("/attendance", status_code=201)
def create_attendance(attendance: AttendanceCreate) -> dict[str, Any]:
    return execute_returning(
        """
        INSERT INTO attendance (lesson_id, student_id, status, comment)
        VALUES (%s, %s, %s, %s)
        RETURNING id, lesson_id, student_id, status, comment, marked_at;
        """,
        (
            attendance.lesson_id,
            attendance.student_id,
            attendance.status,
            attendance.comment,
        ),
    )

@app.get("/chat-messages/{chat_room_id}")
def get_chat_messages(chat_room_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            cm.id,
            cm.chat_room_id,
            cm.sender_id,
            u.full_name AS sender_name,
            cm.message,
            cm.sent_at
        FROM chat_messages cm
        JOIN users u ON u.id = cm.sender_id
        WHERE cm.chat_room_id = %s
        ORDER BY cm.sent_at;
        """,
        (chat_room_id,),
    )


@app.websocket("/ws/chat/{chat_room_id}/{user_id}")
async def websocket_chat(
    websocket: WebSocket,
    chat_room_id: int,
    user_id: int,
):
    await manager.connect(chat_room_id, websocket)

    await manager.broadcast(
        chat_room_id,
        {
            "type": "system",
            "message": f"User {user_id} joined chat room {chat_room_id}",
        },
    )

    try:
        while True:
            message_text = await websocket.receive_text()

            rate_limit_key = f"chat:{chat_room_id}:user:{user_id}"

            if not chat_rate_limiter.allow_request(rate_limit_key):
                await websocket.send_json(
                    {
                        "type": "rate_limit",
                        "message": "Too many messages. Please wait before sending again.",
                        "remaining_tokens": chat_rate_limiter.get_tokens(rate_limit_key),
                    }
                )
                continue

            try:
                saved_message = execute_returning(
                    """
                    INSERT INTO chat_messages (chat_room_id, sender_id, message)
                    VALUES (%s, %s, %s)
                    RETURNING id, chat_room_id, sender_id, message, sent_at;
                    """,
                    (chat_room_id, user_id, message_text),
                )

                await manager.broadcast(
                    chat_room_id,
                    {
                        "type": "chat_message",
                        "id": saved_message["id"],
                        "chat_room_id": saved_message["chat_room_id"],
                        "sender_id": saved_message["sender_id"],
                        "message": saved_message["message"],
                        "sent_at": str(saved_message["sent_at"]),
                    },
                )

            except Exception as error:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": str(error),
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(chat_room_id, websocket)

        await manager.broadcast(
            chat_room_id,
            {
                "type": "system",
                "message": f"User {user_id} left chat room {chat_room_id}",
            },
        )


@app.get("/chat-test", response_class=HTMLResponse)
def chat_test_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ritor School LMS-lite Chat Test</title>
    </head>
    <body>
        <h2>Ritor School LMS-lite WebSocket Chat Test</h2>

        <label>Chat Room ID:</label>
        <input id="roomId" value="1">
        <br><br>

        <label>User ID:</label>
        <input id="userId" value="4">
        <br><br>

        <button onclick="connect()">Connect</button>
        <button onclick="disconnect()">Disconnect</button>

        <hr>

        <input id="messageInput" placeholder="Type message here" style="width:300px;">
        <button onclick="sendMessage()">Send</button>

        <h3>Messages</h3>
        <div id="messages" style="border:1px solid black; padding:10px; width:600px; height:300px; overflow:auto;"></div>

        <script>
            let socket = null;

            function addMessage(text) {
                const messages = document.getElementById("messages");
                messages.innerHTML += "<p>" + text + "</p>";
                messages.scrollTop = messages.scrollHeight;
            }

            function connect() {
                const roomId = document.getElementById("roomId").value;
                const userId = document.getElementById("userId").value;

                socket = new WebSocket(`ws://${window.location.host}/ws/chat/${roomId}/${userId}`);

                socket.onopen = function() {
                    addMessage("Connected to chat room " + roomId + " as user " + userId);
                };

                socket.onmessage = function(event) {
                    addMessage(event.data);
                };

                socket.onclose = function() {
                    addMessage("Disconnected");
                };
            }

            function disconnect() {
                if (socket) {
                    socket.close();
                }
            }

            function sendMessage() {
                const input = document.getElementById("messageInput");

                if (socket && input.value.trim() !== "") {
                    socket.send(input.value);
                    input.value = "";
                }
            }
        </script>
    </body>
    </html>
    """