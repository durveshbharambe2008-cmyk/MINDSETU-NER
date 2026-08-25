import streamlit as st
import sqlite3
import random
import time
from datetime import datetime, date, timedelta

DB = "mindsetu.db"

# -----------------------------
# Database
# -----------------------------
def db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            language TEXT DEFAULT 'English',
            baseline REAL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game TEXT,
            score REAL,
            difficulty INTEGER,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            due_time TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
    conn.commit()
    return conn

conn = db()

# -----------------------------
# Helpers
# -----------------------------
def current_user():
    uid = st.session_state.get("user_id")
    if uid is None:
        return None
    return conn.execute("SELECT id, name, language, baseline FROM users WHERE id=?",
                        (uid,)).fetchone()

def get_sessions(uid):
    return conn.execute("""
        SELECT game, score, difficulty, created_at
        FROM sessions
        WHERE user_id=?
        ORDER BY id DESC
    """, (uid,)).fetchall()

def get_baseline(uid):
    rows = conn.execute("""
        SELECT score FROM sessions
        WHERE user_id=?
        ORDER BY id DESC LIMIT 10
    """, (uid,)).fetchall()
    if not rows:
        return 0.0
    return round(sum(r[0] for r in rows) / len(rows), 1)

def adaptive_difficulty(uid):
    baseline = get_baseline(uid)
    if baseline == 0:
        return 1
    if baseline >= 85:
        return 3
    if baseline >= 65:
        return 2
    return 1

def save_score(uid, game, score, difficulty):
    conn.execute("""
        INSERT INTO sessions(user_id, game, score, difficulty, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (uid, game, score, difficulty, datetime.now().isoformat(timespec="seconds")))
    conn.execute("UPDATE users SET baseline=? WHERE id=?", (get_baseline(uid), uid))
    conn.commit()

def recent_scores(uid):
    return [r[0] for r in get_sessions(uid)]

def unusual_change(uid):
    scores = recent_scores(uid)
    if len(scores) < 5:
        return False, "Not enough history yet."
    recent = sum(scores[:3]) / 3
    older = sum(scores[3:6]) / max(1, len(scores[3:6]))
    if older >= 1 and recent < older * 0.75:
        return True, "Recent performance is noticeably lower than the user's recent baseline. Caregiver review is recommended."
    return False, "No major change detected."

# -----------------------------
# UI
# -----------------------------
st.set_page_config(
    page_title="MINDSETU NER",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
.main {background:#07121f;}
h1,h2,h3 {color:#34d399;}
div[data-testid="stMetricValue"] {color:#38bdf8;}
button[kind="primary"] {background:#34d399;}
.small-note {color:#a6b9c9;font-size:13px;}
</style>
""", unsafe_allow_html=True)

st.title("🧠 MINDSETU NER")
st.caption("Personalised AI Cognitive & Memory Companion — prototype")
st.info("This is a wellness/support prototype. It does not diagnose dementia or replace a medical professional.")

# -----------------------------
# Login / user selection
# -----------------------------
users = conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()

with st.sidebar:
    st.header("User")
    if users:
        names = {name: uid for uid, name in users}
        selected = st.selectbox("Select user", list(names.keys()))
        st.session_state["user_id"] = names[selected]
    else:
        st.warning("Create the first user below.")

    st.divider()
    st.subheader("Create user")
    new_name = st.text_input("Name")
    language = st.selectbox("Language", ["English", "Hindi", "Marathi"])
    if st.button("Create User", type="primary"):
        if new_name.strip():
            cur = conn.execute("INSERT INTO users(name, language) VALUES (?, ?)",
                               (new_name.strip(), language))
            conn.commit()
            st.session_state["user_id"] = cur.lastrowid
            st.success("User created.")
            st.rerun()

user = current_user()

if user is None:
    st.stop()

uid, name, lang, baseline = user
difficulty = adaptive_difficulty(uid)

# -----------------------------
# Dashboard
# -----------------------------
tabs = st.tabs(["🏠 Home", "🎮 Cognitive Games", "⏰ Reminders", "👨‍👩‍👧 Caregiver Dashboard"])

with tabs[0]:
    st.subheader(f"Welcome, {name} 👋")
    c1, c2, c3 = st.columns(3)
    c1.metric("Personal Baseline", f"{baseline:.1f}")
    c2.metric("Current Difficulty", str(difficulty))
    c3.metric("Sessions", str(len(get_sessions(uid))))

    changed, message = unusual_change(uid)
    if changed:
        st.warning("⚠️ " + message)
    else:
        st.success("✅ " + message)

    st.write("### Today's plan")
    st.write("1. 5-minute memory activity")
    st.write("2. Daily reminder check")
    st.write("3. Optional caregiver review")

    st.caption("The app compares the user with their own previous activity, not with other people.")

# -----------------------------
# Game 1: Memory Sequence
# -----------------------------
with tabs[1]:
    st.subheader("🎮 Adaptive Cognitive Games")
    st.write(f"Current difficulty: **{difficulty}**")

    if "sequence" not in st.session_state:
        st.session_state.sequence = None
    if "game_started" not in st.session_state:
        st.session_state.game_started = False

    st.markdown("#### Memory Sequence")
    length = {1: 4, 2: 6, 3: 8}[difficulty]

    if not st.session_state.game_started:
        if st.button("Start Memory Game", type="primary"):
            seq = random.sample(range(1, 10), length)
            st.session_state.sequence = seq
            st.session_state.game_started = True
            st.rerun()
    else:
        seq = st.session_state.sequence
        st.success("Remember this sequence:")
        st.markdown("### " + "  •  ".join(map(str, seq)))
        st.write("After memorising it, enter the numbers in the same order.")

        answer = st.text_input("Your answer", placeholder="Example: 3 8 1 7")
        if st.button("Submit Answer"):
            try:
                user_seq = [int(x) for x in answer.replace(",", " ").split()]
                correct = sum(a == b for a, b in zip(seq, user_seq))
                score = round(100 * correct / max(len(seq), 1), 1)
                if user_seq == seq:
                    st.success(f"Excellent! Score: {score}")
                else:
                    st.warning(f"Good attempt. Score: {score}")
                save_score(uid, "Memory Sequence", score, difficulty)
                st.session_state.game_started = False
                st.session_state.sequence = None
            except ValueError:
                st.error("Please enter numbers separated by spaces.")

    st.divider()

    # Game 2: Pattern
    st.markdown("#### Pattern Recall")
    if "pattern" not in st.session_state:
        st.session_state.pattern = None
    if st.button("Generate Pattern"):
        size = {1: 3, 2: 4, 3: 5}[difficulty]
        st.session_state.pattern = random.choices(
            ["▲", "●", "■", "★"], k=size
        )

    pattern = st.session_state.pattern
    if pattern:
        st.write("Remember:")
        st.markdown("### " + " ".join(pattern))
        user_pattern = st.text_input("Type the pattern using ▲ ● ■ ★", key="pattern_input")
        if st.button("Check Pattern"):
            entered = user_pattern.split()
            score = round(100 * sum(a == b for a, b in zip(pattern, entered)) / len(pattern), 1)
            st.write(f"Score: **{score}**")
            save_score(uid, "Pattern Recall", score, difficulty)
            st.session_state.pattern = None

# -----------------------------
# Reminders
# -----------------------------
with tabs[2]:
    st.subheader("⏰ Daily Routine & Reminders")
    st.write("Add medicine, hydration, appointment or activity reminders.")

    rtitle = st.text_input("Reminder title", placeholder="Drink water")
    rtime = st.time_input("Time")
    if st.button("Add Reminder", type="primary"):
        if rtitle.strip():
            due = f"{date.today().isoformat()} {rtime.strftime('%H:%M')}"
            conn.execute("""
                INSERT INTO reminders(user_id, title, due_time, status)
                VALUES (?, ?, ?, 'Pending')
            """, (uid, rtitle.strip(), due))
            conn.commit()
            st.success("Reminder added.")

    rows = conn.execute("""
        SELECT id, title, due_time, status
        FROM reminders
        WHERE user_id=?
        ORDER BY due_time
    """, (uid,)).fetchall()

    st.write("### Your reminders")
    for rid, title, due, status in rows:
        c1, c2, c3 = st.columns([4, 2, 1])
        c1.write(title)
        c2.write(due)
        if status == "Done":
            c3.success("Done")
        else:
            if c3.button("Done", key=f"done_{rid}"):
                conn.execute("UPDATE reminders SET status='Done' WHERE id=?", (rid,))
                conn.commit()
                st.rerun()

# -----------------------------
# Caregiver dashboard
# -----------------------------
with tabs[3]:
    st.subheader("👨‍👩‍👧 Caregiver Dashboard")
    st.write(f"Monitoring: **{name}**")

    sessions = get_sessions(uid)
    if sessions:
        scores = [r[1] for r in sessions]
        games = [r[0] for r in sessions]
        avg = sum(scores) / len(scores)

        c1, c2, c3 = st.columns(3)
        c1.metric("Average Score", f"{avg:.1f}")
        c2.metric("Best Score", f"{max(scores):.1f}")
        c3.metric("Completed Sessions", len(scores))

        st.write("### Recent activity")
        st.dataframe(
            [{"Game": r[0], "Score": r[1], "Difficulty": r[2], "Time": r[3]}
             for r in sessions[:10]],
            use_container_width=True
        )

        changed, message = unusual_change(uid)
        if changed:
            st.warning("Caregiver attention suggested: " + message)
        else:
            st.success("No unusual recent change detected.")
    else:
        st.info("Complete a few cognitive sessions to populate the dashboard.")

    st.caption("This dashboard is for supportive monitoring only; unusual changes should be reviewed by an appropriate healthcare professional.")
