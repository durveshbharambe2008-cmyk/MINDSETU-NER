# ============================================================
# MINDSETU NER - COMPLETE VOICE-FIRST STREAMLIT APP
# ============================================================
#
# FEATURES
#
# 1. Patient / Doctor / Admin roles
# 2. Patient registration and login
# 3. Admin dashboard
# 4. Admin can add doctors
# 5. Admin can assign patients to doctors
# 6. Doctor can see assigned patients only
# 7. Doctor cannot access games
# 8. Patient cognitive games
# 9. Memory Sequence Game
# 10. Pattern Memory Game
# 11. Attention Game
# 12. Adaptive difficulty
# 13. Difficulty increases after strong performance
# 14. Difficulty decreases after weak performance
# 15. Personal history
# 16. Personal baseline
# 17. Reminders
# 18. Doctor reports
# 19. Patient can listen to reports
# 20. Hidden voice output
# 21. Voice welcome after login
# 22. Voice confirmation after actions
# 23. Voice commands
# 24. Multilingual voice output
# 25. Multilingual voice recognition
# 26. Multilingual UI
#
# INSTALL:
#
# pip install streamlit gTTS SpeechRecognition streamlit-mic-recorder
#
# RUN:
#
# streamlit run app.py
#
# ============================================================

import streamlit as st
import sqlite3
import random
import hashlib
import io
import re
import base64

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
# DATABASE
# ============================================================

DB_NAME = "mindsetu_ner.db"


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

    # --------------------------------------------------------
    # DATABASE MIGRATION FOR OLD DATABASES
    # --------------------------------------------------------

    columns = connection.execute(
        "PRAGMA table_info(users)"
    ).fetchall()

    column_names = [
        column[1]
        for column in columns
    ]

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

    "English": {
        "code": "en",
        "speech": "en-IN"
    },

    "Hindi": {
        "code": "hi",
        "speech": "hi-IN"
    },

    "Marathi": {
        "code": "mr",
        "speech": "mr-IN"
    },

    "Bengali": {
        "code": "bn",
        "speech": "bn-IN"
    },

    "Gujarati": {
        "code": "gu",
        "speech": "gu-IN"
    },

    "Tamil": {
        "code": "ta",
        "speech": "ta-IN"
    },

    "Telugu": {
        "code": "te",
        "speech": "te-IN"
    },

    "Kannada": {
        "code": "kn",
        "speech": "kn-IN"
    },

    "Malayalam": {
        "code": "ml",
        "speech": "ml-IN"
    },

    "Punjabi": {
        "code": "pa",
        "speech": "pa-IN"
    },

    "Urdu": {
        "code": "ur",
        "speech": "ur-PK"
    },

    "Nepali": {
        "code": "ne",
        "speech": "ne-NP"
    },

    "French": {
        "code": "fr",
        "speech": "fr-FR"
    },

    "Spanish": {
        "code": "es",
        "speech": "es-ES"
    },

    "German": {
        "code": "de",
        "speech": "de-DE"
    },

    "Italian": {
        "code": "it",
        "speech": "it-IT"
    },

    "Portuguese": {
        "code": "pt",
        "speech": "pt-PT"
    },

    "Arabic": {
        "code": "ar",
        "speech": "ar-SA"
    },

    "Chinese": {
        "code": "zh-CN",
        "speech": "zh-CN"
    },

    "Japanese": {
        "code": "ja",
        "speech": "ja-JP"
    },

    "Korean": {
        "code": "ko",
        "speech": "ko-KR"
    },

    "Russian": {
        "code": "ru",
        "speech": "ru-RU"
    },

    "Turkish": {
        "code": "tr",
        "speech": "tr-TR"
    }
}


# ============================================================
# UI TRANSLATIONS
# ============================================================

TRANSLATIONS = {

    "English": {

        "home": "Home",
        "games": "Cognitive Games",
        "reminders": "Reminders",
        "history": "My History",
        "details": "My Details",
        "reports": "Reports",
        "logout": "Logout",
        "welcome": "Welcome",
        "language": "Language",
        "save": "Save",
        "add": "Add",
        "delete": "Delete",
        "submit": "Submit",
        "start": "Start",
        "score": "Score",
        "difficulty": "Difficulty",
        "doctor": "Doctor",
        "patient": "Patient",
        "admin": "Administrator",
        "send_report": "Send Report",
        "select_patient": "Select Patient",
        "no_reports": "No reports available.",
        "no_history": "No game history available.",
        "success": "Success"
    },

    "Hindi": {

        "home": "होम",
        "games": "संज्ञानात्मक खेल",
        "reminders": "रिमाइंडर",
        "history": "मेरा इतिहास",
        "details": "मेरी जानकारी",
        "reports": "रिपोर्ट",
        "logout": "लॉगआउट",
        "welcome": "स्वागत है",
        "language": "भाषा",
        "save": "सेव करें",
        "add": "जोड़ें",
        "delete": "हटाएं",
        "submit": "सबमिट करें",
        "start": "शुरू करें",
        "score": "स्कोर",
        "difficulty": "कठिनाई",
        "doctor": "डॉक्टर",
        "patient": "मरीज",
        "admin": "एडमिन",
        "send_report": "रिपोर्ट भेजें",
        "select_patient": "मरीज चुनें",
        "no_reports": "कोई रिपोर्ट उपलब्ध नहीं है।",
        "no_history": "कोई गेम इतिहास उपलब्ध नहीं है।",
        "success": "सफलता"
    },

    "Marathi": {

        "home": "मुख्यपृष्ठ",
        "games": "संज्ञानात्मक खेळ",
        "reminders": "स्मरणपत्रे",
        "history": "माझा इतिहास",
        "details": "माझी माहिती",
        "reports": "अहवाल",
        "logout": "लॉगआउट",
        "welcome": "स्वागत आहे",
        "language": "भाषा",
        "save": "सेव्ह करा",
        "add": "जोडा",
        "delete": "हटवा",
        "submit": "सबमिट करा",
        "start": "सुरू करा",
        "score": "गुण",
        "difficulty": "अडचण",
        "doctor": "डॉक्टर",
        "patient": "रुग्ण",
        "admin": "प्रशासक",
        "send_report": "अहवाल पाठवा",
        "select_patient": "रुग्ण निवडा",
        "no_reports": "कोणताही अहवाल उपलब्ध नाही.",
        "no_history": "कोणताही गेम इतिहास उपलब्ध नाही.",
        "success": "यशस्वी"
    },

    "Gujarati": {

        "home": "હોમ",
        "games": "કોગ્નિટિવ ગેમ્સ",
        "reminders": "રિમાઇન્ડર્સ",
        "history": "મારો ઇતિહાસ",
        "details": "મારી માહિતી",
        "reports": "રિપોર્ટ્સ",
        "logout": "લોગઆઉટ",
        "welcome": "સ્વાગત છે",
        "language": "ભાષા",
        "save": "સેવ કરો",
        "add": "ઉમેરો",
        "delete": "કાઢી નાખો",
        "submit": "સબમિટ કરો",
        "start": "શરૂ કરો",
        "score": "સ્કોર",
        "difficulty": "મુશ્કેલી",
        "doctor": "ડોક્ટર",
        "patient": "દર્દી",
        "admin": "એડમિન",
        "send_report": "રિપોર્ટ મોકલો",
        "select_patient": "દર્દી પસંદ કરો",
        "no_reports": "કોઈ રિપોર્ટ ઉપલબ્ધ નથી.",
        "no_history": "કોઈ ગેમ ઇતિહાસ ઉપલબ્ધ નથી.",
        "success": "સફળ"
    },

    "Tamil": {

        "home": "முகப்பு",
        "games": "அறிவாற்றல் விளையாட்டுகள்",
        "reminders": "நினைவூட்டல்கள்",
        "history": "என் வரலாறு",
        "details": "என் விவரங்கள்",
        "reports": "அறிக்கைகள்",
        "logout": "வெளியேறு",
        "welcome": "வரவேற்கிறோம்",
        "language": "மொழி",
        "save": "சேமிக்கவும்",
        "add": "சேர்க்கவும்",
        "delete": "நீக்கவும்",
        "submit": "சமர்ப்பிக்கவும்",
        "start": "தொடங்கவும்",
        "score": "மதிப்பெண்",
        "difficulty": "சிரமம்",
        "doctor": "மருத்துவர்",
        "patient": "நோயாளர்",
        "admin": "நிர்வாகி",
        "send_report": "அறிக்கையை அனுப்பவும்",
        "select_patient": "நோயாளியைத் தேர்ந்தெடுக்கவும்",
        "no_reports": "அறிக்கைகள் இல்லை.",
        "no_history": "விளையாட்டு வரலாறு இல்லை.",
        "success": "வெற்றி"
    },

    "Telugu": {

        "home": "హోమ్",
        "games": "కాగ్నిటివ్ గేమ్స్",
        "reminders": "రిమైండర్లు",
        "history": "నా చరిత్ర",
        "details": "నా వివరాలు",
        "reports": "రిపోర్టులు",
        "logout": "లాగ్ అవుట్",
        "welcome": "స్వాగతం",
        "language": "భాష",
        "save": "సేవ్ చేయండి",
        "add": "జోడించండి",
        "delete": "తొలగించండి",
        "submit": "సమర్పించండి",
        "start": "ప్రారంభించండి",
        "score": "స్కోర్",
        "difficulty": "కష్టం",
        "doctor": "డాక్టర్",
        "patient": "రోగి",
        "admin": "అడ్మిన్",
        "send_report": "రిపోర్ట్ పంపండి",
        "select_patient": "రోగిని ఎంచుకోండి",
        "no_reports": "రిపోర్టులు లేవు.",
        "no_history": "గేమ్ చరిత్ర లేదు.",
        "success": "విజయం"
    },

    "Bengali": {

        "home": "হোম",
        "games": "কগনিটিভ গেম",
        "reminders": "রিমাইন্ডার",
        "history": "আমার ইতিহাস",
        "details": "আমার তথ্য",
        "reports": "রিপোর্ট",
        "logout": "লগআউট",
        "welcome": "স্বাগতম",
        "language": "ভাষা",
        "save": "সংরক্ষণ",
        "add": "যোগ করুন",
        "delete": "মুছুন",
        "submit": "জমা দিন",
        "start": "শুরু করুন",
        "score": "স্কোর",
        "difficulty": "কঠিনতা",
        "doctor": "ডাক্তার",
        "patient": "রোগী",
        "admin": "অ্যাডমিন",
        "send_report": "রিপোর্ট পাঠান",
        "select_patient": "রোগী নির্বাচন করুন",
        "no_reports": "কোনো রিপোর্ট নেই।",
        "no_history": "কোনো গেম ইতিহাস নেই।",
        "success": "সফল"
    }
}


def text(key, language):

    language_dict = TRANSLATIONS.get(
        language,
        TRANSLATIONS["English"]
    )

    return language_dict.get(
        key,
        TRANSLATIONS["English"].get(
            key,
            key
        )
    )


# ============================================================
# PASSWORD
# ============================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# VOICE OUTPUT
# ============================================================

def generate_voice_html(
    message,
    language="English"
):

    if not message:
        return ""

    if gTTS is None:
        return ""

    try:

        audio_buffer = io.BytesIO()

        language_code = LANGUAGES.get(
            language,
            LANGUAGES["English"]
        )["code"]

        gTTS(
            text=message,
            lang=language_code,
            slow=False
        ).write_to_fp(
            audio_buffer
        )

        audio_buffer.seek(0)

        audio_base64 = base64.b64encode(
            audio_buffer.read()
        ).decode("utf-8")

        html = f"""
        <div style="
            width:1px;
            height:1px;
            overflow:hidden;
            position:absolute;
            left:-9999px;
            top:-9999px;
        ">

            <audio
                id="mindsetuVoice"
                autoplay
                playsinline
                preload="auto"
            >

                <source
                    src="data:audio/mpeg;base64,{audio_base64}"
                    type="audio/mpeg"
                >

            </audio>

            <script>

                const audio =
                    document.getElementById(
                        "mindsetuVoice"
                    );

                if (audio) {{

                    audio.volume = 1.0;

                    const playAudio = () => {{

                        audio.play().catch(
                            () => {{}}
                        );

                    }};

                    playAudio();

                }}

            </script>

        </div>
        """

        return html

    except Exception:
        return ""


def queue_voice(
    message,
    language="English"
):

    if not message:
        return

    st.session_state.pending_voice_message = (
        message
    )

    st.session_state.pending_voice_language = (
        language
    )


def play_pending_voice():

    message = st.session_state.get(
        "pending_voice_message"
    )

    language = st.session_state.get(
        "pending_voice_language",
        "English"
    )

    if not message:
        return

    # Clear first so the same message isn't played
    # on every rerun.
    st.session_state.pending_voice_message = None
    st.session_state.pending_voice_language = None

    html = generate_voice_html(
        message,
        language
    )

    if html:

        st.html(
            html,
            width=1,
            unsafe_allow_javascript=True
        )


def announce(
    message,
    language="English"
):

    # IMPORTANT:
    #
    # This function intentionally does NOT call:
    #
    # st.success()
    # st.info()
    # st.write()
    # st.audio()
    #
    # It is voice-only.

    queue_voice(
        message,
        language
    )


# ============================================================
# VOICE RECOGNITION
# ============================================================

def recognize_voice(
    audio_bytes,
    language
):

    if sr is None:
        return None

    if not audio_bytes:
        return None

    try:

        recognizer = sr.Recognizer()

        with sr.AudioFile(
            io.BytesIO(audio_bytes)
        ) as source:

            audio = recognizer.record(
                source
            )

        speech_language = LANGUAGES.get(
            language,
            LANGUAGES["English"]
        )["speech"]

        command = recognizer.recognize_google(
            audio,
            language=speech_language
        )

        return command.lower().strip()

    except Exception:

        return None


# ============================================================
# TIME PARSER
# ============================================================

def parse_time_from_command(command):

    if not command:
        return None

    # --------------------------------------------------------
    # 24-hour format
    #
    # 17:30
    # 09:15
    # --------------------------------------------------------

    match = re.search(
        r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b",
        command
    )

    if match:

        hour = int(
            match.group(1)
        )

        minute = int(
            match.group(2)
        )

        return f"{hour:02d}:{minute:02d}"

    # --------------------------------------------------------
    # 12-hour format
    #
    # 5 PM
    # 5:30 PM
    # 10 AM
    # --------------------------------------------------------

    match = re.search(
        r"\b(1[0-2]|0?[1-9])"
        r"(?:[:.]([0-5]\d))?"
        r"\s*(am|pm)\b",
        command,
        re.IGNORECASE
    )

    if match:

        hour = int(
            match.group(1)
        )

        minute = int(
            match.group(2) or 0
        )

        am_pm = match.group(3).lower()

        if am_pm == "pm" and hour != 12:
            hour += 12

        if am_pm == "am" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute:02d}"

    return None


# ============================================================
# REMINDER TITLE FROM VOICE COMMAND
# ============================================================

def extract_reminder_title(command):

    title = command.strip()

    phrases = [

        "add a reminder",
        "add reminder",

        "set a reminder",
        "set reminder",

        "create a reminder",
        "create reminder",

        "set a time for",
        "set time for",

        "remind me to",
        "remind me"
    ]

    for phrase in phrases:

        title = title.replace(
            phrase,
            ""
        )

    title = re.sub(
        r"\b(?:at|for)\s+"
        r"(?:[01]?\d|2[0-3])[:.][0-5]\d\b",
        "",
        title
    )

    title = re.sub(
        r"\b(?:at|for)\s+"
        r"(?:1[0-2]|0?[1-9])"
        r"(?:[:.][0-5]\d)?"
        r"\s*(?:am|pm)\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = title.strip()

    if not title:
        title = "Reminder"

    return title[0].upper() + title[1:]


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_SESSION_VALUES = {

    "logged_in": False,

    "user_id": None,

    "name": "",

    "username": "",

    "role": None,

    "language": "English",

    "doctor_id": None,

    "page": "home",

    "welcome_pending": False,

    "pending_voice_message": None,

    "pending_voice_language": None,

    "memory_sequence": None,

    "pattern_sequence": None,

    "reaction_target": None
}


for key, value in DEFAULT_SESSION_VALUES.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# PLAY PENDING VOICE
# ============================================================

if st.session_state.logged_in:

    play_pending_voice()


# ============================================================
# LOGIN / REGISTRATION
# ============================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:25px;
            border-radius:20px;
            background:linear-gradient(
                135deg,
                #667eea,
                #764ba2
            );
            color:white;
        ">

            <h1>🧠 MINDSETU NER</h1>

            <p>
                Personalised Cognitive &
                Memory Companion
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    st.info(
        "MINDSETU NER is a prototype for "
        "cognitive wellness and performance tracking. "
        "It is not a medical diagnostic system."
    )

    login_tab, signup_tab = st.tabs(
        [
            "🔐 Login",
            "📝 Patient Registration"
        ]
    )

    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        st.subheader("Login")

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
            "🔐 Login",
            type="primary",
            use_container_width=True
        ):

            username_clean = (
                username.strip()
            )

            # ------------------------------------------------
            # ADMIN
            # ------------------------------------------------

            if username_clean.lower() == "admin":

                if password == "admin123":

                    st.session_state.logged_in = True
                    st.session_state.user_id = 0
                    st.session_state.name = "Administrator"
                    st.session_state.username = "admin"
                    st.session_state.role = "admin"
                    st.session_state.language = "English"
                    st.session_state.page = "home"

                    queue_voice(
                        "Welcome Administrator. "
                        "You have logged in successfully.",
                        "English"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Incorrect admin password."
                    )

            # ------------------------------------------------
            # NORMAL USER
            # ------------------------------------------------

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
                        doctor_id,
                        adaptive_difficulty
                    FROM users
                    WHERE LOWER(username)=LOWER(?)
                    """,
                    (
                        username_clean,
                    )
                ).fetchone()

                if user is None:

                    st.error(
                        "Username not found."
                    )

                elif (
                    hash_password(password)
                    != user[3]
                ):

                    st.error(
                        "Incorrect password."
                    )

                else:

                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.name = user[1]
                    st.session_state.username = user[2]
                    st.session_state.language = user[4]
                    st.session_state.role = user[5]
                    st.session_state.doctor_id = user[6]
                    st.session_state.page = "home"

                    queue_voice(
                        (
                            f"Welcome {user[1]}. "
                            "You have logged in successfully."
                        ),
                        user[4]
                    )

                    if user[5] == "patient":

                        queue_voice(
                            (
                                f"Welcome {user[1]}. "
                                "You have logged in successfully. "
                                "Now you can play cognitive games, "
                                "set reminders, check your history, "
                                "and listen to your reports."
                            ),
                            user[4]
                        )

                    elif user[5] == "doctor":

                        queue_voice(
                            (
                                f"Welcome Dr. {user[1]}. "
                                "You have logged in successfully. "
                                "You can review your assigned patients "
                                "and manage their reports."
                            ),
                            user[4]
                        )

                    st.rerun()

    # ========================================================
    # REGISTRATION
    # ========================================================

    with signup_tab:

        st.subheader(
            "Create Patient Account"
        )

        reg_name = st.text_input(
            "Full Name",
            key="reg_name"
        )

        reg_username = st.text_input(
            "Username",
            key="reg_username"
        )

        reg_password = st.text_input(
            "Password",
            type="password",
            key="reg_password"
        )

        reg_confirm = st.text_input(
            "Confirm Password",
            type="password",
            key="reg_confirm"
        )

        reg_language = st.selectbox(
            "Select Language",
            list(LANGUAGES.keys()),
            key="reg_language"
        )

        if st.button(
            "📝 Create Patient Account",
            type="primary",
            use_container_width=True
        ):

            if not reg_name.strip():

                st.error(
                    "Please enter your name."
                )

            elif not reg_username.strip():

                st.error(
                    "Please enter a username."
                )

            elif len(reg_password) < 6:

                st.error(
                    "Password must contain at least "
                    "6 characters."
                )

            elif reg_password != reg_confirm:

                st.error(
                    "Passwords do not match."
                )

            else:

                existing = conn.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE LOWER(username)=LOWER(?)
                    """,
                    (
                        reg_username.strip(),
                    )
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
                            baseline,
                            role,
                            adaptive_difficulty
                        )
                        VALUES(
                            ?,
                            ?,
                            ?,
                            ?,
                            0,
                            'patient',
                            1
                        )
                        """,
                        (
                            reg_name.strip(),
                            reg_username.strip(),
                            hash_password(
                                reg_password
                            ),
                            reg_language
                        )
                    )

                    conn.commit()

                    st.success(
                        "Patient account created successfully."
                    )

                    queue_voice(
                        (
                            f"Welcome {reg_name.strip()}. "
                            "Your patient account has been "
                            "created successfully."
                        ),
                        reg_language
                    )

                    # Play the queued registration voice.
                    play_pending_voice()

    st.stop()


# ============================================================
# CURRENT SESSION USER
# ============================================================

role = st.session_state.role
user_id = st.session_state.user_id
name = st.session_state.name
language = st.session_state.language


# ============================================================
# ADMIN DASHBOARD
# ============================================================

if role == "admin":

    st.title(
        "👑 MINDSETU NER — Administrator Dashboard"
    )

    admin_tabs = st.tabs(
        [
            "📊 Overview",
            "👥 Patients",
            "🩺 Doctors",
            "🔗 Assign Patients",
            "🎮 All Sessions",
            "📄 All Reports"
        ]
    )

    # ========================================================
    # OVERVIEW
    # ========================================================

    with admin_tabs[0]:

        patient_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE role='patient'
            """
        ).fetchone()[0]

        doctor_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE role='doctor'
            """
        ).fetchone()[0]

        session_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM sessions
            """
        ).fetchone()[0]

        report_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM reports
            """
        ).fetchone()[0]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Patients",
            patient_count
        )

        c2.metric(
            "Doctors",
            doctor_count
        )

        c3.metric(
            "Game Sessions",
            session_count
        )

        c4.metric(
            "Reports",
            report_count
        )

    # ========================================================
    # PATIENTS
    # ========================================================

    with admin_tabs[1]:

        patients = conn.execute(
            """
            SELECT
                id,
                name,
                username,
                language,
                baseline,
                doctor_id,
                adaptive_difficulty
            FROM users
            WHERE role='patient'
            ORDER BY name
            """
        ).fetchall()

        patient_data = []

        for patient_row in patients:

            doctor_name = "Not assigned"

            if patient_row[5]:

                doctor = conn.execute(
                    """
                    SELECT name
                    FROM users
                    WHERE id=?
                    AND role='doctor'
                    """,
                    (
                        patient_row[5],
                    )
                ).fetchone()

                if doctor:

                    doctor_name = (
                        "Dr. " +
                        doctor[0]
                    )

            patient_data.append(
                {
                    "ID": patient_row[0],
                    "Name": patient_row[1],
                    "Username": patient_row[2],
                    "Language": patient_row[3],
                    "Baseline": patient_row[4],
                    "Difficulty": patient_row[6],
                    "Doctor": doctor_name
                }
            )

        if patient_data:

            st.dataframe(
                patient_data,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No patients registered."
            )

    # ========================================================
    # DOCTORS
    # ========================================================

    with admin_tabs[2]:

        st.subheader(
            "➕ Add Doctor"
        )

        doctor_name = st.text_input(
            "Doctor Name",
            key="admin_doctor_name"
        )

        doctor_username = st.text_input(
            "Doctor Username",
            key="admin_doctor_username"
        )

        doctor_password = st.text_input(
            "Doctor Password",
            type="password",
            key="admin_doctor_password"
        )

        if st.button(
            "➕ Add Doctor",
            type="primary"
        ):

            if not doctor_name.strip():

                st.error(
                    "Enter doctor name."
                )

            elif not doctor_username.strip():

                st.error(
                    "Enter doctor username."
                )

            elif len(doctor_password) < 6:

                st.error(
                    "Doctor password must contain "
                    "at least 6 characters."
                )

            else:

                existing = conn.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE LOWER(username)=LOWER(?)
                    """,
                    (
                        doctor_username.strip(),
                    )
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
                            baseline,
                            role,
                            adaptive_difficulty
                        )
                        VALUES(
                            ?,
                            ?,
                            ?,
                            'English',
                            0,
                            'doctor',
                            1
                        )
                        """,
                        (
                            doctor_name.strip(),
                            doctor_username.strip(),
                            hash_password(
                                doctor_password
                            )
                        )
                    )

                    conn.commit()

                    announce(
                        "Doctor added successfully.",
                        "English"
                    )

                    st.rerun()

        st.subheader(
            "🩺 Registered Doctors"
        )

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

        if doctors:

            st.dataframe(
                [
                    {
                        "ID": doctor[0],
                        "Doctor": doctor[1],
                        "Username": doctor[2]
                    }
                    for doctor in doctors
                ],
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No doctors added yet."
            )

    # ========================================================
    # ASSIGN PATIENTS
    # ========================================================

    with admin_tabs[3]:

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

        patients = conn.execute(
            """
            SELECT
                id,
                name,
                username
            FROM users
            WHERE role='patient'
            ORDER BY name
            """
        ).fetchall()

        if not doctors:

            st.warning(
                "Add a doctor before assigning patients."
            )

        elif not patients:

            st.warning(
                "No patients are available."
            )

        else:

            doctor_options = {
                f"Dr. {d[1]} ({d[2]})": d[0]
                for d in doctors
            }

            patient_options = {
                f"{p[1]} ({p[2]})": p[0]
                for p in patients
            }

            selected_doctor = st.selectbox(
                "Select Doctor",
                list(
                    doctor_options.keys()
                ),
                key="assign_doctor"
            )

            selected_patient = st.selectbox(
                "Select Patient",
                list(
                    patient_options.keys()
                ),
                key="assign_patient"
            )

            if st.button(
                "🔗 Assign Patient to Doctor",
                type="primary"
            ):

                conn.execute(
                    """
                    UPDATE users
                    SET doctor_id=?
                    WHERE id=?
                    AND role='patient'
                    """,
                    (
                        doctor_options[
                            selected_doctor
                        ],
                        patient_options[
                            selected_patient
                        ]
                    )
                )

                conn.commit()

                announce(
                    "Patient assigned to doctor successfully.",
                    "English"
                )

                st.rerun()

            st.subheader(
                "Current Assignments"
            )

            assignments = conn.execute(
                """
                SELECT
                    p.name,
                    p.username,
                    d.name
                FROM users p
                LEFT JOIN users d
                ON p.doctor_id=d.id
                WHERE p.role='patient'
                ORDER BY p.name
                """
            ).fetchall()

            st.dataframe(
                [
                    {
                        "Patient": row[0],
                        "Username": row[1],
                        "Doctor": (
                            "Dr. " + row[2]
                            if row[2]
                            else "Not assigned"
                        )
                    }
                    for row in assignments
                ],
                use_container_width=True,
                hide_index=True
            )

    # ========================================================
    # ALL SESSIONS
    # ========================================================

    with admin_tabs[4]:

        sessions = conn.execute(
            """
            SELECT
                u.name,
                u.username,
                s.game,
                s.score,
                s.difficulty,
                s.created_at
            FROM sessions s
            INNER JOIN users u
            ON s.user_id=u.id
            ORDER BY s.id DESC
            """
        ).fetchall()

        if sessions:

            st.dataframe(
                [
                    {
                        "Patient": row[0],
                        "Username": row[1],
                        "Game": row[2],
                        "Score": row[3],
                        "Difficulty": row[4],
                        "Date": row[5]
                    }
                    for row in sessions
                ],
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No sessions available."
            )

    # ========================================================
    # ALL REPORTS
    # ========================================================

    with admin_tabs[5]:

        reports = conn.execute(
            """
            SELECT
                r.created_at,
                p.name,
                d.name,
                r.title,
                r.report_text
            FROM reports r
            INNER JOIN users p
            ON r.patient_id=p.id
            INNER JOIN users d
            ON r.doctor_id=d.id
            ORDER BY r.id DESC
            """
        ).fetchall()

        if reports:

            for report in reports:

                with st.expander(
                    f"{report[1]} — {report[3]}"
                ):

                    st.write(
                        f"Doctor: Dr. {report[2]}"
                    )

                    st.write(
                        f"Date: {report[0]}"
                    )

                    st.write(
                        report[4]
                    )

        else:

            st.info(
                "No reports available."
            )

    # ========================================================
    # ADMIN LOGOUT
    # ========================================================

    st.divider()

    if st.button(
        "🚪 Logout",
        key="admin_logout"
    ):

        st.session_state.clear()

        st.rerun()

    st.stop()


# ============================================================
# DOCTOR DASHBOARD
# ============================================================

if role == "doctor":

    st.title(
        f"🩺 Doctor Portal — Dr. {name}"
    )

    st.info(
        "Doctors can view assigned patients, "
        "review performance and send reports. "
        "Game access is disabled for doctors."
    )

    doctor_tabs = st.tabs(
        [
            "🏠 Overview",
            "👥 My Patients",
            "📊 Patient Performance",
            "📄 Send Report"
        ]
    )

    assigned_patients = conn.execute(
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
        (
            user_id,
        )
    ).fetchall()

    # ========================================================
    # DOCTOR OVERVIEW
    # ========================================================

    with doctor_tabs[0]:

        c1, c2 = st.columns(2)

        c1.metric(
            "Assigned Patients",
            len(assigned_patients)
        )

        c2.metric(
            "Your Role",
            "Doctor"
        )

        st.warning(
            "🎮 Cognitive games are not available "
            "for doctor accounts."
        )

    # ========================================================
    # DOCTOR PATIENTS
    # ========================================================

    with doctor_tabs[1]:

        if assigned_patients:

            st.dataframe(
                [
                    {
                        "Patient": p[1],
                        "Username": p[2],
                        "Language": p[3],
                        "Baseline": p[4]
                    }
                    for p in assigned_patients
                ],
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No patients have been assigned to you."
            )

    # ========================================================
    # DOCTOR PERFORMANCE
    # ========================================================

    with doctor_tabs[2]:

        if assigned_patients:

            patient_map = {
                f"{p[1]} ({p[2]})": p[0]
                for p in assigned_patients
            }

            selected_patient_name = st.selectbox(
                "Select Patient",
                list(
                    patient_map.keys()
                ),
                key="doctor_view_patient"
            )

            selected_patient_id = patient_map[
                selected_patient_name
            ]

            patient_data = conn.execute(
                """
                SELECT
                    id,
                    name,
                    username,
                    language,
                    baseline,
                    adaptive_difficulty
                FROM users
                WHERE id=?
                AND role='patient'
                AND doctor_id=?
                """,
                (
                    selected_patient_id,
                    user_id
                )
            ).fetchone()

            if patient_data:

                st.subheader(
                    f"👤 {patient_data[1]}"
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Baseline",
                    f"{patient_data[4]:.1f}"
                )

                c2.metric(
                    "Difficulty",
                    patient_data[5]
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
                    (
                        selected_patient_id,
                    )
                ).fetchall()

                scores = [
                    float(s[1])
                    for s in sessions
                ]

                average_score = (
                    sum(scores) /
                    len(scores)
                    if scores
                    else 0
                )

                best_score = (
                    max(scores)
                    if scores
                    else 0
                )

                c2.metric(
                    "Average Score",
                    f"{average_score:.1f}"
                )

                c3.metric(
                    "Best Score",
                    f"{best_score:.1f}"
                )

                if sessions:

                    st.subheader(
                        "📊 Game Performance"
                    )

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
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.info(
                        "No game sessions recorded."
                    )

    # ========================================================
    # SEND REPORT
    # ========================================================

    with doctor_tabs[3]:

        if assigned_patients:

            patient_map = {
                f"{p[1]} ({p[2]})": p[0]
                for p in assigned_patients
            }

            selected_report_patient = st.selectbox(
                "Select Patient",
                list(
                    patient_map.keys()
                ),
                key="doctor_report_patient"
            )

            report_patient_id = patient_map[
                selected_report_patient
            ]

            sessions = conn.execute(
                """
                SELECT score
                FROM sessions
                WHERE user_id=?
                """,
                (
                    report_patient_id,
                )
            ).fetchall()

            report_scores = [
                float(row[0])
                for row in sessions
            ]

            report_average = (
                sum(report_scores) /
                len(report_scores)
                if report_scores
                else 0
            )

            report_best = (
                max(report_scores)
                if report_scores
                else 0
            )

            st.write(
                f"Completed sessions: "
                f"**{len(report_scores)}**"
            )

            st.write(
                f"Average score: "
                f"**{report_average:.1f}**"
            )

            st.write(
                f"Best score: "
                f"**{report_best:.1f}**"
            )

            report_title = st.text_input(
                "Report Title",
                value="Overall Performance Report",
                key="report_title"
            )

            report_text = st.text_area(
                "Overall Performance Report",
                value=(
                    "Overall Performance Report\n\n"
                    f"Total sessions: {len(report_scores)}\n"
                    f"Average score: {report_average:.1f}\n"
                    f"Best score: {report_best:.1f}\n\n"
                    "Doctor's observations:\n"
                ),
                height=280,
                key="report_text"
            )

            if st.button(
                "📤 Send Report to Patient",
                type="primary"
            ):

                valid_patient = conn.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE id=?
                    AND role='patient'
                    AND doctor_id=?
                    """,
                    (
                        report_patient_id,
                        user_id
                    )
                ).fetchone()

                if not valid_patient:

                    st.error(
                        "You are not authorized to send "
                        "a report to this patient."
                    )

                elif not report_text.strip():

                    st.error(
                        "Report cannot be empty."
                    )

                else:

                    conn.execute(
                        """
                        INSERT INTO reports(
                            patient_id,
                            doctor_id,
                            title,
                            report_text,
                            created_at,
                            status
                        )
                        VALUES(
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            'Sent'
                        )
                        """,
                        (
                            report_patient_id,
                            user_id,
                            report_title.strip(),
                            report_text.strip(),
                            datetime.now().isoformat(
                                timespec="seconds"
                            )
                        )
                    )

                    conn.commit()

                    announce(
                        (
                            "Overall performance report "
                            "sent successfully to the patient."
                        ),
                        "English"
                    )

                    st.rerun()

        else:

            st.info(
                "Assign patients before sending reports."
            )

    # ========================================================
    # DOCTOR LOGOUT
    # ========================================================

    st.divider()

    if st.button(
        "🚪 Logout",
        key="doctor_logout"
    ):

        st.session_state.clear()

        st.rerun()

    st.stop()


# ============================================================
# LOAD PATIENT
# ============================================================

patient = conn.execute(
    """
    SELECT
        id,
        name,
        username,
        language,
        baseline,
        role,
        doctor_id,
        adaptive_difficulty
    FROM users
    WHERE id=?
    AND role='patient'
    """,
    (
        user_id,
    )
).fetchone()


if patient is None:

    st.error(
        "Patient account could not be loaded."
    )

    st.session_state.clear()

    st.stop()


# ============================================================
# REFRESH PATIENT INFORMATION
# ============================================================

user_id = patient[0]
name = patient[1]
username = patient[2]
language = patient[3]
doctor_id = patient[6]


# ============================================================
# BASELINE
# ============================================================

def calculate_baseline(
    patient_id
):

    rows = conn.execute(
        """
        SELECT score
        FROM sessions
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (
            patient_id,
        )
    ).fetchall()

    if not rows:

        return 0.0

    return round(
        sum(
            float(row[0])
            for row in rows
        ) / len(rows),
        1
    )


baseline = calculate_baseline(
    user_id
)


# ============================================================
# GET CURRENT DIFFICULTY
# ============================================================

difficulty_row = conn.execute(
    """
    SELECT adaptive_difficulty
    FROM users
    WHERE id=?
    AND role='patient'
    """,
    (
        user_id,
    )
).fetchone()


if difficulty_row:

    difficulty = int(
        difficulty_row[0] or 1
    )

else:

    difficulty = 1


difficulty = max(
    1,
    min(
        difficulty,
        3
    )
)


# ============================================================
# UPDATE DIFFICULTY
# ============================================================

def update_adaptive_difficulty(
    patient_id,
    score
):

    row = conn.execute(
        """
        SELECT adaptive_difficulty
        FROM users
        WHERE id=?
        AND role='patient'
        """,
        (
            patient_id,
        )
    ).fetchone()

    if row:

        old_difficulty = int(
            row[0] or 1
        )

    else:

        old_difficulty = 1

    # --------------------------------------------------------
    # STRONG PERFORMANCE
    # --------------------------------------------------------

    if score >= 70:

        new_difficulty = min(
            old_difficulty + 1,
            3
        )

        result = "won"

    # --------------------------------------------------------
    # WEAK PERFORMANCE
    # --------------------------------------------------------

    else:

        new_difficulty = max(
            old_difficulty - 1,
            1
        )

        result = "lost"

    conn.execute(
        """
        UPDATE users
        SET adaptive_difficulty=?
        WHERE id=?
        AND role='patient'
        """,
        (
            new_difficulty,
            patient_id
        )
    )

    conn.commit()

    return (
        old_difficulty,
        new_difficulty,
        result
    )


# ============================================================
# GAME COMPLETION VOICE
# ============================================================

def game_result_voice(
    game_name,
    score,
    old_difficulty,
    new_difficulty,
    language
):

    if score >= 70:

        message = (
            f"Congratulations! "
            f"You completed the {game_name} "
            f"with a score of {score}. "
        )

        if new_difficulty > old_difficulty:

            message += (
                f"Excellent performance. "
                f"Your difficulty has increased "
                f"to level {new_difficulty}."
            )

        else:

            message += (
                f"Your difficulty remains at "
                f"level {new_difficulty}."
            )

    else:

        message = (
            f"You completed the {game_name} "
            f"with a score of {score}. "
        )

        if new_difficulty < old_difficulty:

            message += (
                f"Keep practicing. "
                f"Your difficulty has been adjusted "
                f"to level {new_difficulty}."
            )

        else:

            message += (
                f"Your difficulty remains at "
                f"level {new_difficulty}."
            )

    return message


# ============================================================
# PATIENT SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🧠 MINDSETU NER"
    )

    st.write(
        f"👤 **{name}**"
    )

    st.caption(
        "Role: Patient"
    )

    st.divider()

    # ========================================================
    # LANGUAGE
    # ========================================================

    st.subheader(
        "🌐 " +
        text(
            "language",
            language
        )
    )

    language_options = list(
        LANGUAGES.keys()
    )

    current_index = (
        language_options.index(language)
        if language in language_options
        else 0
    )

    selected_language = st.selectbox(
        "Select Language",
        language_options,
        index=current_index,
        key="patient_language_select"
    )

    if selected_language != language:

        conn.execute(
            """
            UPDATE users
            SET language=?
            WHERE id=?
            AND role='patient'
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

        queue_voice(
            (
                "Language changed to "
                f"{selected_language} successfully."
            ),
            selected_language
        )

        st.rerun()

    # ========================================================
    # VOICE COMMANDS
    # ========================================================

    st.divider()

    st.subheader(
        "🎤 Voice"
    )

    if mic_recorder is None:

        st.warning(
            "Voice input package is not installed."
        )

    else:

        audio_data = mic_recorder(
            start_prompt="🎤",
            stop_prompt="⏹️",
            just_once=True,
            key="patient_voice_recorder"
        )

        if audio_data:

            command = recognize_voice(
                audio_data["bytes"],
                language
            )

            # ------------------------------------------------
            # IMPORTANT:
            #
            # We NEVER display:
            #
            # st.success(command)
            #
            # Therefore the user's speech is not shown.
            # ------------------------------------------------

            if command:

                # =================================================
                # LOGOUT
                # =================================================

                if (
                    "logout" in command
                    or "log out" in command
                    or "exit" in command
                ):

                    queue_voice(
                        "Logging out now.",
                        language
                    )

                    st.session_state.logged_in = False

                    st.rerun()

                # =================================================
                # GAMES
                # =================================================

                elif (
                    "game" in command
                    or "games" in command
                    or "play" in command
                    or "cognitive" in command
                ):

                    st.session_state.page = "games"

                    queue_voice(
                        (
                            "Opening cognitive games. "
                            "You can start a game whenever you are ready."
                        ),
                        language
                    )

                    st.rerun()

                # =================================================
                # REMINDERS
                # =================================================

                elif (
                    "reminder" in command
                    or "reminders" in command
                    or "remind me" in command
                    or "set time" in command
                    or "set a time" in command
                ):

                    reminder_time = (
                        parse_time_from_command(
                            command
                        )
                    )

                    if reminder_time:

                        reminder_title = (
                            extract_reminder_title(
                                command
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
                                reminder_title,
                                (
                                    f"{date.today()} "
                                    f"{reminder_time}"
                                )
                            )
                        )

                        conn.commit()

                        queue_voice(
                            (
                                f"{reminder_title} "
                                f"reminder has been added "
                                f"for {reminder_time}."
                            ),
                            language
                        )

                    else:

                        queue_voice(
                            (
                                "I heard the reminder request, "
                                "but I could not understand the time. "
                                "Please say something like "
                                "set reminder drink water at 5 PM."
                            ),
                            language
                        )

                    st.session_state.page = "reminders"

                    st.rerun()

                # =================================================
                # REPORTS
                # =================================================

                elif (
                    "report" in command
                    or "reports" in command
                ):

                    st.session_state.page = "reports"

                    queue_voice(
                        "Opening your reports.",
                        language
                    )

                    st.rerun()

                # =================================================
                # HISTORY
                # =================================================

                elif (
                    "history" in command
                    or "performance" in command
                ):

                    st.session_state.page = "history"

                    queue_voice(
                        "Opening your performance history.",
                        language
                    )

                    st.rerun()

                # =================================================
                # DETAILS
                # =================================================

                elif (
                    "details" in command
                    or "profile" in command
                    or "my data" in command
                ):

                    st.session_state.page = "details"

                    queue_voice(
                        "Opening your details.",
                        language
                    )

                    st.rerun()

                # =================================================
                # HOME
                # =================================================

                elif (
                    "home" in command
                    or "dashboard" in command
                ):

                    st.session_state.page = "home"

                    queue_voice(
                        "Opening your dashboard.",
                        language
                    )

                    st.rerun()

                # =================================================
                # UNKNOWN COMMAND
                # =================================================

                else:

                    queue_voice(
                        (
                            "Sorry, I did not understand "
                            "that command. "
                            "You can say open games, "
                            "open reminders, "
                            "open reports, "
                            "open history, "
                            "open details, "
                            "go home, "
                            "or logout."
                        ),
                        language
                    )

                    st.rerun()

            else:

                queue_voice(
                    (
                        "Sorry, I could not understand "
                        "your voice. Please try again."
                    ),
                    language
                )

                st.rerun()

    st.divider()

    # ========================================================
    # LOGOUT BUTTON
    # ========================================================

    if st.button(
        "🚪 " +
        text(
            "logout",
            language
        ),
        use_container_width=True
    ):

        queue_voice(
            "Logging out now. Goodbye.",
            language
        )

        st.session_state.logged_in = False

        st.rerun()


# ============================================================
# PATIENT NAVIGATION
# ============================================================

page_names = {

    "home":
        "🏠 " +
        text(
            "home",
            language
        ),

    "games":
        "🎮 " +
        text(
            "games",
            language
        ),

    "reminders":
        "⏰ " +
        text(
            "reminders",
            language
        ),

    "history":
        "📜 " +
        text(
            "history",
            language
        ),

    "details":
        "👤 " +
        text(
            "details",
            language
        ),

    "reports":
        "📄 " +
        text(
            "reports",
            language
        )
}


page_keys = list(
    page_names.keys()
)


current_page = st.session_state.page


if current_page not in page_keys:

    current_page = "home"


selected_page = st.radio(
    "Navigation",
    page_keys,
    format_func=lambda key: page_names[key],
    horizontal=True,
    index=page_keys.index(
        current_page
    )
)


st.session_state.page = selected_page


# ============================================================
# PATIENT HOME
# ============================================================

if selected_page == "home":

    st.markdown(
        f"""
        <div style="
            padding:25px;
            border-radius:20px;
            background:linear-gradient(
                135deg,
                #667eea,
                #764ba2
            );
            color:white;
        ">

            <h1>
                🧠 {text("welcome", language)},
                {name}!
            </h1>

            <p>
                Your personalised
                MINDSETU NER dashboard
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    total_sessions = conn.execute(
        """
        SELECT COUNT(*)
        FROM sessions
        WHERE user_id=?
        """,
        (
            user_id,
        )
    ).fetchone()[0]

    report_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM reports
        WHERE patient_id=?
        """,
        (
            user_id,
        )
    ).fetchone()[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Personal Baseline",
        f"{baseline:.1f}"
    )

    c2.metric(
        "Difficulty",
        difficulty
    )

    c3.metric(
        "Sessions",
        total_sessions
    )

    c4.metric(
        "Reports",
        report_count
    )

    st.divider()

    if doctor_id:

        doctor = conn.execute(
            """
            SELECT
                name,
                username
            FROM users
            WHERE id=?
            AND role='doctor'
            """,
            (
                doctor_id,
            )
        ).fetchone()

        if doctor:

            st.success(
                f"🩺 Assigned Doctor: "
                f"Dr. {doctor[0]}"
            )

    else:

        st.info(
            "🩺 No doctor has been assigned yet."
        )

    st.info(
        "Your game difficulty adapts after every "
        "completed game. Strong performance increases "
        "the difficulty; weaker performance decreases it."
    )


# ============================================================
# COGNITIVE GAMES
# ============================================================

elif selected_page == "games":

    st.title(
        "🎮 " +
        text(
            "games",
            language
        )
    )

    st.write(
        f"Adaptive difficulty level: "
        f"**{difficulty} / 3**"
    )

    game_tab1, game_tab2, game_tab3 = st.tabs(
        [
            "🧠 Memory Sequence",
            "🔷 Pattern Memory",
            "⚡ Attention Game"
        ]
    )

    # ========================================================
    # MEMORY SEQUENCE
    # ========================================================

    with game_tab1:

        st.subheader(
            "🧠 Memory Sequence"
        )

        sequence_length = {

            1: 4,

            2: 6,

            3: 8

        }[difficulty]

        if st.session_state.memory_sequence is None:

            st.write(
                f"Remember {sequence_length} numbers."
            )

            if st.button(
                "▶️ Start Memory Game",
                type="primary",
                key="memory_start"
            ):

                st.session_state.memory_sequence = (
                    random.sample(
                        range(1, 10),
                        sequence_length
                    )
                )

                queue_voice(
                    (
                        f"Memory game started. "
                        f"Remember {sequence_length} numbers."
                    ),
                    language
                )

                st.rerun()

        else:

            sequence = (
                st.session_state.memory_sequence
            )

            st.success(
                "Remember this sequence:"
            )

            st.markdown(
                "## " +
                " • ".join(
                    str(number)
                    for number in sequence
                )
            )

            answer = st.text_input(
                "Enter the numbers in the same order",
                key="memory_answer"
            )

            if st.button(
                "Submit Memory Answer",
                key="memory_submit"
            ):

                try:

                    user_answer = [

                        int(x)

                        for x in re.split(
                            r"[,\s]+",
                            answer.strip()
                        )

                        if x

                    ]

                    if len(user_answer) != len(sequence):

                        queue_voice(
                            (
                                f"Please enter exactly "
                                f"{len(sequence)} numbers."
                            ),
                            language
                        )

                        st.error(
                            f"Enter exactly "
                            f"{len(sequence)} numbers."
                        )

                    else:

                        correct = sum(
                            a == b
                            for a, b in zip(
                                sequence,
                                user_answer
                            )
                        )

                        score = round(
                            (
                                correct /
                                len(sequence)
                            ) * 100,
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

                        old_difficulty, new_difficulty, result = (
                            update_adaptive_difficulty(
                                user_id,
                                score
                            )
                        )

                        st.session_state.memory_sequence = None

                        queue_voice(
                            game_result_voice(
                                "Memory Game",
                                score,
                                old_difficulty,
                                new_difficulty,
                                language
                            ),
                            language
                        )

                        st.rerun()

                except ValueError:

                    queue_voice(
                        "Please enter numbers only.",
                        language
                    )

                    st.error(
                        "Please enter numbers only."
                    )

    # ========================================================
    # PATTERN MEMORY
    # ========================================================

    with game_tab2:

        st.subheader(
            "🔷 Pattern Memory"
        )

        pattern_length = {

            1: 4,

            2: 6,

            3: 8

        }[difficulty]

        symbols = [

            "▲",

            "●",

            "■",

            "◆"

        ]

        if st.session_state.pattern_sequence is None:

            st.write(
                f"Remember {pattern_length} symbols."
            )

            if st.button(
                "▶️ Start Pattern Game",
                type="primary",
                key="pattern_start"
            ):

                st.session_state.pattern_sequence = [

                    random.choice(symbols)

                    for _ in range(
                        pattern_length
                    )

                ]

                queue_voice(
                    (
                        f"Pattern game started. "
                        f"Remember {pattern_length} symbols."
                    ),
                    language
                )

                st.rerun()

        else:

            pattern = (
                st.session_state.pattern_sequence
            )

            st.success(
                "Remember this pattern:"
            )

            st.markdown(
                "## " +
                " ".join(pattern)
            )

            pattern_answer = st.text_input(
                "Enter the pattern using symbols",
                placeholder="Example: ▲ ● ■ ◆",
                key="pattern_answer"
            )

            if st.button(
                "Submit Pattern Answer",
                key="pattern_submit"
            ):

                answer_symbols = (
                    pattern_answer
                    .strip()
                    .split()
                )

                if len(answer_symbols) != len(pattern):

                    queue_voice(
                        (
                            f"Please enter exactly "
                            f"{len(pattern)} symbols."
                        ),
                        language
                    )

                    st.error(
                        f"Enter exactly "
                        f"{len(pattern)} symbols."
                    )

                else:

                    correct = sum(
                        a == b
                        for a, b in zip(
                            pattern,
                            answer_symbols
                        )
                    )

                    score = round(
                        (
                            correct /
                            len(pattern)
                        ) * 100,
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
                            "Pattern Memory",
                            score,
                            difficulty,
                            datetime.now().isoformat(
                                timespec="seconds"
                            )
                        )
                    )

                    conn.commit()

                    old_difficulty, new_difficulty, result = (
                        update_adaptive_difficulty(
                            user_id,
                            score
                        )
                    )

                    st.session_state.pattern_sequence = None

                    queue_voice(
                        game_result_voice(
                            "Pattern Memory Game",
                            score,
                            old_difficulty,
                            new_difficulty,
                            language
                        ),
                        language
                    )

                    st.rerun()

    # ========================================================
    # ATTENTION GAME
    # ========================================================

    with game_tab3:

        st.subheader(
            "⚡ Attention Game"
        )

        st.write(
            "Click the target number."
        )

        if st.session_state.reaction_target is None:

            if st.button(
                "▶️ Start Attention Game",
                type="primary",
                key="attention_start"
            ):

                st.session_state.reaction_target = (
                    random.randint(
                        1,
                        9
                    )
                )

                queue_voice(
                    "Attention game started. "
                    "Find the target number.",
                    language
                )

                st.rerun()

        else:

            target = (
                st.session_state.reaction_target
            )

            st.markdown(
                f"## Find: **{target}**"
            )

            cols = st.columns(3)

            numbers = list(
                range(1, 10)
            )

            random.shuffle(numbers)

            for index, number in enumerate(
                numbers
            ):

                with cols[index % 3]:

                    if st.button(
                        str(number),
                        key=f"attention_{number}"
                    ):

                        if number == target:

                            score = 100

                        else:

                            score = 0

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
                                "Attention Game",
                                score,
                                difficulty,
                                datetime.now().isoformat(
                                    timespec="seconds"
                                )
                            )
                        )

                        conn.commit()

                        old_difficulty, new_difficulty, result = (
                            update_adaptive_difficulty(
                                user_id,
                                score
                            )
                        )

                        st.session_state.reaction_target = None

                        queue_voice(
                            game_result_voice(
                                "Attention Game",
                                score,
                                old_difficulty,
                                new_difficulty,
                                language
                            ),
                            language
                        )

                        st.rerun()


# ============================================================
# REMINDERS
# ============================================================

elif selected_page == "reminders":

    st.title(
        "⏰ " +
        text(
            "reminders",
            language
        )
    )

    st.subheader(
        "➕ Add New Reminder"
    )

    reminder_title = st.text_input(
        "Reminder Title",
        placeholder="Example: Drink water",
        key="reminder_title"
    )

    reminder_time = st.time_input(
        "Reminder Time",
        value=time(9, 0),
        key="reminder_time"
    )

    if st.button(
        "➕ Add Reminder",
        type="primary"
    ):

        if not reminder_title.strip():

            queue_voice(
                "Please enter a reminder.",
                language
            )

            st.error(
                "Please enter a reminder."
            )

        else:

            formatted_time = (
                reminder_time.strftime(
                    "%H:%M"
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
                    reminder_title.strip(),
                    (
                        f"{date.today()} "
                        f"{formatted_time}"
                    )
                )
            )

            conn.commit()

            queue_voice(
                (
                    f"{reminder_title.strip()} "
                    f"reminder has been added "
                    f"for {formatted_time}."
                ),
                language
            )

            st.rerun()

    st.divider()

    reminders = conn.execute(
        """
        SELECT
            id,
            title,
            due_time,
            status
        FROM reminders
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (
            user_id,
        )
    ).fetchall()

    if not reminders:

        st.info(
            "No reminders added yet."
        )

    else:

        for reminder in reminders:

            col1, col2, col3, col4 = st.columns(
                [4, 2, 1, 1]
            )

            col1.write(
                f"**{reminder[1]}**"
            )

            col2.write(
                reminder[2]
            )

            if reminder[3] == "Done":

                col3.success(
                    "Done"
                )

            else:

                if col3.button(
                    "Done",
                    key=f"reminder_done_{reminder[0]}"
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

                    queue_voice(
                        (
                            f"Congratulations! "
                            f"You completed your reminder: "
                            f"{reminder[1]}."
                        ),
                        language
                    )

                    st.rerun()

            if col4.button(
                "Delete",
                key=f"reminder_delete_{reminder[0]}"
            ):

                conn.execute(
                    """
                    DELETE FROM reminders
                    WHERE id=?
                    AND user_id=?
                    """,
                    (
                        reminder[0],
                        user_id
                    )
                )

                conn.commit()

                queue_voice(
                    "Reminder deleted successfully.",
                    language
                )

                st.rerun()


# ============================================================
# HISTORY
# ============================================================

elif selected_page == "history":

    st.title(
        "📜 " +
        text(
            "history",
            language
        )
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
        (
            user_id,
        )
    ).fetchall()

    if not sessions:

        st.info(
            text(
                "no_history",
                language
            )
        )

    else:

        c1, c2, c3 = st.columns(3)

        scores = [
            float(row[1])
            for row in sessions
        ]

        c1.metric(
            "Personal Baseline",
            f"{baseline:.1f}"
        )

        c2.metric(
            "Average",
            f"{sum(scores) / len(scores):.1f}"
        )

        c3.metric(
            "Current Difficulty",
            difficulty
        )

        st.dataframe(
            [
                {
                    "Game": row[0],
                    "Score": row[1],
                    "Difficulty": row[2],
                    "Date": row[3]
                }
                for row in sessions
            ],
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# DETAILS
# ============================================================

elif selected_page == "details":

    st.title(
        "👤 " +
        text(
            "details",
            language
        )
    )

    st.write(
        f"**Name:** {name}"
    )

    st.write(
        f"**Username:** {username}"
    )

    st.write(
        "**Role:** Patient"
    )

    st.write(
        f"**Language:** {language}"
    )

    st.write(
        f"**Personal Baseline:** {baseline:.1f}"
    )

    st.write(
        f"**Adaptive Difficulty:** "
        f"{difficulty}/3"
    )

    if doctor_id:

        doctor = conn.execute(
            """
            SELECT
                name,
                username
            FROM users
            WHERE id=?
            AND role='doctor'
            """,
            (
                doctor_id,
            )
        ).fetchone()

        if doctor:

            st.success(
                f"🩺 Assigned Doctor: Dr. {doctor[0]}"
            )

            st.write(
                f"Doctor Username: {doctor[1]}"
            )

    else:

        st.info(
            "No doctor assigned."
        )


# ============================================================
# REPORTS
# ============================================================

elif selected_page == "reports":

    st.title(
        "📄 " +
        text(
            "reports",
            language
        )
    )

    reports = conn.execute(
        """
        SELECT
            r.id,
            r.title,
            r.report_text,
            r.created_at,
            d.name
        FROM reports r
        INNER JOIN users d
        ON r.doctor_id=d.id
        WHERE r.patient_id=?
        ORDER BY r.id DESC
        """,
        (
            user_id,
        )
    ).fetchall()

    if not reports:

        st.info(
            text(
                "no_reports",
                language
            )
        )

    else:

        for report in reports:

            with st.expander(
                f"📄 {report[1]} — {report[3]}"
            ):

                st.write(
                    f"🩺 Doctor: Dr. {report[4]}"
                )

                st.divider()

                st.write(
                    report[2]
                )

                if st.button(
                    "🔊 Listen to Report",
                    key=f"listen_report_{report[0]}"
                ):

                    # Voice only.
                    # NO st.audio()
                    # NO success message.

                    queue_voice(
                        report[2],
                        language
                    )

                    st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🧠 MINDSETU NER | Cognitive Wellness Prototype"
)

st.caption(
    "For demonstration and educational purposes only. "
    "This prototype does not provide medical diagnosis."
)
