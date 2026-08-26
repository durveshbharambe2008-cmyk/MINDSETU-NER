# ============================================================
# MINDSETU NER - COMPLETE VOICE-FIRST STREAMLIT APP (ENHANCED)
# ============================================================

import streamlit as st
import sqlite3
import random
import hashlib
import io
import re
import base64
import textwrap
import time as time_lib
from datetime import datetime, date, time

# ============================================================
# OPTIONAL PACKAGES
# ============================================================

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
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="MINDSETU NER",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DATABASE (CACHED)
# ============================================================

DB_NAME = "mindsetu_ner.db"

@st.cache_resource
def get_connection():
    connection = sqlite3.connect(
        DB_NAME,
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
            doctor_id INTEGER,
            adaptive_difficulty INTEGER DEFAULT 1
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game TEXT NOT NULL,
            score REAL NOT NULL,
            difficulty INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            due_time TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            report_text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'Sent'
        )
    """)

    columns = connection.execute("PRAGMA table_info(users)").fetchall()
    column_names = [column[1] for column in columns]

    if "adaptive_difficulty" not in column_names:
        connection.execute("""
            ALTER TABLE users
            ADD COLUMN adaptive_difficulty
            INTEGER DEFAULT 1
        """)

    connection.commit()
    return connection

conn = get_connection()

# ============================================================
# LANGUAGE SETTINGS
# ============================================================

LANGUAGES = {
    "English": {"code": "en", "speech": "en-IN"},
    "Hindi": {"code": "hi", "speech": "hi-IN"},
    "Marathi": {"code": "mr", "speech": "mr-IN"},
    "Bengali": {"code": "bn", "speech": "bn-IN"},
    "Gujarati": {"code": "gu", "speech": "gu-IN"},
    "Tamil": {"code": "ta", "speech": "ta-IN"},
    "Telugu": {"code": "te", "speech": "te-IN"},
    "Kannada": {"code": "kn", "speech": "kn-IN"},
    "Malayalam": {"code": "ml", "speech": "ml-IN"},
    "Punjabi": {"code": "pa", "speech": "pa-IN"},
    "Urdu": {"code": "ur", "speech": "ur-PK"},
    "Nepali": {"code": "ne", "speech": "ne-NP"},
    "French": {"code": "fr", "speech": "fr-FR"},
    "Spanish": {"code": "es", "speech": "es-ES"},
    "German": {"code": "de", "speech": "de-DE"},
    "Italian": {"code": "it", "speech": "it-IT"},
    "Portuguese": {"code": "pt", "speech": "pt-PT"},
    "Arabic": {"code": "ar", "speech": "ar-SA"},
    "Chinese": {"code": "zh-CN", "speech": "zh-CN"},
    "Japanese": {"code": "ja", "speech": "ja-JP"},
    "Korean": {"code": "ko", "speech": "ko-KR"},
    "Russian": {"code": "ru", "speech": "ru-RU"},
    "Turkish": {"code": "tr", "speech": "tr-TR"}
}

TRANSLATIONS = {
    "English": {
        "home": "Home", "games": "Cognitive Games", "reminders": "Reminders",
        "history": "My History", "details": "My Details", "reports": "Reports",
        "logout": "Logout", "welcome": "Welcome", "language": "Language",
        "save": "Save", "add": "Add", "delete": "Delete", "submit": "Submit",
        "start": "Start", "score": "Score", "difficulty": "Difficulty",
        "doctor": "Doctor", "patient": "Patient", "admin": "Administrator",
        "send_report": "Send Report", "select_patient": "Select Patient",
        "no_reports": "No reports available.", "no_history": "No game history available.",
        "success": "Success"
    }
}

def text(key, language):
    language_dict = TRANSLATIONS.get(language, TRANSLATIONS["English"])
    return language_dict.get(key, TRANSLATIONS["English"].get(key, key))

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# ============================================================
# ENHANCED VOICE OUTPUT (GTTS + BROWSER WEB SPEECH FALLBACK)
# ============================================================

def generate_voice_html(message, language="English"):
    if not message:
        return ""

    language_code = LANGUAGES.get(language, LANGUAGES["English"])["code"]
    audio_base64 = ""

    if gTTS is not None:
        try:
            audio_buffer = io.BytesIO()
            gTTS(text=message, lang=language_code, slow=False).write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_base64 = base64.b64encode(audio_buffer.read()).decode("utf-8")
        except Exception:
            audio_base64 = ""

    html = f"""
    <div style="width:1px;height:1px;overflow:hidden;position:absolute;left:-9999px;top:-9999px;">
        {'<audio id="mindsetuVoice" autoplay playsinline preload="auto"><source src="data:audio/mpeg;base64,' + audio_base64 + '" type="audio/mpeg"></audio>' if audio_base64 else ''}
        <script>
            const audio = document.getElementById("mindsetuVoice");
            if (audio) {{
                audio.volume = 1.0;
                audio.play().catch(() => {{ speakFallback(); }});
            }} else {{
                speakFallback();
            }}
            function speakFallback() {{
                if ('speechSynthesis' in window) {{
                    window.speechSynthesis.cancel();
                    const msg = new SpeechSynthesisUtterance("{message}");
                    msg.lang = "{language_code}";
                    window.speechSynthesis.speak(msg);
                }}
            }}
        </script>
    </div>
    """
    return html

def queue_voice(message, language="English"):
    if not message:
        return
    st.session_state.pending_voice_message = message
    st.session_state.pending_voice_language = language

def play_pending_voice():
    message = st.session_state.get("pending_voice_message")
    language = st.session_state.get("pending_voice_language", "English")

    if not message:
        return

    st.session_state.pending_voice_message = None
    st.session_state.pending_voice_language = None

    html = generate_voice_html(message, language)
    if html:
        st.html(html, width=1, unsafe_allow_javascript=True)

def announce(message, language="English"):
    queue_voice(message, language)

# ============================================================
# VOICE RECOGNITION
# ============================================================

def recognize_voice(audio_bytes, language):
    if sr is None:
        return None, "SpeechRecognition package is not installed."
    if not audio_bytes:
        return None, "No audio was recorded."
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        speech_lang = LANGUAGES.get(language, LANGUAGES["English"])["speech"]
        command = recognizer.recognize_google(audio, language=speech_lang)
        return command.lower().strip(), None
    except Exception:
        return None, "Could not understand speech."

# ============================================================
# TIME & COMMAND PARSERS
# ============================================================

def parse_time_from_command(command):
    if not command: return None
    match = re.search(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b", command)
    if match: return f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"
    match = re.search(r"\b(1[0-2]|0?[1-9])(?:[:.]([0-5]\d))?\s*(am|pm)\b", command, re.I)
    if match:
        hr = int(match.group(1))
        mn = int(match.group(2) or 0)
        ampm = match.group(3).lower()
        if ampm == "pm" and hr != 12: hr += 12
        if ampm == "am" and hr == 12: hr = 0
        return f"{hr:02d}:{mn:02d}"
    return None

def extract_reminder_title(command):
    title = command.strip()
    for phrase in ["add a reminder", "add reminder", "set reminder", "remind me to"]:
        title = title.replace(phrase, "")
    title = re.sub(r"\b(?:at|for)\s+.*", "", title, flags=re.I).strip()
    return title.capitalize() if title else "Reminder"

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

DEFAULT_SESSION_VALUES = {
    "logged_in": False, "user_id": None, "name": "", "username": "",
    "role": None, "language": "English", "doctor_id": None, "page": "home",
    "pending_voice_message": None, "pending_voice_language": None,
    "memory_sequence": None, "pattern_sequence": None, "pattern_user_input": [],
    "reaction_target": None, "attention_start_time": None,
    "spatial_target": None, "spatial_user_input": []
}

for key, val in DEFAULT_SESSION_VALUES.items():
    if key not in st.session_state:
        st.session_state[key] = val

if st.session_state.logged_in:
    play_pending_voice()

# ============================================================
# LOGIN / REGISTRATION ROUTING
# ============================================================

if not st.session_state.logged_in:
    st.markdown("""
        <div style="text-align:center;padding:25px;border-radius:20px;background:linear-gradient(135deg, #667eea, #764ba2);color:white;">
            <h1>🧠 MINDSETU NER</h1>
            <p>Personalised Cognitive & Memory Companion</p>
        </div>
    """, unsafe_allow_html=True)
    
    login_tab, signup_tab = st.tabs(["🔐 Login", "📝 Patient Registration"])

    with login_tab:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("🔐 Login", type="primary", use_container_width=True):
            username_clean = username.strip()
            if username_clean.lower() == "admin" and password == "admin123":
                st.session_state.update({"logged_in": True, "user_id": 0, "name": "Administrator", "username": "admin", "role": "admin", "language": "English", "page": "home"})
                queue_voice("Welcome Administrator.", "English")
                st.rerun()
            else:
                user = conn.execute("SELECT id, name, username, password_hash, language, role, doctor_id, adaptive_difficulty FROM users WHERE LOWER(username)=LOWER(?)", (username_clean,)).fetchone()
                if user and hash_password(password) == user[3]:
                    st.session_state.update({"logged_in": True, "user_id": user[0], "name": user[1], "username": user[2], "language": user[4], "role": user[5], "doctor_id": user[6], "page": "home"})
                    queue_voice(f"Welcome {user[1]}. You have logged in successfully.", user[4])
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    with signup_tab:
        st.subheader("Create Patient Account")
        reg_name = st.text_input("Full Name", key="reg_name")
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_language = st.selectbox("Select Language", list(LANGUAGES.keys()), key="reg_language")

        if st.button("📝 Create Patient Account", type="primary", use_container_width=True):
            if reg_name and reg_username and len(reg_password) >= 6:
                conn.execute("INSERT INTO users(name, username, password_hash, language, baseline, role, adaptive_difficulty) VALUES(?, ?, ?, ?, 0, 'patient', 1)", (reg_name.strip(), reg_username.strip(), hash_password(reg_password), reg_language))
                conn.commit()
                st.success("Account created successfully! You can now log in.")
            else:
                st.error("Please fill all details correctly.")

    st.stop()

# ============================================================
# LOGGED IN STATE MANAGEMENT
# ============================================================

role = st.session_state.role
user_id = st.session_state.user_id
name = st.session_state.name
language = st.session_state.language

def calculate_baseline(patient_id):
    rows = conn.execute("SELECT score FROM sessions WHERE user_id=? ORDER BY id DESC LIMIT 10", (patient_id,)).fetchall()
    return round(sum(float(r[0]) for r in rows) / len(rows), 1) if rows else 0.0

def update_adaptive_difficulty(patient_id, score):
    row = conn.execute("SELECT adaptive_difficulty FROM users WHERE id=? AND role='patient'", (patient_id,)).fetchone()
    old_diff = int(row[0] or 1) if row else 1
    new_diff = min(old_diff + 1, 3) if score >= 70 else max(old_diff - 1, 1)
    conn.execute("UPDATE users SET adaptive_difficulty=? WHERE id=? AND role='patient'", (new_diff, patient_id))
    conn.commit()
    return old_diff, new_diff, "won" if score >= 70 else "lost"

def game_result_voice(game_name, score, old_d, new_d, lang):
    msg = f"Completed {game_name} with score {score}. "
    msg += f"Difficulty adjusted to level {new_d}." if new_d != old_d else f"Difficulty remains level {new_d}."
    return msg

# ============================================================
# PATIENT SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🧠 MINDSETU NER")
    st.write(f"👤 **{name}**")
    st.caption(f"Role: {role.capitalize()}")
    st.divider()

    selected_language = st.selectbox("Language", list(LANGUAGES.keys()), index=list(LANGUAGES.keys()).index(language))
    if selected_language != language:
        conn.execute("UPDATE users SET language=? WHERE id=?", (selected_language, user_id))
        conn.commit()
        st.session_state.language = selected_language
        st.rerun()

    if mic_recorder is not None:
        st.caption("Click 🎤, speak clearly, then click ⏹️ to stop.")
        audio_data = mic_recorder(start_prompt="🎤 Start Listening", stop_prompt="⏹️ Stop Listening", just_once=True, key="voice_rec")
        if audio_data:
            cmd, err = recognize_voice(audio_data["bytes"], language)
            if cmd:
                st.caption(f'🎤 I heard: "{cmd}"')
                if "game" in cmd: st.session_state.page = "games"
                elif "reminder" in cmd: st.session_state.page = "reminders"
                elif "history" in cmd: st.session_state.page = "history"
                elif "report" in cmd: st.session_state.page = "reports"
                elif "logout" in cmd: st.session_state.logged_in = False
                st.rerun()

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ============================================================
# NAVIGATION & ROUTING
# ============================================================

page = st.radio("Navigation", ["home", "games", "reminders", "history", "details", "reports"], 
                format_func=lambda x: f"🏠 {x.capitalize()}" if x=="home" else f"🎮 Games" if x=="games" else f"⏰ Reminders" if x=="reminders" else f"📜 History" if x=="history" else f"👤 Details" if x=="details" else f"📄 Reports", 
                horizontal=True, index=["home", "games", "reminders", "history", "details", "reports"].index(st.session_state.page))

st.session_state.page = page

# ============================================================
# HOME TAB
# ============================================================

if page == "home":
    st.markdown(f"## 🧠 Welcome back, {name}!")
    b_line = calculate_baseline(user_id)
    diff = conn.execute("SELECT adaptive_difficulty FROM users WHERE id=?", (user_id,)).fetchone()[0]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Baseline Score", f"{b_line:.1f}")
    c2.metric("Current Difficulty", f"{diff}/3")
    c3.metric("Role", role.capitalize())

    st.subheader("📈 Performance Trend")
    sessions_data = conn.execute("SELECT score FROM sessions WHERE user_id=? ORDER BY id ASC", (user_id,)).fetchall()
    if sessions_data:
        st.line_chart([s[0] for s in sessions_data])
    else:
        st.info("Play cognitive games to start tracking your performance over time!")

# ============================================================
# GAMES TAB
# ============================================================

elif page == "games":
    st.title("🎮 Cognitive Games")
    diff = conn.execute("SELECT adaptive_difficulty FROM users WHERE id=?", (user_id,)).fetchone()[0]
    
    tab1, tab2, tab3, tab4 = st.tabs(["🧠 Memory Sequence", "🔷 Pattern Memory Grid", "⚡ Reaction Attention", "🧩 Spatial Matrix"])

    # --- GAME 1: MEMORY SEQUENCE ---
    with tab1:
        seq_len = {1: 4, 2: 6, 3: 8}[diff]
        if st.session_state.memory_sequence is None:
            if st.button("▶️ Start Memory Sequence", type="primary"):
                st.session_state.memory_sequence = random.sample(range(1, 10), seq_len)
                st.rerun()
        else:
            st.success("Remember this sequence:")
            st.markdown("## " + " • ".join(str(n) for n in st.session_state.memory_sequence))
            ans = st.text_input("Enter sequence separated by spaces:")
            if st.button("Submit Answer"):
                try:
                    user_ans = [int(x) for x in ans.split()]
                    correct = sum(a == b for a, b in zip(st.session_state.memory_sequence, user_ans))
                    score = round((correct / len(st.session_state.memory_sequence)) * 100, 1)
                    conn.execute("INSERT INTO sessions(user_id, game, score, difficulty, created_at) VALUES(?, ?, ?, ?, ?)",
                                 (user_id, "Memory Sequence", score, diff, datetime.now().isoformat(timespec="seconds")))
                    conn.commit()
                    o_diff, n_diff, _ = update_adaptive_difficulty(user_id, score)
                    st.session_state.memory_sequence = None
                    queue_voice(game_result_voice("Memory Game", score, o_diff, n_diff, language), language)
                    st.rerun()
                except Exception: st.error("Please enter valid space-separated numbers.")

    # --- GAME 2: PATTERN MEMORY (CLICKABLE GRID) ---
    with tab2:
        symbols = ["▲", "●", "■", "◆"]
        pat_len = {1: 3, 2: 4, 3: 5}[diff]
        if st.session_state.pattern_sequence is None:
            if st.button("▶️ Start Pattern Memory", type="primary"):
                st.session_state.pattern_sequence = [random.choice(symbols) for _ in range(pat_len)]
                st.session_state.pattern_user_input = []
                st.rerun()
        else:
            st.success(f"Remember this sequence of {pat_len} symbols:")
            st.markdown("## " + " ".join(st.session_state.pattern_sequence))
            st.write("Click the buttons in the exact order:")
            
            cols = st.columns(4)
            for idx, sym in enumerate(symbols):
                if cols[idx].button(sym, key=f"pat_sym_{sym}"):
                    st.session_state.pattern_user_input.append(sym)

            st.write("Your Input: " + " ".join(st.session_state.pattern_user_input))
            
            if len(st.session_state.pattern_user_input) == pat_len:
                correct = sum(a == b for a, b in zip(st.session_state.pattern_sequence, st.session_state.pattern_user_input))
                score = round((correct / pat_len) * 100, 1)
                conn.execute("INSERT INTO sessions(user_id, game, score, difficulty, created_at) VALUES(?, ?, ?, ?, ?)",
                             (user_id, "Pattern Memory", score, diff, datetime.now().isoformat(timespec="seconds")))
                conn.commit()
                o_diff, n_diff, _ = update_adaptive_difficulty(user_id, score)
                st.session_state.pattern_sequence = None
                st.session_state.pattern_user_input = []
                queue_voice(game_result_voice("Pattern Memory", score, o_diff, n_diff, language), language)
                st.rerun()

    # --- GAME 3: ATTENTION WITH REACTION TIME METRIC ---
    with tab3:
        if st.session_state.reaction_target is None:
            if st.button("▶️ Start Attention Game", type="primary"):
                st.session_state.reaction_target = random.randint(1, 9)
                st.session_state.attention_start_time = time_lib.time()
                st.rerun()
        else:
            st.markdown(f"## Target Number: **{st.session_state.reaction_target}**")
            nums = list(range(1, 10))
            random.shuffle(nums)
            cols = st.columns(3)
            for i, n in enumerate(nums):
                if cols[i % 3].button(str(n), key=f"att_{n}"):
                    reaction_time = round(time_lib.time() - st.session_state.attention_start_time, 2)
                    score = 100 if n == st.session_state.reaction_target else 0
                    if reaction_time > 3.0 and score == 100: score = 80 # Speed penalty
                    
                    conn.execute("INSERT INTO sessions(user_id, game, score, difficulty, created_at) VALUES(?, ?, ?, ?, ?)",
                                 (user_id, "Attention Game", score, diff, datetime.now().isoformat(timespec="seconds")))
                    conn.commit()
                    o_diff, n_diff, _ = update_adaptive_difficulty(user_id, score)
                    st.session_state.reaction_target = None
                    queue_voice(f"Reaction time: {reaction_time} seconds. " + game_result_voice("Attention Game", score, o_diff, n_diff, language), language)
                    st.rerun()

    # --- GAME 4: SPATIAL MATRIX MEMORY ---
    with tab4:
        matrix_tiles = {1: 3, 2: 4, 3: 5}[diff]
        if st.session_state.spatial_target is None:
            if st.button("▶️ Start Spatial Matrix", type="primary"):
                st.session_state.spatial_target = random.sample(range(9), matrix_tiles)
                st.session_state.spatial_user_input = []
                st.rerun()
        else:
            st.info(f"Memorize the highlighted {matrix_tiles} positions in the 3x3 grid:")
            grid_cols = st.columns(3)
            for i in range(9):
                is_target = i in st.session_state.spatial_target
                label = "🟦" if is_target else "⬜"
                if grid_cols[i % 3].button(label, key=f"spat_{i}"):
                    st.session_state.spatial_user_input.append(i)
                    
            if len(st.session_state.spatial_user_input) == matrix_tiles:
                correct = len(set(st.session_state.spatial_target).intersection(set(st.session_state.spatial_user_input)))
                score = round((correct / matrix_tiles) * 100, 1)
                conn.execute("INSERT INTO sessions(user_id, game, score, difficulty, created_at) VALUES(?, ?, ?, ?, ?)",
                             (user_id, "Spatial Matrix", score, diff, datetime.now().isoformat(timespec="seconds")))
                conn.commit()
                o_diff, n_diff, _ = update_adaptive_difficulty(user_id, score)
                st.session_state.spatial_target = None
                st.session_state.spatial_user_input = []
                queue_voice(game_result_voice("Spatial Matrix", score, o_diff, n_diff, language), language)
                st.rerun()

# ============================================================
# HISTORY TAB
# ============================================================

elif page == "history":
    st.title("📜 My Performance History")
    sessions = conn.execute("SELECT game, score, difficulty, created_at FROM sessions WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
    
    if sessions:
        scores = [s[1] for s in sessions]
        st.line_chart(scores)
        st.dataframe([{"Game": s[0], "Score": s[1], "Difficulty": s[2], "Date": s[3]} for s in sessions], use_container_width=True)
    else:
        st.info("No game history recorded yet.")

# ============================================================
# REMINDERS, DETAILS & REPORTS TABS
# ============================================================

elif page == "reminders":
    st.title("⏰ Reminders")
    r_title = st.text_input("Reminder Title")
    r_time = st.time_input("Time", value=time(9, 0))
    if st.button("Add Reminder"):
        conn.execute("INSERT INTO reminders(user_id, title, due_time, status) VALUES(?, ?, ?, 'Pending')",
                     (user_id, r_title, f"{date.today()} {r_time.strftime('%H:%M')}"))
        conn.commit()
        st.rerun()

elif page == "details":
    st.title("👤 Account Details")
    st.write(f"**Name:** {name}\n**Username:** {username}\n**Role:** {role.capitalize()}")

elif page == "reports":
    st.title("📄 Clinical Reports")
    reports = conn.execute("SELECT title, report_text, created_at FROM reports WHERE patient_id=?", (user_id,)).fetchall()
    for rep in reports:
        with st.expander(f"{rep[0]} - {rep[2]}"):
            st.write(rep[1])
            if st.button("🔊 Listen to Report", key=f"rep_{rep[0]}"):
                queue_voice(rep[1], language)
                st.rerun()
