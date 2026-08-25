import streamlit as st
import sqlite3
import random
import hashlib
from datetime import datetime, date

DB = "mindsetu.db"

# ============================================================
# PAGE SETTINGS
# ============================================================
st.set_page_config(
    page_title="MINDSETU NER",
    page_icon="🧠",
    layout="wide"
)


# ============================================================
# DATABASE
# ============================================================
def db():
    conn = sqlite3.connect(DB, check_same_thread=False)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            language TEXT DEFAULT 'English',
            baseline REAL DEFAULT 0,
            role TEXT DEFAULT 'user'
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


# ============================================================
# PASSWORD
# ============================================================
def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# SESSION
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "login"


# ============================================================
# LOGIN / REGISTER PAGE
# ============================================================
if not st.session_state.logged_in:

    st.title("🧠 MINDSETU NER")

    st.caption(
        "Personalised AI Cognitive & Memory Companion — prototype"
    )

    st.info(
        "This is a wellness/support prototype. "
        "It does not diagnose dementia or replace a medical professional."
    )

    login_tab, signup_tab = st.tabs([
        "🔐 Login",
        "📝 Create Account"
    ])

    # ========================================================
    # LOGIN
    # ========================================================
    with login_tab:

        st.subheader("🔐 Login")

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            type="primary",
            key="login_button"
        ):

            # ------------------------------------------------
            # ADMIN LOGIN
            # ------------------------------------------------
            if username.strip().lower() == "durvesh":

                try:
                    admin_password = st.secrets[
                        "ADMIN_PASSWORD"
                    ]
                except Exception:
                    admin_password = None

                if admin_password is None:

                    st.error(
                        "Admin password is not configured."
                    )

                elif password == admin_password:

                    st.session_state.logged_in = True
                    st.session_state.user_id = 0
                    st.session_state.name = "Durvesh"
                    st.session_state.role = "admin"

                    st.rerun()

                else:

                    st.error(
                        "Incorrect admin password."
                    )

            # ------------------------------------------------
            # NORMAL USER LOGIN
            # ------------------------------------------------
            else:

                user = conn.execute("""
                    SELECT
                        id,
                        name,
                        username,
                        password_hash,
                        language,
                        baseline
                    FROM users_new
                    WHERE LOWER(username)=LOWER(?)
                """, (
                    username.strip(),
                )).fetchone()

                if user is None:

                    st.error(
                        "Username not found. "
                        "If you are a new user, use "
                        "'Create Account'."
                    )

                else:

                    uid, name, uname, saved_hash, language, baseline = user

                    if hash_password(password) == saved_hash:

                        st.session_state.logged_in = True
                        st.session_state.user_id = uid
                        st.session_state.name = name
                        st.session_state.role = "user"

                        st.rerun()

                    else:

                        st.error(
                            "Incorrect password."
                        )


    # ========================================================
    # CREATE ACCOUNT
    # ========================================================
    with signup_tab:

        st.subheader("📝 Create Your Account")

        st.write(
            "Anyone with the app link can create an account."
        )

        new_name = st.text_input(
            "Your Name",
            key="signup_name"
        )

        new_username = st.text_input(
            "Choose Username",
            key="signup_username"
        )

        new_password = st.text_input(
            "Choose Password",
            type="password",
            key="signup_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="signup_confirm"
        )

        language = st.selectbox(
            "Language",
            [
                "English",
                "Hindi",
                "Marathi"
            ],
            key="signup_language"
        )

        if st.button(
            "Create Account",
            type="primary",
            key="signup_button"
        ):

            if not new_name.strip():

                st.error(
                    "Please enter your name."
                )

            elif not new_username.strip():

                st.error(
                    "Please choose a username."
                )

            elif new_username.strip().lower() == "durvesh":

                st.error(
                    "That username is reserved."
                )

            elif not new_password:

                st.error(
                    "Please create a password."
                )

            elif len(new_password) < 6:

                st.error(
                    "Password must contain at least 6 characters."
                )

            elif new_password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                existing = conn.execute("""
                    SELECT id
                    FROM users_new
                    WHERE LOWER(username)=LOWER(?)
                """, (
                    new_username.strip(),
                )).fetchone()

                if existing:

                    st.error(
                        "Username already exists. "
                        "Please choose another username."
                    )

                else:

                    conn.execute("""
                        INSERT INTO users_new(
                            name,
                            username,
                            password_hash,
                            language,
                            role
                        )
                        VALUES (?, ?, ?, ?, 'user')
                    """, (
                        new_name.strip(),
                        new_username.strip(),
                        hash_password(new_password),
                        language
                    ))

                    conn.commit()

                    st.success(
                        "✅ Account created successfully!"
                    )

                    st.info(
                        "Now go to the Login tab and sign in."
                    )

    st.stop()


# ============================================================
# CURRENT USER
# ============================================================
uid = st.session_state.user_id
name = st.session_state.name
role = st.session_state.role


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:

    st.header("Account")

    st.write(
        f"👤 **{name}**"
    )

    if role == "admin":

        st.success("👑 Administrator")

    else:

        st.info("👤 User")

    if st.button("Logout"):

        st.session_state.clear()
        st.rerun()


# ============================================================
# HELPERS
# ============================================================
def get_sessions(user_id):

    return conn.execute("""
        SELECT
            game,
            score,
            difficulty,
            created_at
        FROM sessions
        WHERE user_id=?
        ORDER BY id DESC
    """, (
        user_id,
    )).fetchall()


def get_baseline(user_id):

    rows = conn.execute("""
        SELECT score
        FROM sessions
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (
        user_id,
    )).fetchall()

    if not rows:
        return 0.0

    return round(
        sum(float(r[0]) for r in rows) / len(rows),
        1
    )


def adaptive_difficulty(user_id):

    baseline = get_baseline(user_id)

    if baseline == 0:
        return 1

    if baseline >= 85:
        return 3

    if baseline >= 65:
        return 2

    return 1


def save_score(
    user_id,
    game,
    score,
    difficulty
):

    conn.execute("""
        INSERT INTO sessions(
            user_id,
            game,
            score,
            difficulty,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        game,
        score,
        difficulty,
        datetime.now().isoformat(
            timespec="seconds"
        )
    ))

    conn.commit()


def unusual_change(user_id):

    rows = conn.execute("""
        SELECT score
        FROM sessions
        WHERE user_id=?
        ORDER BY id DESC
    """, (
        user_id,
    )).fetchall()

    scores = [
        float(r[0])
        for r in rows
    ]

    if len(scores) < 5:

        return (
            False,
            "Not enough history yet."
        )

    recent = sum(scores[:3]) / 3

    older_scores = scores[3:6]

    older = (
        sum(older_scores) /
        len(older_scores)
    )

    if older >= 1 and recent < older * 0.75:

        return (
            True,
            "Recent performance is noticeably "
            "lower than the user's recent baseline. "
            "Caregiver review is recommended."
        )

    return (
        False,
        "No major change detected."
    )


# ============================================================
# STYLE
# ============================================================
st.markdown("""
<style>
.main {
    background:#07121f;
}

h1,h2,h3 {
    color:#34d399;
}

div[data-testid="stMetricValue"] {
    color:#38bdf8;
}

button[kind="primary"] {
    background:#34d399;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# ADMIN DASHBOARD
# ============================================================
if role == "admin":

    st.title("🧠 MINDSETU NER")

    st.caption(
        "Administrator Dashboard"
    )

    st.success(
        "👑 You are the administrator. "
        "You can see everyone's history."
    )

    tabs = st.tabs([
        "🏠 Home",
        "👥 Users",
        "📊 All History"
    ])

    # --------------------------------------------------------
    # ADMIN HOME
    # --------------------------------------------------------
    with tabs[0]:

        total_users = conn.execute("""
            SELECT COUNT(*)
            FROM users_new
        """).fetchone()[0]

        total_sessions = conn.execute("""
            SELECT COUNT(*)
            FROM sessions
        """).fetchone()[0]

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Users",
            total_users
        )

        c2.metric(
            "Total Sessions",
            total_sessions
        )

        st.write(
            "### 👥 Public Registration"
        )

        st.info(
            "Anyone who has your app link can create "
            "their own account from the Create Account tab."
        )


    # --------------------------------------------------------
    # ALL USERS
    # --------------------------------------------------------
    with tabs[1]:

        st.subheader(
            "👥 Registered Users"
        )

        users = conn.execute("""
            SELECT
                name,
                username,
                language,
                baseline
            FROM users_new
            ORDER BY name
        """).fetchall()

        if users:

            data = []

            for user in users:

                session_count = conn.execute("""
                    SELECT COUNT(*)
                    FROM sessions
                    WHERE user_id=(
                        SELECT id
                        FROM users_new
                        WHERE username=?
                    )
                """, (
                    user[1],
                )).fetchone()[0]

                data.append({
                    "Name": user[0],
                    "Username": user[1],
                    "Language": user[2],
                    "Baseline": user[3],
                    "Sessions": session_count
                })

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No users have registered yet."
            )


    # --------------------------------------------------------
    # ALL HISTORY
    # --------------------------------------------------------
    with tabs[2]:

        st.subheader(
            "📊 All Users History"
        )

        history = conn.execute("""
            SELECT
                users_new.name,
                users_new.username,
                sessions.game,
                sessions.score,
                sessions.difficulty,
                sessions.created_at
            FROM sessions
            JOIN users_new
            ON sessions.user_id = users_new.id
            ORDER BY sessions.id DESC
        """).fetchall()

        if history:

            data = []

            for row in history:

                data.append({
                    "User": row[0],
                    "Username": row[1],
                    "Game": row[2],
                    "Score": row[3],
                    "Difficulty": row[4],
                    "Time": row[5]
                })

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No history available yet."
            )

    st.stop()


# ============================================================
# NORMAL USER
# ============================================================
user = conn.execute("""
    SELECT
        id,
        name,
        language,
        baseline
    FROM users_new
    WHERE id=?
""", (
    uid,
)).fetchone()


if user is None:

    st.error(
        "User account not found."
    )

    st.stop()


uid, name, lang, baseline = user

difficulty = adaptive_difficulty(uid)


# ============================================================
# USER APP
# ============================================================
st.title("🧠 MINDSETU NER")

st.caption(
    "Personalised AI Cognitive & Memory Companion — prototype"
)

st.info(
    "This is a wellness/support prototype. "
    "It does not diagnose dementia or replace a medical professional."
)


tabs = st.tabs([
    "🏠 Home",
    "🎮 Cognitive Games",
    "⏰ Reminders",
    "📜 My History",
    "👨‍👩‍👧 My Dashboard"
])


# ============================================================
# HOME
# ============================================================
with tabs[0]:

    st.subheader(
        f"Welcome, {name} 👋"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Personal Baseline",
        f"{baseline:.1f}"
    )

    c2.metric(
        "Current Difficulty",
        difficulty
    )

    c3.metric(
        "Sessions",
        len(get_sessions(uid))
    )

    changed, message = unusual_change(uid)

    if changed:

        st.warning(
            "⚠️ " + message
        )

    else:

        st.success(
            "✅ " + message
        )

    st.write(
        "### Today's plan"
    )

    st.write(
        "1. 5-minute memory activity"
    )

    st.write(
        "2. Daily reminder check"
    )

    st.write(
        "3. Optional caregiver review"
    )

    st.caption(
        "🔒 Your history is private and can only be seen by you."
    )


# ============================================================
# GAMES
# ============================================================
with tabs[1]:

    st.subheader(
        "🎮 Adaptive Cognitive Games"
    )

    st.write(
        f"Current difficulty: **{difficulty}**"
    )

    # --------------------------------------------------------
    # MEMORY GAME
    # --------------------------------------------------------
    if "sequence" not in st.session_state:
        st.session_state.sequence = None

    if "game_started" not in st.session_state:
        st.session_state.game_started = False

    st.markdown(
        "#### Memory Sequence"
    )

    length = {
        1: 4,
        2: 6,
        3: 8
    }[difficulty]

    if not st.session_state.game_started:

        if st.button(
            "Start Memory Game",
            type="primary"
        ):

            st.session_state.sequence = random.sample(
                range(1, 10),
                length
            )

            st.session_state.game_started = True

            st.rerun()

    else:

        seq = st.session_state.sequence

        st.success(
            "Remember this sequence:"
        )

        st.markdown(
            "### " +
            " • ".join(
                map(str, seq)
            )
        )

        answer = st.text_input(
            "Your answer",
            placeholder="Example: 3 8 1 7"
        )

        if st.button(
            "Submit Answer"
        ):

            try:

                user_seq = [
                    int(x)
                    for x in answer.replace(
                        ",",
                        " "
                    ).split()
                ]

                correct = sum(
                    a == b
                    for a, b in zip(
                        seq,
                        user_seq
                    )
                )

                score = round(
                    100 *
                    correct /
                    max(len(seq), 1),
                    1
                )

                if user_seq == seq:

                    st.success(
                        f"Excellent! Score: {score}"
                    )

                else:

                    st.warning(
                        f"Good attempt. Score: {score}"
                    )

                save_score(
                    uid,
                    "Memory Sequence",
                    score,
                    difficulty
                )

                st.session_state.game_started = False
                st.session_state.sequence = None

                st.rerun()

            except ValueError:

                st.error(
                    "Please enter numbers separated by spaces."
                )


    st.divider()


    # --------------------------------------------------------
    # PATTERN GAME
    # --------------------------------------------------------
    st.markdown(
        "#### Pattern Recall"
    )

    if "pattern" not in st.session_state:
        st.session_state.pattern = None

    if st.button(
        "Generate Pattern"
    ):

        size = {
            1: 3,
            2: 4,
            3: 5
        }[difficulty]

        st.session_state.pattern = random.choices(
            ["▲", "●", "■", "★"],
            k=size
        )

    pattern = st.session_state.pattern

    if pattern:

        st.write(
            "Remember:"
        )

        st.markdown(
            "### " +
            " ".join(pattern)
        )

        user_pattern = st.text_input(
            "Type the pattern using ▲ ● ■ ★",
            key="pattern_input"
        )

        if st.button(
            "Check Pattern"
        ):

            entered = user_pattern.split()

            score = round(
                100 *
                sum(
                    a == b
                    for a, b in zip(
                        pattern,
                        entered
                    )
                )
                /
                max(len(pattern), 1),
                1
            )

            st.write(
                f"Score: **{score}**"
            )

            save_score(
                uid,
                "Pattern Recall",
                score,
                difficulty
            )

            st.session_state.pattern = None

            st.rerun()


# ============================================================
# REMINDERS
# ============================================================
with tabs[2]:

    st.subheader(
        "⏰ Daily Routine & Reminders"
    )

    st.write(
        "Add medicine, hydration, appointment or activity reminders."
    )

    rtitle = st.text_input(
        "Reminder title",
        placeholder="Drink water"
    )

    rtime = st.time_input(
        "Time"
    )

    if st.button(
        "Add Reminder",
        type="primary"
    ):

        if rtitle.strip():

            due = (
                f"{date.today().isoformat()} "
                f"{rtime.strftime('%H:%M')}"
            )

            conn.execute("""
                INSERT INTO reminders(
                    user_id,
                    title,
                    due_time,
                    status
                )
                VALUES (?, ?, ?, 'Pending')
            """, (
                uid,
                rtitle.strip(),
                due
            ))

            conn.commit()

            st.success(
                "Reminder added."
            )

            st.rerun()


    rows = conn.execute("""
        SELECT
            id,
            title,
            due_time,
            status
        FROM reminders
        WHERE user_id=?
        ORDER BY due_time
    """, (
        uid,
    )).fetchall()


    st.write(
        "### Your reminders"
    )

    for rid, title, due, status in rows:

        c1, c2, c3 = st.columns(
            [4, 2, 1]
        )

        c1.write(title)
        c2.write(due)

        if status == "Done":

            c3.success("Done")

        else:

            if c3.button(
                "Done",
                key=f"done_{rid}"
            ):

                conn.execute("""
                    UPDATE reminders
                    SET status='Done'
                    WHERE id=?
                    AND user_id=?
                """, (
                    rid,
                    uid
                ))

                conn.commit()

                st.rerun()


# ============================================================
# MY HISTORY
# ============================================================
with tabs[3]:

    st.subheader(
        "📜 My History"
    )

    st.success(
        "🔒 Only your own history is shown here."
    )

    sessions = get_sessions(uid)

    if sessions:

        st.dataframe(
            [
                {
                    "Game": r[0],
                    "Score": r[1],
                    "Difficulty": r[2],
                    "Time": r[3]
                }
                for r in sessions
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Complete a game to create your history."
        )


# ============================================================
# MY DASHBOARD
# ============================================================
with tabs[4]:

    st.subheader(
        "👨‍👩‍👧 My Dashboard"
    )

    st.write(
        f"Monitoring: **{name}**"
    )

    sessions = get_sessions(uid)

    if sessions:

        scores = [
            r[1]
            for r in sessions
        ]

        avg = sum(scores) / len(scores)

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Average Score",
            f"{avg:.1f}"
        )

        c2.metric(
            "Best Score",
            f"{max(scores):.1f}"
        )

        c3.metric(
            "Completed Sessions",
            len(scores)
        )

        changed, message = unusual_change(uid)

        if changed:

            st.warning(
                "Caregiver attention suggested: "
                + message
            )

        else:

            st.success(
                "No unusual recent change detected."
            )

    else:

        st.info(
            "Complete a few cognitive sessions "
            "to populate the dashboard."
        )

    st.caption(
        "This dashboard is for supportive monitoring only; "
        "unusual changes should be reviewed by an appropriate "
        "healthcare professional."
    )
