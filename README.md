# Ritor School LMS-lite

**Ritor School LMS-lite** is a learning center management system designed for a private education center.  
The system helps admins, teachers, and students manage courses, groups, assignments, submissions, grades, attendance, chat messages, and weekly performance reports.

Project author:

**RAHIMBEK RAJABBOEV**  
**Student ID: U2210182**

---
Project helpers: 


## 1. Project Overview

Ritor School LMS-lite is based on a university LMS-lite scenario, but it is adapted for a private learning center environment.

The system supports three main user roles:

- Admin
- Teacher
- Student

Main features:

- REST API using FastAPI
- PostgreSQL relational database
- Redis caching
- WebSocket real-time chat
- Token-bucket rate limiter
- Weekly report batch pipeline
- Nginx API gateway
- Docker Compose orchestration
- Basic observability with health check, metrics, and logs
- Remote deployment on DigitalOcean Droplet

---

## 2. Technology Stack

| Component | Technology |
|---|---|
| Backend | FastAPI |
| Main Database | PostgreSQL 16 |
| Cache / Additional Store | Redis |
| API Gateway | Nginx |
| Real-Time Communication | WebSocket |
| Batch Processing | Python batch worker |
| Containerization | Docker |
| Orchestration | Docker Compose |
| Deployment | DigitalOcean Droplet |
| API Documentation | Swagger / OpenAPI |

---

## 3. Project Structure

```text
ritor-school-lms/
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── rate_limiter.py
│       └── batch_worker.py
│
├── migrations/
│   ├── 001_init.sql
│   ├── 002_seed.sql
│   └── 003_indexes.sql
│
├── nginx/
│   └── nginx.conf
│
├── docker-compose.yml
└── README.md

## 4. Main Services

The system runs with Docker Compose and contains four main services:

### 1. backend

Runs the FastAPI application.

Responsibilities:

- REST API endpoints
- WebSocket chat
- Redis caching
- Batch worker logic
- Observability endpoints

### 2. postgres

Runs PostgreSQL 16.

Responsibilities:

- Stores relational LMS data
- Stores users, courses, groups, assignments, submissions, grades, attendance, chat messages, and weekly reports

### 3. redis

Runs Redis.

Responsibilities:

- Caches frequently requested data
- Improves response time for repeated requests

### 4. nginx

Runs Nginx API Gateway.

Responsibilities:

- Receives requests on port `8080`
- Forwards requests to FastAPI backend
- Supports REST API and WebSocket traffic

5. How to Run Locally
Step 1: Clone the repository
git clone https://github.com/invalituser/ritor-school-lms.git
cd ritor-school-lms
Step 2: Start the system
docker compose up -d --build
Step 3: Check running containers
docker compose ps

Expected services:

ritor_backend
ritor_postgres
ritor_redis
ritor_nginx



6. Local URLs
Direct FastAPI backend:
http://localhost:8000

Nginx API Gateway:
http://localhost:8080

Useful local links:
http://localhost:8080/health
http://localhost:8080/docs
http://localhost:8080/courses
http://localhost:8080/chat-test
http://localhost:8080/metrics



7. Public Deployment URLs
The project is deployed on a DigitalOcean Droplet.
Public server IP: 142.93.99.38

Public links:
http://142.93.99.38:8080/health
http://142.93.99.38:8080/docs
http://142.93.99.38:8080/courses
http://142.93.99.38:8080/chat-test
http://142.93.99.38:8080/metrics




8. Main API Endpoints
System endpoints
GET /
GET /health
GET /db-check
GET /metrics

Users
GET /users
GET /users/{user_id}
POST /users

Courses
GET /courses
GET /courses/{course_id}
POST /courses
GET /courses-no-cache
GET /courses-cached

Groups
GET /groups
GET /groups/{group_id}
POST /groups

Assignments
GET /assignments
GET /assignments/{assignment_id}
POST /assignments

Submissions
GET /submissions
POST /submissions

Grades
GET /grades
POST /grades

Attendance
GET /attendance
POST /attendance

Chat
GET /chat-test
GET /chat-messages/{chat_room_id}
WebSocket /ws/chat/{chat_room_id}/{user_id}

Weekly Reports
GET /weekly-reports




9. Redis Caching
Redis is used to cache the course list.

Caching endpoints:
GET /courses-no-cache
GET /courses-cached

Measured result:
Without cache: 14.25 ms
With Redis cache: 0.52 ms

Redis caching improved response time by approximately 27 times.




10. WebSocket Chat
The system supports real-time chat using WebSocket.

WebSocket endpoint:
/ws/chat/{chat_room_id}/{user_id}

Test page:
/chat-test

Chat messages are saved into PostgreSQL and can be retrieved using:
GET /chat-messages/{chat_room_id}




11. From-Scratch Component
The from-scratch component is a token-bucket rate limiter.

File:
backend/app/rate_limiter.py

Purpose:
Prevents users from sending too many chat messages quickly
Protects the chat system from spam
Limits excessive WebSocket message sending

Configuration:
Capacity: 5 tokens
Refill rate: 0.5 tokens per second

If the user sends too many messages, the system returns:
Too many messages. Please wait before sending again.




12. Batch Pipeline
The system includes a weekly report batch pipeline.

File:
backend/app/batch_worker.py

The batch worker calculates:
attendance percentage
average score
submitted assignments
total assignments

Run command:
docker compose exec backend python app/batch_worker.py --week-start 2026-05-04

Generated reports are stored in:
weekly_reports




13. Observability
The system includes basic observability features:
Health check
GET /health
Metrics endpoint
GET /metrics

Metrics include:
total requests
total errors
average response time
Backend logs

Check logs using:
docker compose logs backend --tail=20




14. Database Migrations
Migration files:

001_init.sql
002_seed.sql
003_indexes.sql

Purpose:
001_init.sql creates database tables and relationships
002_seed.sql inserts sample data
003_indexes.sql creates indexes for optimization




15. GitHub Repository
Repository:
https://github.com/invalituser/ritor-school-lms




16. Author
RAHIMBEK RAJABBOEV
Student ID: U2210182

Database Application and Design Group Project


After saving README, run:
```powershell
git status

If README changed, run:
git add README.md
git commit -m "Add project README"
git push




