"""Database layer. MySQL (PyMySQL) is the main store; SQLite is a zero-setup fallback
so the demo runs anywhere. All SQL is written with '?' placeholders and converted for MySQL."""
import os
import sqlite3
from flask import g

BACKEND = os.getenv("DB_BACKEND", "sqlite").lower()
SQLITE_PATH = os.getenv("SQLITE_PATH", os.path.join(os.path.dirname(__file__), "roleready.db"))

PK = "INT AUTO_INCREMENT PRIMARY KEY" if BACKEND == "mysql" else "INTEGER PRIMARY KEY AUTOINCREMENT"

SCHEMA = [
    f"""CREATE TABLE IF NOT EXISTS students (
        id {PK}, name VARCHAR(100) NOT NULL, email VARCHAR(120) NOT NULL UNIQUE,
        degree VARCHAR(80), branch VARCHAR(80), grad_year INT, cgpa FLOAT,
        skills TEXT, pref_companies TEXT, pref_roles TEXT, pref_locations TEXT,
        created_at VARCHAR(30))""",
    f"""CREATE TABLE IF NOT EXISTS opportunities (
        id {PK}, company VARCHAR(80) NOT NULL, role VARCHAR(80) NOT NULL, type VARCHAR(20),
        location VARCHAR(80), skills TEXT, min_cgpa FLOAT, branches TEXT, grad_year INT,
        stipend VARCHAR(40), deadline VARCHAR(10), apply_link VARCHAR(255), description TEXT)""",
    f"""CREATE TABLE IF NOT EXISTS applications (
        id {PK}, student_id INT NOT NULL, opportunity_id INT NOT NULL,
        status VARCHAR(20) NOT NULL, notes TEXT, updated_at VARCHAR(30),
        UNIQUE (student_id, opportunity_id))""",
    f"""CREATE TABLE IF NOT EXISTS resume_analyses (
        id {PK}, student_id INT NOT NULL, data LONGTEXT, created_at VARCHAR(30))"""
    if BACKEND == "mysql" else
    f"""CREATE TABLE IF NOT EXISTS resume_analyses (
        id {PK}, student_id INT NOT NULL, data TEXT, created_at VARCHAR(30))""",
    """CREATE TABLE IF NOT EXISTS skill_hours (skill VARCHAR(60) PRIMARY KEY, hours FLOAT NOT NULL)""",
    f"""CREATE TABLE IF NOT EXISTS skill_tests (
        id {PK}, student_id INT NOT NULL, skill VARCHAR(60) NOT NULL, score INT NOT NULL,
        total INT NOT NULL, created_at VARCHAR(30))""",
]

# Columns added after the first release (applied to existing databases too).
MIGRATIONS = ["ALTER TABLE students ADD COLUMN weekly_hours INT DEFAULT 10"]


def _connect():
    if BACKEND == "mysql":
        import pymysql
        return pymysql.connect(
            host=os.getenv("MYSQL_HOST", "localhost"), user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""), database=os.getenv("MYSQL_DB", "roleready"),
            charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def conn():
    if "db" not in g:
        g.db = _connect()
    return g.db


def close(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _sql(sql):
    return sql.replace("?", "%s") if BACKEND == "mysql" else sql


def query(sql, args=(), one=False):
    c = conn()
    if BACKEND == "mysql":
        with c.cursor() as cur:
            cur.execute(_sql(sql), args)
            rows = cur.fetchall()
    else:
        rows = [dict(r) for r in c.execute(sql, args).fetchall()]
    return (rows[0] if rows else None) if one else rows


def execute(sql, args=()):
    c = conn()
    if BACKEND == "mysql":
        with c.cursor() as cur:
            cur.execute(_sql(sql), args)
            last = cur.lastrowid
    else:
        last = c.execute(sql, args).lastrowid
    c.commit()
    return last


def init_db():
    c = _connect()
    cur = c.cursor()
    for stmt in SCHEMA:
        cur.execute(stmt)
    c.commit()
    for stmt in MIGRATIONS:
        try:
            cur.execute(stmt)
            c.commit()
        except Exception:  # column already exists
            if BACKEND == "mysql":
                c.rollback()
    for stmt in MIGRATIONS:
        try:
            cur.execute(stmt)
            c.commit()
        except Exception:  # column already exists
            if BACKEND == "mysql":
                c.rollback()
    c.close()
