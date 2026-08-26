import streamlit as st
import sqlite3
import random
import hashlib
import io
import re
from datetime import datetime, date, time

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    mic_recorder = None


# ============================================================
# MINDSETU NER
# ============================================================

DB = "mindsetu.db"

st.set_page_config(
    page_title="MINDSETU NER",
    page_icon="🧠",
    layout="wide"
)


# ============================================================
# LANGUAGES
# ============================================================

LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr",
    "Bengali": "bn",
    "Gujarati": "gu",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Punjabi": "pa",
    "Urdu": "ur",
    "Odia": "or",
    "Assamese": "as",
    "Nepali": "ne",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Arabic": "ar",
    "Chinese": "zh-CN",
    "Japanese": "ja",
    "Korean": "ko",
    "Russian": "ru",
    "Turkish": "tr"
}


# ============================================================
# DATABASE
# ============================================================

def get_db():

    connection = sqlite3.connect(
        DB,
        check_same_thread=False
    )

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            language TEXT DEFAULT 'English',
            baseline REAL DEFAULT 0,
            role TEXT DEFAULT 'patient',
            doctor_id INTEGER
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game TEXT,
            score REAL,
            difficulty INTEGER,
            created_at TEXT
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            due_time TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            title TEXT,
            report_text TEXT,
            created_at TEXT,
            status TEXT DEFAULT 'Sent'
        )
    """)

    connection.commit()

    return connection


conn = get_db()


# ============================================================
# PASSWORD
# ============================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# VOICE
# ============================================================

def speak(text, language="English"):

    if not text:
        return

    if gTTS is None:
        return

    try:

        audio = io.BytesIO()

        gTTS(
            text=text,
            lang=LANGUAGES.get(language, "en"),
            slow=False
        ).write_to_fp(audio)

        audio.seek(0)

        st.audio(
            audio.read(),
            format="audio/mp3",
            autoplay=True
        )

    except Exception:
        pass


def voice_success(text, language="English"):

    st.success("🔊 " + text)

    speak(
        text,
        language
    )


def recognize_voice(audio_bytes, language):

    if sr is None:

        return None

    try:

        recognizer = sr.Recognizer()

        with sr.AudioFile(
            io.BytesIO(audio_bytes)
        ) as source:

            audio = recognizer.record(source)

        return recognizer.recognize_google(
            audio,
            language=LANGUAGES.get(
                language,
                "en"
            )
        ).lower()

    except Exception:

        return None


def parse_time(command):

    match = re.search(
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
        command
    )

    if match:

        return (
            f"{int(match.group(1)):02d}:"
            f"{int(match.group(2)):02d}"
        )

    return None


# ============================================================
# SESSION
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

if "user_id" not in st.session_state:
    st.session_state.user_id = None


# ============================================================
# LOGIN PAGE
# ============================================================

if not st.session_state.logged_in:

    st.title("🧠 MINDSETU NER")

    st.subheader(
        "Personalised AI Cognitive & Memory Companion"
    )

    st.info(
        "Supportive wellness prototype. "
        "It is not a medical diagnostic system."
    )

    login_tab, signup_tab = st.tabs(
        [
            "🔐 Login",
            "📝 Create Patient Account"
        ]
    )


    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Login",
            type="primary"
        ):

            # ADMIN LOGIN
            if username.lower() == "admin":

                if password == "admin123":

                    st.session_state.logged_in = True
                    st.session_state.role = "admin"
                    st.session_state.user_id = 0
                    st.session_state.name = "Administrator"
                    st.session_state.language = "English"

                    st.rerun()

                else:

                    st.error(
                        "Incorrect admin password."
                    )

            else:

                user = conn.execute(
                    """
                    SELECT
                        id,
                        name,
                        username,
                        password_hash,
                        language,
                        role,
                        doctor_id
                    FROM users
                    WHERE LOWER(username)=LOWER(?)
                    """,
                    (username.strip(),)
                ).fetchone()

                if user is None:

                    st.error(
                        "Username not found."
                    )

                elif hash_password(password) != user[3]:

                    st.error(
                        "Incorrect password."
                    )

                else:

                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.name = user[1]
                    st.session_state.language = user[4]
                    st.session_state.role = user[5]
                    st.session_state.doctor_id = user[6]

                    st.session_state.say_welcome = True

                    st.rerun()


    # ========================================================
    # CREATE ACCOUNT
    # ========================================================

    with signup_tab:

        name = st.text_input(
            "Full Name"
        )

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        confirm = st.text_input(
            "Confirm Password",
            type="password"
        )

        language = st.selectbox(
            "Select your language",
            list(LANGUAGES.keys())
        )

        if st.button(
            "Create Account",
            type="primary"
        ):

            if not name or not username or not password:

                st.error(
                    "Please fill all fields."
                )

            elif password != confirm:

                st.error(
                    "Passwords do not match."
                )

            elif len(password) < 6:

                st.error(
                    "Password must contain at least 6 characters."
                )

            else:

                existing = conn.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE LOWER(username)=LOWER(?)
                    """,
                    (username,)
                ).fetchone()

                if existing:

                    st.error(
                        "Username already exists."
                    )

                else:

                    conn.execute(
                        """
                        INSERT INTO users(
                            name,
                            username,
                            password_hash,
                            language,
                            role
                        )
                        VALUES(
                            ?,
                            ?,
                            ?,
                            ?,
                            'patient'
                        )
                        """,
                        (
                            name,
                            username,
                            hash_password(password),
                            language
                        )
                    )

                    conn.commit()

                    st.success(
                        "Account created successfully."
                    )

                    speak(
                        f"Welcome {name}. "
                        f"Your account was created successfully.",
                        language
                    )

    st.stop()


# ============================================================
# CURRENT USER
# ============================================================

role = st.session_state.role
user_id = st.session_state.user_id
name = st.session_state.name
language = st.session_state.get(
    "language",
    "English"
)


# ============================================================
# WELCOME VOICE
# ============================================================

if st.session_state.pop(
    "say_welcome",
    False
):

    voice_success(
        f"Welcome {name}. "
        f"You have logged in successfully.",
        language
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🧠 MINDSETU NER")

    st.write(
        f"👤 **{name}**"
    )

    if role == "admin":

        st.success(
            "👑 Administrator"
        )

    elif role == "doctor":

        st.success(
            "🩺 Doctor"
        )

    else:

        st.info(
            "👤 Patient"
        )


    # ========================================================
    # LANGUAGE
    # ========================================================

    st.subheader(
        "🌐 Language"
    )

    selected_language = st.selectbox(
        "Choose any language",
        list(LANGUAGES.keys()),
        index=list(
            LANGUAGES.keys()
        ).index(language)
    )

    if selected_language != language:

        if role != "admin":

            conn.execute(
                """
                UPDATE users
                SET language=?
                WHERE id=?
                """,
                (
                    selected_language,
                    user_id
                )
            )

            conn.commit()

            st.session_state.language = (
                selected_language
            )

            language = selected_language

            voice_success(
                f"Language changed to "
                f"{selected_language} successfully.",
                language
            )

            st.rerun()


    # ========================================================
    # VOICE COMMAND
    # ========================================================

    st.subheader(
        "🎤 Voice Commands"
    )

    if mic_recorder is None:

        st.warning(
            "Install streamlit-mic-recorder."
        )

    else:

        audio = mic_recorder(
            start_prompt="🎤 Start",
            stop_prompt="⏹ Stop",
            key="voice"
        )

        if audio:

            command = recognize_voice(
                audio["bytes"],
                language
            )

            if command:

                st.write(
                    f"**Command:** {command}"
                )

                if "logout" in command:

                    st.session_state.clear()

                    st.rerun()

                elif (
                    "game" in command
                    or "play" in command
                ):

                    st.session_state.page = "games"

                    voice_success(
                        "Opening cognitive games.",
                        language
                    )

                elif "reminder" in command:

                    st.session_state.page = "reminders"

                    due = parse_time(
                        command
                    )

                    if (
                        due
                        and (
                            "add" in command
                            or "set" in command
                        )
                    ):

                        title = (
                            command
                            .replace(
                                "add reminder",
                                ""
                            )
                            .replace(
                                "set reminder",
                                ""
                            )
                        )

                        conn.execute(
                            """
                            INSERT INTO reminders(
                                user_id,
                                title,
                                due_time,
                                status
                            )
                            VALUES(
                                ?,
                                ?,
                                ?,
                                'Pending'
                            )
                            """,
                            (
                                user_id,
                                title.strip().title(),
                                f"{date.today()} {due}"
                            )
                        )

                        conn.commit()

                        voice_success(
                            f"Reminder added "
                            f"successfully for {due}.",
                            language
                        )

                        st.rerun()

                elif "report" in command:

                    st.session_state.page = "reports"

                    voice_success(
                        "Opening reports.",
                        language
                    )

                elif (
                    "details" in command
                    or "my data" in command
                ):

                    st.session_state.page = "details"

                    voice_success(
                        "Opening your details.",
                        language
                    )


    if st.button("Logout"):

        st.session_state.clear()

        st.rerun()


# ============================================================
# ADMIN DASHBOARD
# ============================================================

if role == "admin":

    st.title(
        "👑 Administrator Dashboard"
    )

    st.success(
        "Administrator can view all system details "
        "and manage doctors."
    )

    tabs = st.tabs(
        [
            "🏠 Overview",
            "👥 Patients",
            "🩺 Doctors",
            "📊 All Sessions",
            "📄 Reports"
        ]
    )


    # ========================================================
    # OVERVIEW
    # ========================================================

    with tabs[0]:

        patients = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE role='patient'
            """
        ).fetchone()[0]

        doctors = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE role='doctor'
            """
        ).fetchone()[0]

        sessions = conn.execute(
            """
            SELECT COUNT(*)
            FROM sessions
            """
        ).fetchone()[0]

        reports = conn.execute(
            """
            SELECT COUNT(*)
            FROM reports
            """
        ).fetchone()[0]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Patients",
            patients
        )

        c2.metric(
            "Doctors",
            doctors
        )

        c3.metric(
            "Game Sessions",
            sessions
        )

        c4.metric(
            "Reports",
            reports
        )


    # ========================================================
    # PATIENTS
    # ========================================================

    with tabs[1]:

        rows = conn.execute(
            """
            SELECT
                id,
                name,
                username,
                language,
                baseline,
                doctor_id
            FROM users
            WHERE role='patient'
            ORDER BY name
            """
        ).fetchall()

        if rows:

            st.dataframe(
                [
                    {
                        "ID": r[0],
                        "Name": r[1],
                        "Username": r[2],
                        "Language": r[3],
                        "Baseline": r[4],
                        "Doctor ID": r[5] or "Not assigned"
                    }
                    for r in rows
                ],
                use_container_width=True
            )

        else:

            st.info(
                "No patients registered."
            )


    # ========================================================
    # DOCTORS
    # ========================================================

    with tabs[2]:

        st.subheader(
            "➕ Add Doctor"
        )

        doctor_name = st.text_input(
            "Doctor Name"
        )

        doctor_username = st.text_input(
            "Doctor Username"
        )

        doctor_password = st.text_input(
            "Doctor Password",
            type="password"
        )

        if st.button(
            "Add Doctor",
            type="primary"
        ):

            if (
                not doctor_name
                or not doctor_username
                or len(doctor_password) < 6
            ):

                st.error(
                    "Enter all doctor details."
                )

            else:

                existing = conn.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE LOWER(username)=LOWER(?)
                    """,
                    (doctor_username,)
                ).fetchone()

                if existing:

                    st.error(
                        "Username already exists."
                    )

                else:

                    conn.execute(
                        """
                        INSERT INTO users(
                            name,
                            username,
                            password_hash,
                            language,
                            role
                        )
                        VALUES(
                            ?,
                            ?,
                            ?,
                            'English',
                            'doctor'
                        )
                        """,
                        (
                            doctor_name,
                            doctor_username,
                            hash_password(
                                doctor_password
                            )
                        )
                    )

                    conn.commit()

                    voice_success(
                        "Doctor added successfully.",
                        "English"
                    )

                    st.rerun()


        doctors = conn.execute(
            """
            SELECT
                id,
                name,
                username
            FROM users
            WHERE role='doctor'
            ORDER BY name
            """
        ).fetchall()

        st.subheader(
            "🩺 Registered Doctors"
        )

        if doctors:

            st.dataframe(
                [
                    {
                        "ID": d[0],
                        "Doctor": d[1],
                        "Username": d[2]
                    }
                    for d in doctors
                ],
                use_container_width=True
            )


            st.subheader(
                "Assign Patient to Doctor"
            )

            doctor_map = {
                f"{d[1]} ({d[2]})": d[0]
                for d in doctors
            }

            patient_rows = conn.execute(
                """
                SELECT id,name,username
                FROM users
                WHERE role='patient'
                ORDER BY name
                """
            ).fetchall()

            patient_map = {
                f"{p[1]} ({p[2]})": p[0]
                for p in patient_rows
            }

            if patient_map:

                selected_doctor = st.selectbox(
                    "Doctor",
                    list(
                        doctor_map.keys()
                    )
                )

                selected_patient = st.selectbox(
                    "Patient",
                    list(
                        patient_map.keys()
                    )
                )

                if st.button(
                    "Assign Patient"
                ):

                    conn.execute(
                        """
                        UPDATE users
                        SET doctor_id=?
                        WHERE id=?
                        """,
                        (
                            doctor_map[
                                selected_doctor
                            ],
                            patient_map[
                                selected_patient
                            ]
                        )
                    )

                    conn.commit()

                    voice_success(
                        "Patient assigned successfully.",
                        "English"
                    )

                    st.rerun()


    # ========================================================
    # ALL SESSIONS
    # ========================================================

    with tabs[3]:

        rows = conn.execute(
            """
            SELECT
                u.name,
                u.username,
                s.game,
                s.score,
                s.difficulty,
                s.created_at
            FROM sessions s
            JOIN users u
            ON s.user_id=u.id
            ORDER BY s.id DESC
            """
        ).fetchall()

        if rows:

            st.dataframe(
                [
                    {
                        "Patient": r[0],
                        "Username": r[1],
                        "Game": r[2],
                        "Score": r[3],
                        "Difficulty": r[4],
                        "Date": r[5]
                    }
                    for r in rows
                ],
                use_container_width=True
            )


    # ========================================================
    # REPORTS
    # ========================================================

    with tabs[4]:

        rows = conn.execute(
            """
            SELECT
                r.created_at,
                p.name,
                d.name,
                r.title,
                r.report_text
            FROM reports r
            JOIN users p
            ON r.patient_id=p.id
            JOIN users d
            ON r.doctor_id=d.id
            ORDER BY r.id DESC
            """
        ).fetchall()

        for r in rows:

            with st.expander(
                f"{r[1]} — {r[3]}"
            ):

                st.write(
                    f"Doctor: Dr. {r[2]}"
                )

                st.write(
                    f"Date: {r[0]}"
                )

                st.write(
                    r[4]
                )

    st.stop()


# ============================================================
# DOCTOR DASHBOARD
# ============================================================

if role == "doctor":

    st.title(
        f"🩺 Doctor Portal — Dr. {name}"
    )

    st.info(
        "Doctors can view assigned patient information "
        "and send reports. Doctors cannot play games."
    )

    tabs = st.tabs(
        [
            "🏠 Overview",
            "👥 Patients",
            "📊 Patient Details",
            "📄 Send Report"
        ]
    )

    patients = conn.execute(
        """
        SELECT
            id,
            name,
            username,
            language,
            baseline
        FROM users
        WHERE role='patient'
        AND doctor_id=?
        ORDER BY name
        """,
        (user_id,)
    ).fetchall()


    with tabs[0]:

        st.metric(
            "Assigned Patients",
            len(patients)
        )

        st.write(
            "🔒 Game access is disabled for doctor accounts."
        )


    with tabs[1]:

        if patients:

            st.dataframe(
                [
                    {
                        "Patient": p[1],
                        "Username": p[2],
                        "Language": p[3],
                        "Baseline": p[4]
                    }
                    for p in patients
                ],
                use_container_width=True
            )

        else:

            st.info(
                "No patients assigned."
            )


    with tabs[2]:

        if patients:

            patient_map = {
                f"{p[1]} ({p[2]})": p[0]
                for p in patients
            }

            selected = st.selectbox(
                "Select Patient",
                list(patient_map.keys())
            )

            patient_id = patient_map[
                selected
            ]

            patient = conn.execute(
                """
                SELECT
                    name,
                    username,
                    language,
                    baseline
                FROM users
                WHERE id=?
                """,
                (patient_id,)
            ).fetchone()

            st.write(
                f"### 👤 {patient[0]}"
            )

            st.write(
                f"Username: {patient[1]}"
            )

            st.write(
                f"Language: {patient[2]}"
            )

            st.metric(
                "Personal Baseline",
                f"{patient[3]:.1f}"
            )

            sessions = conn.execute(
                """
                SELECT
                    game,
                    score,
                    difficulty,
                    created_at
                FROM sessions
                WHERE user_id=?
                ORDER BY id DESC
                """,
                (patient_id,)
            ).fetchall()

            if sessions:

                st.dataframe(
                    [
                        {
                            "Game": s[0],
                            "Score": s[1],
                            "Difficulty": s[2],
                            "Date": s[3]
                        }
                        for s in sessions
                    ],
                    use_container_width=True
                )

            else:

                st.info(
                    "No game history available."
                )


    with tabs[3]:

        if patients:

            patient_map = {
                f"{p[1]} ({p[2]})": p[0]
                for p in patients
            }

            selected = st.selectbox(
                "Select Patient",
                list(patient_map.keys()),
                key="report_patient"
            )

            patient_id = patient_map[
                selected
            ]

            sessions = conn.execute(
                """
                SELECT score
                FROM sessions
                WHERE user_id=?
                """,
                (patient_id,)
            ).fetchall()

            scores = [
                float(x[0])
                for x in sessions
            ]

            average = (
                sum(scores) / len(scores)
                if scores else 0
            )

            best = (
                max(scores)
                if scores else 0
            )

            report_title = st.text_input(
                "Report Title",
                value="Overall Performance Report"
            )

            report = st.text_area(
                "Doctor Report",
                value=(
                    "Overall Performance Report\n\n"
                    f"Sessions completed: {len(scores)}\n"
                    f"Average score: {average:.1f}\n"
                    f"Best score: {best:.1f}\n\n"
                    "Doctor's observation:\n"
                ),
                height=250
            )

            if st.button(
                "📤 Send Report",
                type="primary"
            ):

                conn.execute(
                    """
                    INSERT INTO reports(
                        patient_id,
                        doctor_id,
                        title,
                        report_text,
                        created_at
                    )
                    VALUES(
                        ?,
                        ?,
                        ?,
                        ?,
                        ?
                    )
                    """,
                    (
                        patient_id,
                        user_id,
                        report_title,
                        report,
                        datetime.now().isoformat(
                            timespec="seconds"
                        )
                    )
                )

                conn.commit()

                voice_success(
                    "Overall performance report "
                    "sent successfully to the patient.",
                    "English"
                )

                st.rerun()

        else:

            st.info(
                "Assign patients first."
            )

    st.stop()


# ============================================================
# PATIENT
# ============================================================

patient = conn.execute(
    """
    SELECT
        id,
        name,
        username,
        language,
        baseline,
        doctor_id
    FROM users
    WHERE id=?
    AND role='patient'
    """,
    (user_id,)
).fetchone()

if patient is None:

    st.error(
        "Patient account not found."
    )

    st.stop()


user_id = patient[0]
name = patient[1]
username = patient[2]
language = patient[3]
doctor_id = patient[5]


# ============================================================
# BASELINE
# ============================================================

def get_baseline():

    rows = conn.execute(
        """
        SELECT score
        FROM sessions
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (user_id,)
    ).fetchall()

    if not rows:

        return 0

    return round(
        sum(
            float(x[0])
            for x in rows
        ) / len(rows),
        1
    )


baseline = get_baseline()


def get_difficulty():

    if baseline >= 85:
        return 3

    if baseline >= 65:
        return 2

    return 1


difficulty = get_difficulty()


# ============================================================
# PATIENT NAVIGATION
# ============================================================

if "page" not in st.session_state:

    st.session_state.page = "home"


pages = {
    "home": "🏠 Home",
    "games": "🎮 Cognitive Games",
    "reminders": "⏰ Reminders",
    "history": "📜 My History",
    "details": "👤 My Details",
    "reports": "📄 Reports"
}


page = st.radio(
    "Navigation",
    list(pages.keys()),
    format_func=lambda x: pages[x],
    horizontal=True
)

st.session_state.page = page


# ============================================================
# HOME
# ============================================================

if page == "home":

    st.title(
        f"🧠 Welcome {name}!"
    )

    c1, c2, c3 = st.columns(3)

    sessions_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM sessions
        WHERE user_id=?
        """,
        (user_id,)
    ).fetchone()[0]

    c1.metric(
        "Personal Baseline",
        baseline
    )

    c2.metric(
        "Current Difficulty",
        difficulty
    )

    c3.metric(
        "Sessions",
        sessions_count
    )

    st.success(
        "Your personal dashboard is ready."
    )

    if doctor_id:

        doctor = conn.execute(
            """
            SELECT name
            FROM users
            WHERE id=?
            AND role='doctor'
            """,
            (doctor_id,)
        ).fetchone()

        if doctor:

            st.info(
                f"🩺 Assigned Doctor: Dr. {doctor[0]}"
            )

    else:

        st.info(
            "🩺 No doctor assigned yet."
        )


# ============================================================
# COGNITIVE GAMES
# ============================================================

elif page == "games":

    st.title(
        "🎮 Cognitive Games"
    )

    st.write(
        f"Current adaptive difficulty: **{difficulty}**"
    )


    # ========================================================
    # MEMORY SEQUENCE
    # ========================================================

    st.subheader(
        "🧠 Memory Sequence"
    )

    length = {
        1: 4,
        2: 6,
        3: 8
    }[difficulty]

    if "sequence" not in st.session_state:

        st.session_state.sequence = None


    if st.button(
        "Start Memory Game",
        type="primary"
    ):

        st.session_state.sequence = random.sample(
            range(1, 10),
            length
        )

    sequence = st.session_state.sequence

    if sequence:

        st.success(
            "Remember this sequence:"
        )

        st.markdown(
            "### " +
            " • ".join(
                map(str, sequence)
            )
        )

        answer = st.text_input(
            "Enter the sequence"
        )

        if st.button(
            "Submit Answer"
        ):

            try:

                user_answer = [
                    int(x)
                    for x in answer.replace(
                        ",",
                        " "
                    ).split()
                ]

                correct = sum(
                    a == b
                    for a, b in zip(
                        sequence,
                        user_answer
                    )
                )

                score = round(
                    correct /
                    len(sequence) *
                    100,
                    1
                )

                conn.execute(
                    """
                    INSERT INTO sessions(
                        user_id,
                        game,
                        score,
                        difficulty,
                        created_at
                    )
                    VALUES(
                        ?,
                        ?,
                        ?,
                        ?,
                        ?
                    )
                    """,
                    (
                        user_id,
                        "Memory Sequence",
                        score,
                        difficulty,
                        datetime.now().isoformat(
                            timespec="seconds"
                        )
                    )
                )

                conn.commit()

                voice_success(
                    f"Your memory game score is {score}.",
                    language
                )

                st.session_state.sequence = None

                st.rerun()

            except ValueError:

                st.error(
                    "Enter numbers separated by spaces."
                )


# ============================================================
# REMINDERS
# ============================================================

elif page == "reminders":

    st.title(
        "⏰ Reminders"
    )

    title = st.text_input(
        "Reminder"
    )

    reminder_time = st.time_input(
        "Time",
        value=time(9, 0)
    )

    if st.button(
        "Add Reminder",
        type="primary"
    ):

        if title:

            conn.execute(
                """
                INSERT INTO reminders(
                    user_id,
                    title,
                    due_time,
                    status
                )
                VALUES(
                    ?,
                    ?,
                    ?,
                    'Pending'
                )
                """,
                (
                    user_id,
                    title,
                    f"{date.today()} "
                    f"{reminder_time.strftime('%H:%M')}"
                )
            )

            conn.commit()

            voice_success(
                f"{title} reminder added successfully.",
                language
            )

            st.rerun()


    reminders = conn.execute(
        """
        SELECT
            id,
            title,
            due_time,
            status
        FROM reminders
        WHERE user_id=?
        ORDER BY due_time
        """,
        (user_id,)
    ).fetchall()


    for reminder in reminders:

        c1, c2, c3 = st.columns(
            [4, 2, 1]
        )

        c1.write(
            reminder[1]
        )

        c2.write(
            reminder[2]
        )

        if reminder[3] == "Done":

            c3.success(
                "Done"
            )

        elif c3.button(
            "Done",
            key=f"done_{reminder[0]}"
        ):

            conn.execute(
                """
                UPDATE reminders
                SET status='Done'
                WHERE id=?
                AND user_id=?
                """,
                (
                    reminder[0],
                    user_id
                )
            )

            conn.commit()

            voice_success(
                f"{reminder[1]} completed successfully.",
                language
            )

            st.rerun()


# ============================================================
# HISTORY
# ============================================================

elif page == "history":

    st.title(
        "📜 My History"
    )

    rows = conn.execute(
        """
        SELECT
            game,
            score,
            difficulty,
            created_at
        FROM sessions
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    if rows:

        st.dataframe(
            [
                {
                    "Game": r[0],
                    "Score": r[1],
                    "Difficulty": r[2],
                    "Date": r[3]
                }
                for r in rows
            ],
            use_container_width=True
        )

    else:

        st.info(
            "No game history available."
        )


# ============================================================
# DETAILS
# ============================================================

elif page == "details":

    st.title(
        "👤 My Details"
    )

    st.write(
        f"**Name:** {name}"
    )

    st.write(
        f"**Username:** {username}"
    )

    st.write(
        f"**Language:** {language}"
    )

    st.write(
        f"**Personal Baseline:** {baseline}"
    )

    if doctor_id:

        doctor = conn.execute(
            """
            SELECT name
            FROM users
            WHERE id=?
            """,
            (doctor_id,)
        ).fetchone()

        if doctor:

            st.write(
                f"**Doctor:** Dr. {doctor[0]}"
            )

    else:

        st.write(
            "**Doctor:** Not assigned"
        )


# ============================================================
# REPORTS
# ============================================================

elif page == "reports":

    st.title(
        "📄 My Performance Reports"
    )

    reports = conn.execute(
        """
        SELECT
            title,
            report_text,
            created_at,
            doctor_id
        FROM reports
        WHERE patient_id=?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    if reports:

        for report in reports:

            doctor = conn.execute(
                """
                SELECT name
                FROM users
                WHERE id=?
                """,
                (report[3],)
            ).fetchone()

            with st.expander(
                f"{report[0]} — "
                f"{report[2]}"
            ):

                if doctor:

                    st.write(
                        f"🩺 Dr. {doctor[0]}"
                    )

                st.write(
                    report[1]
                )

                if st.button(
                    "🔊 Read Report",
                    key=f"read_{report[2]}"
                ):

                    speak(
                        report[1],
                        language
                    )

    else:

        st.info(
            "No doctor report available yet."
        )
