import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = "language_manager.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS languages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        color TEXT DEFAULT '#3498db',
        icon TEXT DEFAULT '🌐',
        level TEXT DEFAULT 'Beginner',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        language_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT DEFAULT 'Book',
        total_units INTEGER DEFAULT 0,
        completed_units INTEGER DEFAULT 0,
        status TEXT DEFAULT 'In Progress',
        started_at TEXT,
        finished_at TEXT,
        notes TEXT,
        FOREIGN KEY (language_id) REFERENCES languages(id)
    );

    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        language_id INTEGER NOT NULL,
        resource_id INTEGER,
        date TEXT NOT NULL,
        duration_minutes INTEGER DEFAULT 0,
        unit_lesson TEXT,
        topic TEXT,
        skills TEXT,
        new_words_count INTEGER DEFAULT 0,
        new_grammar_count INTEGER DEFAULT 0,
        difficulty INTEGER DEFAULT 3,
        feeling INTEGER DEFAULT 3,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (language_id) REFERENCES languages(id),
        FOREIGN KEY (resource_id) REFERENCES resources(id)
    );

    CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        language_id INTEGER NOT NULL,
        word TEXT NOT NULL,
        meaning TEXT,
        article TEXT,
        plural TEXT,
        pronunciation TEXT,
        part_of_speech TEXT,
        example_sentence TEXT,
        collocations TEXT,
        tags TEXT,
        difficulty INTEGER DEFAULT 3,
        status TEXT DEFAULT 'New',
        ease_factor REAL DEFAULT 2.5,
        interval_days INTEGER DEFAULT 1,
        repetitions INTEGER DEFAULT 0,
        last_reviewed TEXT,
        next_review TEXT,
        success_count INTEGER DEFAULT 0,
        failure_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (language_id) REFERENCES languages(id)
    );

    CREATE TABLE IF NOT EXISTS grammar_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        language_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT,
        explanation TEXT,
        examples TEXT,
        rules TEXT,
        resource TEXT,
        status TEXT DEFAULT 'Not Started',
        mastery_percent INTEGER DEFAULT 0,
        review_count INTEGER DEFAULT 0,
        last_reviewed TEXT,
        next_review TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (language_id) REFERENCES languages(id)
    );

    CREATE TABLE IF NOT EXISTS sentences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        language_id INTEGER NOT NULL,
        sentence TEXT NOT NULL,
        meaning TEXT,
        category TEXT,
        tags TEXT,
        source TEXT,
        status TEXT DEFAULT 'Learning',
        last_reviewed TEXT,
        next_review TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (language_id) REFERENCES languages(id)
    );

    CREATE TABLE IF NOT EXISTS error_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        language_id INTEGER NOT NULL,
        category TEXT,
        wrong_form TEXT NOT NULL,
        correct_form TEXT NOT NULL,
        explanation TEXT,
        source TEXT,
        frequency INTEGER DEFAULT 1,
        status TEXT DEFAULT 'Active',
        last_reviewed TEXT,
        next_review TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (language_id) REFERENCES languages(id)
    );

    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        language_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        goal_type TEXT DEFAULT 'Short-term',
        target_value INTEGER DEFAULT 0,
        current_value INTEGER DEFAULT 0,
        unit TEXT,
        deadline TEXT,
        status TEXT DEFAULT 'Active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS daily_checklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        language_id INTEGER NOT NULL,
        task TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        FOREIGN KEY (language_id) REFERENCES languages(id)
    );

    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        language_id INTEGER,
        title TEXT,
        content TEXT,
        category TEXT,
        tags TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Insert default languages if not exist
    cursor.execute("SELECT COUNT(*) FROM languages")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO languages (name, color, icon, level) VALUES
            ('English', '#2980b9', '🇺🇸', 'Intermediate'),
            ('German', '#27ae60', '🇩🇪', 'Beginner')
        """)

    # Insert default resources if not exist
    cursor.execute("SELECT COUNT(*) FROM resources")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO resources (language_id, name, type, total_units, status) VALUES
            (1, 'American English File 1', 'Book', 12, 'In Progress'),
            (1, 'American English File 2', 'Book', 12, 'Not Started'),
            (1, 'American English File 3', 'Book', 12, 'Not Started'),
            (1, 'American English File 4', 'Book', 12, 'Not Started'),
            (1, 'American English File 5', 'Book', 12, 'Not Started'),
            (2, 'Starten wir A1', 'Book', 12, 'In Progress'),
            (2, 'Starten wir A2', 'Book', 12, 'Not Started')
        """)

    conn.commit()
    conn.close()


# ============ CRUD Functions ============

# Languages
def get_languages():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM languages").fetchall()
    conn.close()
    return rows


def get_language_by_id(lang_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM languages WHERE id=?", (lang_id,)).fetchone()
    conn.close()
    return row


# Resources
def get_resources(language_id=None):
    conn = get_connection()
    if language_id:
        rows = conn.execute("SELECT * FROM resources WHERE language_id=?", (language_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM resources").fetchall()
    conn.close()
    return rows


def update_resource_progress(resource_id, completed_units):
    conn = get_connection()
    conn.execute("UPDATE resources SET completed_units=? WHERE id=?", (completed_units, resource_id))
    conn.commit()
    conn.close()


# Study Sessions
def add_study_session(language_id, resource_id, date, duration, unit_lesson, topic, skills,
                      new_words, new_grammar, difficulty, feeling, notes):
    conn = get_connection()
    conn.execute("""
        INSERT INTO study_sessions 
        (language_id, resource_id, date, duration_minutes, unit_lesson, topic, skills,
         new_words_count, new_grammar_count, difficulty, feeling, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (language_id, resource_id, date, duration, unit_lesson, topic, skills,
          new_words, new_grammar, difficulty, feeling, notes))
    conn.commit()
    conn.close()


def get_study_sessions(language_id=None, limit=50):
    conn = get_connection()
    if language_id:
        rows = conn.execute(
            "SELECT * FROM study_sessions WHERE language_id=? ORDER BY date DESC LIMIT ?",
            (language_id, limit)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM study_sessions ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return rows


def get_today_sessions():
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute("SELECT * FROM study_sessions WHERE date=?", (today,)).fetchall()
    conn.close()
    return rows


def get_total_study_time(language_id=None):
    conn = get_connection()
    if language_id:
        row = conn.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions WHERE language_id=?",
            (language_id,)).fetchone()
    else:
        row = conn.execute("SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions").fetchone()
    conn.close()
    return row[0]


def get_streak():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT date FROM study_sessions ORDER BY date DESC").fetchall()
    conn.close()

    if not rows:
        return 0

    streak = 0
    today = datetime.now().date()

    for row in rows:
        session_date = datetime.strptime(row['date'], "%Y-%m-%d").date()
        expected_date = today - timedelta(days=streak)
        if session_date == expected_date:
            streak += 1
        else:
            break

    return streak


# Vocabulary
def add_vocabulary(language_id, word, meaning, article, plural, pronunciation,
                   part_of_speech, example, collocations, tags, difficulty):
    conn = get_connection()
    next_review = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    conn.execute("""
        INSERT INTO vocabulary 
        (language_id, word, meaning, article, plural, pronunciation, part_of_speech,
         example_sentence, collocations, tags, difficulty, next_review)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (language_id, word, meaning, article, plural, pronunciation, part_of_speech,
          example, collocations, tags, difficulty, next_review))
    conn.commit()
    conn.close()


def get_vocabulary(language_id=None, status=None, search=None):
    conn = get_connection()
    query = "SELECT * FROM vocabulary WHERE 1=1"
    params = []

    if language_id:
        query += " AND language_id=?"
        params.append(language_id)
    if status:
        query += " AND status=?"
        params.append(status)
    if search:
        query += " AND (word LIKE ? OR meaning LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_vocabulary_for_review(language_id=None):
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    query = "SELECT * FROM vocabulary WHERE next_review <= ? AND status != 'Mastered'"
    params = [today]

    if language_id:
        query += " AND language_id=?"
        params.append(language_id)

    query += " ORDER BY next_review ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def update_vocabulary_review(vocab_id, success):
    conn = get_connection()
    row = conn.execute("SELECT * FROM vocabulary WHERE id=?", (vocab_id,)).fetchone()

    if not row:
        conn.close()
        return

    ease = row['ease_factor']
    interval = row['interval_days']
    reps = row['repetitions']
    success_count = row['success_count']
    failure_count = row['failure_count']

    if success:
        success_count += 1
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 3
        else:
            interval = int(interval * ease)
        reps += 1
        ease = max(1.3, ease + 0.1)
        status = 'Reviewing' if reps < 5 else 'Mastered'
    else:
        failure_count += 1
        interval = 1
        reps = 0
        ease = max(1.3, ease - 0.2)
        status = 'Learning'

    next_review = (datetime.now() + timedelta(days=interval)).strftime("%Y-%m-%d")
    last_reviewed = datetime.now().strftime("%Y-%m-%d")

    conn.execute("""
        UPDATE vocabulary SET 
        ease_factor=?, interval_days=?, repetitions=?, success_count=?, 
        failure_count=?, next_review=?, last_reviewed=?, status=?
        WHERE id=?
    """, (ease, interval, reps, success_count, failure_count,
          next_review, last_reviewed, status, vocab_id))
    conn.commit()
    conn.close()


def get_vocabulary_stats(language_id=None):
    conn = get_connection()
    stats = {}

    query_base = "SELECT COUNT(*) FROM vocabulary"
    if language_id:
        query_base += f" WHERE language_id={language_id}"
        stats['total'] = conn.execute(query_base).fetchone()[0]
        for s in ['New', 'Learning', 'Reviewing', 'Mastered']:
            stats[s.lower()] = conn.execute(
                f"SELECT COUNT(*) FROM vocabulary WHERE language_id=? AND status=?",
                (language_id, s)).fetchone()[0]
    else:
        stats['total'] = conn.execute(query_base).fetchone()[0]
        for s in ['New', 'Learning', 'Reviewing', 'Mastered']:
            stats[s.lower()] = conn.execute(
                f"SELECT COUNT(*) FROM vocabulary WHERE status=?", (s,)).fetchone()[0]

    conn.close()
    return stats


# Grammar
def add_grammar_topic(language_id, title, category, explanation, examples, rules, resource, notes):
    conn = get_connection()
    conn.execute("""
        INSERT INTO grammar_topics 
        (language_id, title, category, explanation, examples, rules, resource, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (language_id, title, category, explanation, examples, rules, resource, notes))
    conn.commit()
    conn.close()


def get_grammar_topics(language_id=None):
    conn = get_connection()
    if language_id:
        rows = conn.execute("SELECT * FROM grammar_topics WHERE language_id=? ORDER BY created_at DESC",
                            (language_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM grammar_topics ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def update_grammar_mastery(topic_id, mastery, status):
    conn = get_connection()
    conn.execute("UPDATE grammar_topics SET mastery_percent=?, status=? WHERE id=?",
                 (mastery, status, topic_id))
    conn.commit()
    conn.close()


# Sentences
def add_sentence(language_id, sentence, meaning, category, tags, source):
    conn = get_connection()
    conn.execute("""
        INSERT INTO sentences (language_id, sentence, meaning, category, tags, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (language_id, sentence, meaning, category, tags, source))
    conn.commit()
    conn.close()


def get_sentences(language_id=None):
    conn = get_connection()
    if language_id:
        rows = conn.execute("SELECT * FROM sentences WHERE language_id=? ORDER BY created_at DESC",
                            (language_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM sentences ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


# Error Log
def add_error(language_id, category, wrong_form, correct_form, explanation, source):
    conn = get_connection()
    next_review = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    conn.execute("""
        INSERT INTO error_log (language_id, category, wrong_form, correct_form, explanation, source, next_review)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (language_id, category, wrong_form, correct_form, explanation, source, next_review))
    conn.commit()
    conn.close()


def get_errors(language_id=None):
    conn = get_connection()
    if language_id:
        rows = conn.execute("SELECT * FROM error_log WHERE language_id=? ORDER BY created_at DESC",
                            (language_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM error_log ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def get_errors_for_review():
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute("SELECT * FROM error_log WHERE next_review <= ? AND status='Active'",
                        (today,)).fetchall()
    conn.close()
    return rows


# Goals
def add_goal(language_id, title, description, goal_type, target_value, unit, deadline):
    conn = get_connection()
    conn.execute("""
        INSERT INTO goals (language_id, title, description, goal_type, target_value, unit, deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (language_id, title, description, goal_type, target_value, unit, deadline))
    conn.commit()
    conn.close()


def get_goals(language_id=None, status='Active'):
    conn = get_connection()
    if language_id:
        rows = conn.execute("SELECT * FROM goals WHERE language_id=? AND status=? ORDER BY deadline",
                            (language_id, status)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM goals WHERE status=? ORDER BY deadline",
                            (status,)).fetchall()
    conn.close()
    return rows


def update_goal_progress(goal_id, current_value):
    conn = get_connection()
    goal = conn.execute("SELECT * FROM goals WHERE id=?", (goal_id,)).fetchone()
    status = 'Completed' if current_value >= goal['target_value'] else 'Active'
    conn.execute("UPDATE goals SET current_value=?, status=? WHERE id=?",
                 (current_value, status, goal_id))
    conn.commit()
    conn.close()


# Notes
def add_note(language_id, title, content, category, tags):
    conn = get_connection()
    conn.execute("""
        INSERT INTO notes (language_id, title, content, category, tags)
        VALUES (?, ?, ?, ?, ?)
    """, (language_id, title, content, category, tags))
    conn.commit()
    conn.close()


def get_notes(language_id=None):
    conn = get_connection()
    if language_id:
        rows = conn.execute("SELECT * FROM notes WHERE language_id=? ORDER BY created_at DESC",
                            (language_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM notes ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


# Stats
def get_weekly_stats():
    conn = get_connection()
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    stats = {
        'sessions': conn.execute(
            "SELECT COUNT(*) FROM study_sessions WHERE date >= ?", (week_ago,)).fetchone()[0],
        'total_time': conn.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions WHERE date >= ?",
            (week_ago,)).fetchone()[0],
        'new_words': conn.execute(
            "SELECT COUNT(*) FROM vocabulary WHERE created_at >= ?", (week_ago,)).fetchone()[0],
        'reviews_done': conn.execute(
            "SELECT COUNT(*) FROM vocabulary WHERE last_reviewed >= ?", (week_ago,)).fetchone()[0],
    }
    conn.close()
    return stats


def get_monthly_activity():
    conn = get_connection()
    month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    rows = conn.execute("""
        SELECT date, SUM(duration_minutes) as total_time, COUNT(*) as session_count
        FROM study_sessions WHERE date >= ?
        GROUP BY date ORDER BY date
    """, (month_ago,)).fetchall()
    conn.close()
    return rows