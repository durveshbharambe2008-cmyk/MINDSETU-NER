# ============================================================
# SMRITISETU - COMPLETE VOICE-FIRST STREAMLIT APP
# ============================================================
#
# FEATURES
#
# 1. Patient / Doctor / Admin roles
# 2. Patient registration and login
# 3. Admin dashboard
# 4. Admin can add doctors
# 5. Provider-driven patient relationships
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
# 27. Game Exit Option
# 28. 15-20 Round Cognitive Games
# 29. Last 5 Games Progress Graph
# 30. North-East Regional Language Options
# 31. Doctor Registration + Qualification Verification
# 32. Caretaker Registration
# 33. Phone / Email / Location for providers and patients
# 34. Provider-driven doctor/caretaker/patient registration
# 35. Doctor -> caretaker/patient registration
# 36. Caretaker -> patient registration
# 37. Provider-owned patient privacy
# 38. 10-second Memory Sequence viewing period
# 39. Memory sequence hides automatically before answer entry
# 40. Congratulations message after strong game completion
# 41. Visible adaptive difficulty increase notification
# 42. Image Recognition / Image Memory Game
# 43. 10-second image viewing countdown
# 44. Image answers activate only after countdown reaches 0
# 45. Image game results saved to performance history
# 46. Schulte Table Matrix game
# 47. Spot the Difference game
# 48. Hidden Object Search game
# 49. Target Tracker game
# 50. Supabase/PostgreSQL production database with fail-closed protection
# 51. Admin database health indicator
# 52. Explicit opt-in SQLite only for local development
#
# INSTALL:
#
# pip install streamlit gTTS SpeechRecognition streamlit-mic-recorder reportlab pandas streamlit-autorefresh psycopg2-binary
#
# RUN:
#
# streamlit run app.py
#
# ============================================================

import streamlit as st
import random
import hashlib
import io
import re
import base64
import math
import textwrap
import os
import sqlite3
import psycopg2
from pathlib import Path
from PIL import Image
import pandas as pd

from datetime import datetime, date, time
from uuid import uuid4
import time as pytime

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        KeepTogether,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


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


# Reliable one-second browser-driven reruns for countdown games.
# This is used instead of time.sleep(), which would block Streamlit UI updates.
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None


# ============================================================
# SMRITISETU BRANDING
# ============================================================
# Keep smritisetu_logo.png in the same folder as app.py on GitHub/Streamlit Cloud.
# PNG is used first because it is more reliable for Streamlit page images.
APP_NAME = "SMRITISETU"
APP_DIR = Path(__file__).resolve().parent
APP_LOGO_PNG = APP_DIR / "smritisetu_logo.png"
APP_LOGO_JPEG = APP_DIR / "smritisetu_logo.jpeg"


def load_app_logo():
    """Safely load the SMRITISETU logo without crashing the app if a file is missing/corrupt."""
    for logo_path in (APP_LOGO_PNG, APP_LOGO_JPEG):
        if logo_path.exists():
            try:
                with Image.open(logo_path) as img:
                    img.load()
                    return img.copy()
            except Exception:
                continue
    return None


APP_LOGO = load_app_logo()


def normalize_image_for_streamlit(image_data):
    """Return a Streamlit-safe image value for DB/file image data.

    PostgreSQL BYTEA values can be returned by psycopg2 as ``memoryview``
    objects. ``st.image`` does not reliably accept that type, so convert it
    (and bytearray) to plain bytes before rendering.
    """
    if image_data is None:
        return None
    if isinstance(image_data, memoryview):
        return image_data.tobytes()
    if isinstance(image_data, bytearray):
        return bytes(image_data)
    return image_data


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_LOGO if APP_LOGO is not None else "🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit's default top-right controls and place the SMRITISETU logo
# in their place. The logo remains visible while the large center logo is removed.
try:
    if APP_LOGO is not None:
        logo_buffer = io.BytesIO()
        APP_LOGO.save(logo_buffer, format="PNG")
        logo_b64 = base64.b64encode(logo_buffer.getvalue()).decode("utf-8")
        st.markdown(f"""
        <style>
            #MainMenu {{ visibility: hidden; }}
            footer {{ visibility: hidden; }}
            [data-testid="stToolbar"] {{ visibility: hidden !important; }}
            [data-testid="stDecoration"] {{ visibility: hidden !important; }}
            [data-testid="stStatusWidget"] {{ visibility: hidden !important; display: none !important; }}
            .stStatusWidget {{ visibility: hidden !important; display: none !important; }}
            .smritisetu-fixed-logo {{
                position: fixed;
                top: 8px;
                right: 14px;
                width: 52px;
                height: 52px;
                object-fit: contain;
                border-radius: 50%;
                z-index: 999999;
                background: white;
                box-shadow: 0 2px 10px rgba(0,0,0,0.25);
            }}
        </style>
        <img class="smritisetu-fixed-logo" src="data:image/png;base64,{logo_b64}" alt="SMRITISETU logo" />
        """, unsafe_allow_html=True)
except Exception:
    pass



# ============================================================
# CLINICAL-STYLE PROGRESS REPORT PDF
# ============================================================

REPORT_GREEN = colors.HexColor("#005B4F") if REPORTLAB_AVAILABLE else None
REPORT_DARK = colors.HexColor("#253047") if REPORTLAB_AVAILABLE else None
REPORT_LIGHT = colors.HexColor("#F4F7FA") if REPORTLAB_AVAILABLE else None
REPORT_BORDER = colors.HexColor("#D9E2EC") if REPORTLAB_AVAILABLE else None
REPORT_TEAL = colors.HexColor("#00A67A") if REPORTLAB_AVAILABLE else None


def safe_pdf_text(value):
    """Keep generated PDFs readable and avoid accidental unsupported glyphs."""
    if value is None:
        return "Not provided"
    return str(value).replace("–", "-").replace("—", "-")


def generate_automatic_doctor_observation(
    patient_name,
    sessions,
    current_difficulty,
    baseline,
    doctor_name=None,
):
    """
    Generate a neutral, data-driven observation automatically from the
    patient's recorded app performance. This is NOT a medical diagnosis
    and is not presented as a real doctor's authored note.
    """
    scores = [float(row[1]) for row in sessions]
    total = len(scores)
    average = sum(scores) / total if total else 0.0
    best = max(scores) if scores else 0.0
    lowest = min(scores) if scores else 0.0

    if total == 0:
        return (
            f"Patient {patient_name} has no recorded cognitive game sessions yet. "
            "There is insufficient performance data to generate an observation. "
            "Begin regular cognitive sessions to establish a longitudinal baseline."
        )

    strong = sum(1 for s in scores if s >= 70)
    weak = sum(1 for s in scores if s < 70)

    # Trend from first half to second half of sessions.
    midpoint = max(1, total // 2)
    early_avg = sum(scores[:midpoint]) / len(scores[:midpoint])
    late_avg = sum(scores[midpoint:]) / len(scores[midpoint:]) if total > midpoint else early_avg
    trend_change = late_avg - early_avg

    parts = []
    parts.append(
        f"Automated performance observation for {patient_name}: "
        f"{total} cognitive session(s) recorded with an average score of "
        f"{average:.1f}/100 and a best score of {best:.0f}/100."
    )

    if average >= 80:
        parts.append(
            "Overall performance is strong across the recorded sessions. "
            "The patient is demonstrating consistent task completion at the current level."
        )
    elif average >= 60:
        parts.append(
            "Overall performance is moderate. The patient is completing tasks with "
            "variable performance and may benefit from continued structured practice."
        )
    else:
        parts.append(
            "Overall performance is below the application's strong-performance threshold. "
            "Continued guided practice may help establish a more stable performance pattern."
        )

    if trend_change >= 10:
        parts.append(
            f"Recent session performance is improving by approximately {trend_change:.1f} points "
            "compared with the earlier recorded sessions."
        )
    elif trend_change <= -10:
        parts.append(
            f"Recent session performance is lower by approximately {abs(trend_change):.1f} points "
            "compared with the earlier recorded sessions."
        )
    else:
        parts.append(
            "Recent performance is relatively stable compared with the earlier recorded sessions."
        )

    parts.append(
        f"Strong-performance sessions: {strong}; lower-performance sessions: {weak}. "
        f"Current adaptive difficulty: level {int(current_difficulty or 1)}."
    )

    if baseline and float(baseline) > 0:
        parts.append(
            f"Recorded personal baseline: {float(baseline):.1f}/100."
        )

    parts.append(
        "This observation is generated automatically from application records and "
        "should not be treated as a medical diagnosis or a substitute for evaluation "
        "by a qualified clinician."
    )

    return " ".join(parts)


def build_patient_progress_pdf(patient_id):
    """
    Build a clinical-report-inspired PDF using only data available in the app.
    This intentionally does NOT claim medical verification, diagnosis, ISO, or HL7 compliance.
    Returns PDF bytes, or None when ReportLab is unavailable.
    """
    if not REPORTLAB_AVAILABLE:
        return None

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
        (patient_id,)
    ).fetchone()

    if not patient:
        return None

    sessions = conn.execute(
        """
        SELECT
            game,
            score,
            difficulty,
            created_at
        FROM sessions
        WHERE user_id=?
        ORDER BY id ASC
        """,
        (patient_id,)
    ).fetchall()

    reminders = conn.execute(
        """
        SELECT
            title,
            due_time,
            status
        FROM reminders
        WHERE user_id=?
        ORDER BY due_time ASC
        LIMIT 12
        """,
        (patient_id,)
    ).fetchall()

    doctor_name = "Not assigned"
    if patient[6]:
        doctor = conn.execute(
            """
            SELECT name
            FROM users
            WHERE id=?
            AND role='doctor'
            """,
            (patient[6],)
        ).fetchone()
        if doctor:
            doctor_name = f"Dr. {doctor[0]}"

    # Get the latest actual doctor report, when one exists.
    latest_doctor_report = conn.execute(
        """
        SELECT
            r.title,
            r.report_text,
            r.created_at,
            d.name
        FROM reports r
        INNER JOIN users d
        ON r.doctor_id=d.id
        WHERE r.patient_id=?
        AND d.role='doctor'
        ORDER BY r.id DESC
        LIMIT 1
        """,
        (patient_id,)
    ).fetchone()

    total_sessions = len(sessions)
    scores = [float(row[1]) for row in sessions]
    mean_accuracy = round(sum(scores) / len(scores), 1) if scores else 0.0
    best_score = max(scores) if scores else 0.0
    mean_latency = "Not available"

    # Automatically generate a data-driven observation for every report.
    auto_observation = generate_automatic_doctor_observation(
        patient_name=patient[1],
        sessions=sessions,
        current_difficulty=patient[7] or 1,
        baseline=patient[4] or 0,
        doctor_name=(
            f"Dr. {latest_doctor_report[3]}"
            if latest_doctor_report else doctor_name
        ),
    )

    # If a real doctor report exists, retain it as an additional note rather
    # than requiring manual entry for the automatic observation.
    doctor_observation = {
        "title": "Automatically Generated Performance Observation",
        "text": auto_observation,
        "date": datetime.now().strftime("%d %b %Y %H:%M"),
        "doctor": (
            f"Dr. {latest_doctor_report[3]}"
            if latest_doctor_report
            else "System-generated"
        ),
        "is_automatic": True,
        "source_report": (
            {
                "title": safe_pdf_text(latest_doctor_report[0]),
                "text": safe_pdf_text(latest_doctor_report[1]),
                "date": safe_pdf_text(latest_doctor_report[2]),
                "doctor": f"Dr. {safe_pdf_text(latest_doctor_report[3])}",
            }
            if latest_doctor_report else None
        ),
    }

    # Group sessions into a compact cognitive-assessment table.
    grouped = {}
    for game, score, diff, created_at in sessions:
        key = safe_pdf_text(game)
        item = grouped.setdefault(
            key,
            {"count": 0, "scores": [], "difficulty": [], "dates": []}
        )
        item["count"] += 1
        item["scores"].append(float(score))
        item["difficulty"].append(int(diff or 1))
        item["dates"].append(created_at)

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="SMRITISETU Cognitive Progress Report",
        author="SMRITISETU",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        textColor=colors.white,
        spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    ))
    styles.add(ParagraphStyle(
        name="Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=REPORT_DARK,
        spaceBefore=7,
        spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="Small",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#5C6670"),
    ))
    styles.add(ParagraphStyle(
        name="BodySmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#4D5560"),
    ))
    styles.add(ParagraphStyle(
        name="MetricLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#61708A"),
    ))
    styles.add(ParagraphStyle(
        name="MetricValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        textColor=REPORT_GREEN,
    ))
    styles.add(ParagraphStyle(
        name="MetricSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6,
        leading=7,
        textColor=colors.HexColor("#718096"),
    ))

    story = []

    # Header matching the reference report's visual hierarchy.
    header_table = Table([
        [
            [
                Paragraph("SMRITISETU COGNITIVE HEALTH PLATFORM", styles["ReportTitle"]),
                Paragraph("Cognitive wellness and longitudinal performance report", styles["ReportSubtitle"]),
                Paragraph("Clinical-style summary generated from application data", styles["ReportSubtitle"]),
            ],
            [
                Paragraph("<b>APPLICATION REPORT</b><br/><font size='7'>Not a medical diagnosis or verified medical record</font>", styles["BodySmall"])
            ]
        ]],
        colWidths=[150 * mm, 0],
    )

    # Use a simpler two-column header to avoid unsupported nested widths.
    header_table = Table([
        [
            [
                Paragraph("SMRITISETU COGNITIVE HEALTH PLATFORM", styles["ReportTitle"]),
                Paragraph("Cognitive wellness and longitudinal performance report", styles["ReportSubtitle"]),
                Paragraph("Clinical-style summary generated from application data", styles["ReportSubtitle"]),
            ],
            Paragraph("<b>APPLICATION REPORT</b><br/><font size='7'>Not a medical diagnosis</font>", styles["BodySmall"]),
        ]
    ], colWidths=[135 * mm, 40 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), REPORT_GREEN),
        ("BOX", (0, 0), (-1, -1), 0, REPORT_GREEN),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TEXTCOLOR", (1, 0), (1, 0), colors.white),
        ("BACKGROUND", (1, 0), (1, 0), colors.white),
        ("BOX", (1, 0), (1, 0), 0.6, colors.white),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 7 * mm))

    report_id = f"MNE-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6].upper()}"
    generated_at = datetime.now().strftime("%d %b %Y %H:%M:%S")

    meta_table = Table([
        [
            Paragraph("<b>COGNITIVE PROGRESS SUMMARY</b>", styles["BodySmall"]),
        ],
        [
            Paragraph(
                f"Report ID: {safe_pdf_text(report_id)} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"Generated: {safe_pdf_text(generated_at)} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"App User: {safe_pdf_text(patient[2])}",
                styles["Small"]
            )
        ]
    ], colWidths=[175 * mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.6, REPORT_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)

    def section_title(number, title):
        table = Table([["", Paragraph(f"{number}. {title}", styles["Section"])]], colWidths=[5 * mm, 170 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), REPORT_TEAL),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        return table

    # Section 1 - Profile.
    story.append(section_title(1, "PATIENT PROFILE & APPLICATION DETAILS"))
    profile_data = [
        [Paragraph("<b>Patient Name:</b>", styles["BodySmall"]), safe_pdf_text(patient[1]), Paragraph("<b>Username:</b>", styles["BodySmall"]), safe_pdf_text(patient[2])],
        [Paragraph("<b>Role:</b>", styles["BodySmall"]), safe_pdf_text(patient[5].title()), Paragraph("<b>Language:</b>", styles["BodySmall"]), safe_pdf_text(patient[3])],
        [Paragraph("<b>Personal Baseline:</b>", styles["BodySmall"]), f"{float(patient[4] or 0):.1f}", Paragraph("<b>Adaptive Difficulty:</b>", styles["BodySmall"]), str(int(patient[7] or 1))],
        [Paragraph("<b>Assigned Provider:</b>", styles["BodySmall"]), safe_pdf_text(doctor_name), Paragraph("<b>Clinical Fields:</b>", styles["BodySmall"]), "Provider-managed onboarding"],
    ]
    profile_table = Table(profile_data, colWidths=[36 * mm, 52 * mm, 38 * mm, 49 * mm])
    profile_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, REPORT_BORDER),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F5F8FA")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F5F8FA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (1, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (1, 0), (-1, -1), 7.5),
        ("TEXTCOLOR", (1, 0), (-1, -1), colors.HexColor("#4D5560")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 5 * mm))

    # Section 2 - Metrics.
    story.append(section_title(2, "LONGITUDINAL COGNITIVE METRICS & PERFORMANCE INDICES"))
    metric_values = [
        ("TOTAL SESSIONS", str(total_sessions), "Evaluated runs"),
        ("MEAN SCORE", f"{mean_accuracy:.0f}%", "Average game score"),
        ("BEST SCORE", f"{best_score:.0f}", "Highest recorded score"),
        ("ADAPTIVE LEVEL", str(int(patient[7] or 1)), "Current difficulty"),
    ]
    metric_cells = []
    for label, value, sub in metric_values:
        metric_cells.append([
            Paragraph(label, styles["MetricLabel"]),
            Paragraph(value, styles["MetricValue"]),
            Paragraph(sub, styles["MetricSub"]),
        ])
    metric_table = Table([metric_cells], colWidths=[43.5 * mm] * 4)
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FBFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, REPORT_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, REPORT_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(metric_table)
    story.append(Spacer(1, 3 * mm))

    assessment_rows = [[
        Paragraph("<b>Cognitive Assessment</b>", styles["BodySmall"]),
        Paragraph("<b>Sessions</b>", styles["BodySmall"]),
        Paragraph("<b>Mean Score</b>", styles["BodySmall"]),
        Paragraph("<b>Difficulty</b>", styles["BodySmall"]),
        Paragraph("<b>Application Interpretation</b>", styles["BodySmall"]),
    ]]
    for game, info in grouped.items():
        avg = sum(info["scores"]) / len(info["scores"])
        avg_diff = round(sum(info["difficulty"]) / len(info["difficulty"]))
        interpretation = (
            "Strong performance recorded."
            if avg >= 70 else
            "Performance may benefit from continued practice."
        )
        assessment_rows.append([
            Paragraph(safe_pdf_text(game), styles["BodySmall"]),
            str(info["count"]),
            f"{avg:.0f}%",
            str(avg_diff),
            Paragraph(interpretation, styles["BodySmall"]),
        ])

    if len(assessment_rows) == 1:
        assessment_rows.append([
            "No sessions recorded", "0", "0%", str(int(patient[7] or 1)),
            Paragraph("No cognitive sessions are available yet.", styles["BodySmall"])
        ])

    assessment_table = Table(
        assessment_rows,
        colWidths=[54 * mm, 20 * mm, 25 * mm, 25 * mm, 51 * mm],
        repeatRows=1,
    )
    assessment_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), REPORT_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, REPORT_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 1), (3, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(assessment_table)

    # Section 3 - reminders/care schedule. We use reminders rather than claiming medications.
    story.append(Spacer(1, 5 * mm))
    story.append(section_title(3, "REMINDER & CARE SCHEDULE"))
    reminder_rows = [[
        Paragraph("<b>Time</b>", styles["BodySmall"]),
        Paragraph("<b>Reminder</b>", styles["BodySmall"]),
        Paragraph("<b>Status</b>", styles["BodySmall"]),
    ]]
    for title, due_time, status in reminders:
        reminder_rows.append([
            safe_pdf_text(due_time),
            Paragraph(safe_pdf_text(title), styles["BodySmall"]),
            safe_pdf_text(status),
        ])
    if len(reminder_rows) == 1:
        reminder_rows.append([
            "-",
            Paragraph("No reminders scheduled.", styles["BodySmall"]),
            "-",
        ])
    reminder_table = Table(reminder_rows, colWidths=[32 * mm, 92 * mm, 51 * mm], repeatRows=1)
    reminder_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), REPORT_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, REPORT_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(reminder_table)

    story.append(PageBreak())

    # Section 4 - full session audit.
    story.append(section_title(4, "GAME-BY-GAME SESSION AUDIT LOG"))
    audit_rows = [[
        Paragraph("#", styles["BodySmall"]),
        Paragraph("Date & Time", styles["BodySmall"]),
        Paragraph("Cognitive Assessment", styles["BodySmall"]),
        Paragraph("Difficulty", styles["BodySmall"]),
        Paragraph("Score", styles["BodySmall"]),
        Paragraph("Status", styles["BodySmall"]),
    ]]
    for idx, (game, score, diff, created_at) in enumerate(sessions, start=1):
        status = "Optimal" if float(score) >= 70 else "Attention"
        audit_rows.append([
            str(idx),
            safe_pdf_text(created_at),
            Paragraph(safe_pdf_text(game), styles["BodySmall"]),
            str(int(diff or 1)),
            f"{float(score):.0f}/100",
            status,
        ])
    if len(audit_rows) == 1:
        audit_rows.append(["-", "-", "No sessions recorded", "-", "-", "-"])

    audit_table = Table(
        audit_rows,
        colWidths=[9 * mm, 34 * mm, 62 * mm, 21 * mm, 23 * mm, 26 * mm],
        repeatRows=1,
    )
    audit_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), REPORT_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, REPORT_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (3, 1), (5, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(audit_table)

    # Section 5 - automatically generated observation.
    story.append(Spacer(1, 5 * mm))
    story.append(section_title(5, "DOCTOR OBSERVATION"))

    observation_header = Table([
        [
            Paragraph("<b>Source</b>", styles["BodySmall"]),
            Paragraph("Automatically generated from recorded app performance", styles["BodySmall"]),
            Paragraph("Date", styles["BodySmall"]),
            Paragraph(safe_pdf_text(doctor_observation["date"]), styles["BodySmall"]),
        ],
        [
            Paragraph("<b>Status</b>", styles["BodySmall"]),
            Paragraph("Auto-generated", styles["BodySmall"]),
            Paragraph("Doctor", styles["BodySmall"]),
            Paragraph(safe_pdf_text(doctor_observation["doctor"]), styles["BodySmall"]),
        ],
    ], colWidths=[28 * mm, 70 * mm, 25 * mm, 52 * mm])
    observation_header.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, REPORT_BORDER),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F5F8FA")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F5F8FA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(observation_header)
    story.append(Spacer(1, 3 * mm))

    observation_box = Table([
        [Paragraph(
            safe_pdf_text(doctor_observation["text"]).replace("\n", "<br/>") ,
            styles["BodySmall"]
        )]
    ], colWidths=[175 * mm])
    observation_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.6, REPORT_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(observation_box)

    # Show the real doctor's latest report automatically when it exists.
    if latest_doctor_report:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(
            "<b>Latest Doctor-Submitted Note</b>",
            styles["BodySmall"]
        ))
        submitted_note = Table([[Paragraph(
            safe_pdf_text(latest_doctor_report[1]).replace("\n", "<br/>") ,
            styles["BodySmall"]
        )]], colWidths=[175 * mm])
        submitted_note.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF9E8")),
            ("BOX", (0, 0), (-1, -1), 0.5, REPORT_BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(submitted_note)

    story.append(Spacer(1, 5 * mm))
    story.append(section_title(6, "PERFORMANCE SUMMARY & APP GUIDANCE"))

    if total_sessions:
        guidance = (
            f"The application recorded {total_sessions} cognitive session(s) with a mean score of "
            f"{mean_accuracy:.1f}/100 and a best score of {best_score:.0f}/100. "
            f"The current adaptive difficulty is level {int(patient[7] or 1)}. "
            "Continue structured cognitive practice and use reminders as configured in the app."
        )
    else:
        guidance = (
            "No cognitive sessions have been recorded yet. Start a cognitive game to begin "
            "building the longitudinal performance history."
        )

    guidance_table = Table([
        [Paragraph(guidance, styles["BodySmall"])]
    ], colWidths=[175 * mm])
    guidance_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, REPORT_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(guidance_table)

    story.append(Spacer(1, 7 * mm))
    footer_table = Table([
        [
            Paragraph("SMRITISETU", styles["BodySmall"]),
            Paragraph(
                "Generated from application data. For demonstration and educational purposes only. "
                "This report does not provide a medical diagnosis.",
                styles["Small"]
            ),
        ]
    ], colWidths=[40 * mm, 135 * mm])
    footer_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, REPORT_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(footer_table)

    def draw_page(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(colors.HexColor("#718096"))
        canvas.drawString(16 * mm, 8 * mm, "SMRITISETU | Cognitive Progress Report")
        canvas.drawRightString(194 * mm, 8 * mm, f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    buffer.seek(0)
    return buffer.getvalue()

# ============================================================
# DATABASE
# ============================================================
# DATABASE - SUPABASE POSTGRESQL (PRODUCTION / FAIL-CLOSED)
# ============================================================
#
# IMPORTANT:
#   Production data MUST live in Supabase/PostgreSQL.
#   The app no longer silently switches to SQLite when PostgreSQL is
#   unavailable. A silent fallback can make existing accounts appear to
#   disappear after a Streamlit Cloud restart because local file storage
#   is not a reliable production database.
#
# Streamlit Cloud secret (recommended):
#   [connections.postgresql]
#   url = "postgresql://..."
#
# Or one of:
#   SUPABASE_POOLER_URL
#   SUPABASE_DB_URL
#   DATABASE_URL
#
# LOCAL DEVELOPMENT ONLY:
#   Set ALLOW_SQLITE_FALLBACK=true in Streamlit Secrets or
#   SMRITISETU_ALLOW_SQLITE=1 in the environment if you explicitly want
#   a local SQLite database. This is intentionally OFF by default.
# ============================================================


# Local SQLite remains available only when explicitly enabled for local
# development/testing. It is never an automatic production fallback.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_NAME = str(DATA_DIR / "mindsetu_ner.db")

DB_BACKEND = "Unknown"
DB_SOURCE = ""


class PostgreSQLConnection:
    """Compatibility wrapper for the existing SMRITISETU SQL code."""

    def __init__(self, url, source_name="PostgreSQL"):
        self.url = url
        self.source_name = source_name
        self.connection = None
        self._connect()

    def _connect(self):
        self.connection = psycopg2.connect(
            self.url,
            connect_timeout=20,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            application_name="SMRITISETU",
        )
        self.connection.autocommit = False

    def _reconnect(self):
        try:
            if self.connection and not self.connection.closed:
                self.connection.close()
        except Exception:
            pass
        self._connect()

    @staticmethod
    def _convert_placeholders(sql):
        return sql.replace("?", "%s")

    def execute(self, sql, params=None):
        if self.connection is None or self.connection.closed:
            self._reconnect()

        cursor = self.connection.cursor()
        try:
            cursor.execute(self._convert_placeholders(sql), params or ())
            return cursor
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            # The connection may have gone stale between Streamlit reruns.
            # Reconnect once, then retry the same read/write statement.
            try:
                self.connection.rollback()
            except Exception:
                pass
            self._reconnect()
            cursor = self.connection.cursor()
            cursor.execute(self._convert_placeholders(sql), params or ())
            return cursor

    def commit(self):
        try:
            self.connection.commit()
        except (psycopg2.InterfaceError, psycopg2.OperationalError) as exc:
            raise RuntimeError(
                "The Supabase/PostgreSQL connection was lost while saving data. "
                "No automatic SQLite fallback was used. Please retry after the database connection is restored."
            ) from exc

    def rollback(self):
        try:
            self.connection.rollback()
        except Exception:
            pass

    def close(self):
        try:
            if self.connection and not self.connection.closed:
                self.connection.close()
        except Exception:
            pass


def _secret_bool(name, default=False):
    """Read a boolean from Streamlit Secrets/environment without exposing it."""
    raw = None
    try:
        raw = st.secrets.get(name)
    except Exception:
        raw = None

    if raw is None:
        raw = os.getenv(name)

    if raw is None:
        return default

    if isinstance(raw, bool):
        return raw

    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


ALLOW_SQLITE_FALLBACK = _secret_bool("ALLOW_SQLITE_FALLBACK", False)
if not ALLOW_SQLITE_FALLBACK:
    ALLOW_SQLITE_FALLBACK = _secret_bool("SMRITISETU_ALLOW_SQLITE", False)


def _read_database_urls():
    """Read PostgreSQL URLs from Streamlit Secrets without exposing them."""
    urls = []

    try:
        value = st.secrets["connections"]["postgresql"]["url"]
        if value:
            urls.append(("connections.postgresql.url", str(value).strip()))
    except Exception:
        pass

    for key in ("SUPABASE_POOLER_URL", "SUPABASE_DB_URL", "DATABASE_URL"):
        try:
            value = st.secrets[key]
            if value:
                urls.append((key, str(value).strip()))
        except Exception:
            pass

    unique = []
    seen = set()
    for name, value in urls:
        if value and value not in seen:
            unique.append((name, value))
            seen.add(value)

    # Prefer the explicitly configured Supabase Session Pooler URL because it
    # is designed for persistent application backends and IPv4 environments.
    explicit_pooler = [item for item in unique if item[0] == "SUPABASE_POOLER_URL"]
    if explicit_pooler:
        others = [item for item in unique if item[0] != "SUPABASE_POOLER_URL"]
        unique = explicit_pooler + others

    return unique


def _prepare_postgres_url(url):
    """Ensure SSL is enabled without printing or modifying credentials."""
    url = str(url).strip()
    if not url:
        return url
    if "sslmode=" not in url.lower():
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sslmode=require"
    return url


def _get_sqlite_connection():
    """Create the legacy local SQLite database for explicit local development only."""
    connection = sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )

    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA temp_store = MEMORY")

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
            adaptive_difficulty INTEGER DEFAULT 1,
            caretaker_id INTEGER,
            doctor_id_for_caretaker INTEGER,
            date_of_birth TEXT DEFAULT '',
            age INTEGER DEFAULT 0,
            photo BLOB,
            id_card_number TEXT DEFAULT '',
            id_card_created_at TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            location TEXT DEFAULT '',
            qualification TEXT DEFAULT '',
            qualification_number TEXT DEFAULT '',
            qualification_document TEXT DEFAULT '',
            qualification_status TEXT DEFAULT 'Not Required',
            account_status TEXT DEFAULT 'Active',
            created_by_id INTEGER,
            created_at TEXT DEFAULT ''
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

    connection.execute("""
        CREATE TABLE IF NOT EXISTS treatment_certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            certificate_no TEXT UNIQUE NOT NULL,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            caretaker_id INTEGER,
            treatment_title TEXT NOT NULL,
            treatment_summary TEXT NOT NULL,
            treatment_start TEXT NOT NULL,
            treatment_end TEXT NOT NULL,
            issued_at TEXT NOT NULL
        )
    """)

    existing_columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(users)").fetchall()
    }

    required_columns = {
        "adaptive_difficulty": "INTEGER DEFAULT 1",
        "caretaker_id": "INTEGER",
        "doctor_id_for_caretaker": "INTEGER",
        "date_of_birth": "TEXT DEFAULT ''",
        "age": "INTEGER DEFAULT 0",
        "photo": "BLOB",
        "id_card_number": "TEXT DEFAULT ''",
        "id_card_created_at": "TEXT DEFAULT ''",
        "phone": "TEXT DEFAULT ''",
        "email": "TEXT DEFAULT ''",
        "location": "TEXT DEFAULT ''",
        "qualification": "TEXT DEFAULT ''",
        "qualification_number": "TEXT DEFAULT ''",
        "qualification_document": "TEXT DEFAULT ''",
        "qualification_status": "TEXT DEFAULT 'Not Required'",
        "account_status": "TEXT DEFAULT 'Active'",
        "created_by_id": "INTEGER",
        "created_at": "TEXT DEFAULT ''",
    }

    for column_name, column_definition in required_columns.items():
        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE users ADD COLUMN {column_name} {column_definition}"
            )

    connection.execute("""
        UPDATE users
        SET account_status='Active'
        WHERE account_status IS NULL OR TRIM(account_status)=''
    """)

    connection.execute("""
        UPDATE users
        SET qualification_status='Not Required'
        WHERE qualification_status IS NULL OR TRIM(qualification_status)=''
    """)

    connection.execute("""
        UPDATE users
        SET created_at=datetime('now')
        WHERE created_at IS NULL OR TRIM(created_at)=''
    """)

    connection.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_users_doctor_id ON users(doctor_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_users_caretaker_id ON users(caretaker_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_reports_patient_id ON reports(patient_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_reports_doctor_id ON reports(doctor_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_cert_patient_id ON treatment_certificates(patient_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_cert_doctor_id ON treatment_certificates(doctor_id)")

    connection.commit()
    return connection


@st.cache_resource
def get_connection():
    """Return Supabase/PostgreSQL; only use SQLite when explicitly enabled."""
    global DB_BACKEND, DB_SOURCE

    urls = _read_database_urls()
    errors = []

    # 1) Production path: PostgreSQL/Supabase only.
    for source_name, raw_url in urls:
        url = _prepare_postgres_url(raw_url)
        try:
            connection = PostgreSQLConnection(url, source_name=source_name)
            connection.execute("SELECT 1").fetchone()
            connection = _initialize_postgres_schema(connection)
            DB_BACKEND = "PostgreSQL / Supabase"
            DB_SOURCE = source_name
            return connection
        except psycopg2.OperationalError as exc:
            message = str(exc).splitlines()[0] if str(exc) else "connection failed"
            errors.append(f"{source_name}: {message}")
        except Exception as exc:
            message = str(exc).splitlines()[0] if str(exc) else "database initialization failed"
            errors.append(f"{source_name}: {message}")

    # 2) SQLite is now opt-in only. Never silently switch databases.
    if ALLOW_SQLITE_FALLBACK:
        try:
            connection = _get_sqlite_connection()
            DB_BACKEND = "SQLite (LOCAL DEVELOPMENT ONLY)"
            DB_SOURCE = DB_NAME
            return connection
        except Exception as sqlite_exc:
            errors.append(f"SQLite: {str(sqlite_exc).splitlines()[0] if str(sqlite_exc) else 'initialization failed'}")

    if urls:
        detail = " | ".join(errors[-3:])
        raise RuntimeError(
            "SMRITISETU could not connect to Supabase/PostgreSQL. "
            "The app has stopped instead of switching to a new SQLite database, "
            "so existing patient/doctor/caretaker data cannot silently disappear. "
            f"Connection details: {detail}"
        )

    raise RuntimeError(
        "No Supabase/PostgreSQL database secret is configured for SMRITISETU. "
        "Add connections.postgresql.url or SUPABASE_POOLER_URL in Streamlit Secrets. "
        "For local testing only, explicitly set ALLOW_SQLITE_FALLBACK=true."
    )


def _initialize_postgres_schema(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            language TEXT DEFAULT 'English',
            baseline REAL DEFAULT 0,
            role TEXT DEFAULT 'patient',
            doctor_id INTEGER,
            adaptive_difficulty INTEGER DEFAULT 1,
            caretaker_id INTEGER,
            doctor_id_for_caretaker INTEGER,
            date_of_birth TEXT DEFAULT '',
            age INTEGER DEFAULT 0,
            photo BYTEA,
            id_card_number TEXT DEFAULT '',
            id_card_created_at TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            location TEXT DEFAULT '',
            qualification TEXT DEFAULT '',
            qualification_number TEXT DEFAULT '',
            qualification_document TEXT DEFAULT '',
            qualification_status TEXT DEFAULT 'Not Required',
            account_status TEXT DEFAULT 'Active',
            created_by_id INTEGER,
            created_at TEXT DEFAULT ''
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            game TEXT NOT NULL,
            score REAL NOT NULL,
            difficulty INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            due_time TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id BIGSERIAL PRIMARY KEY,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            report_text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'Sent'
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS treatment_certificates (
            id BIGSERIAL PRIMARY KEY,
            certificate_no TEXT UNIQUE NOT NULL,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            caretaker_id INTEGER,
            treatment_title TEXT NOT NULL,
            treatment_summary TEXT NOT NULL,
            treatment_start TEXT NOT NULL,
            treatment_end TEXT NOT NULL,
            issued_at TEXT NOT NULL
        )
    """)

    existing_columns = {
        row[0]
        for row in connection.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='users'"
        ).fetchall()
    }

    required_columns = {
        "adaptive_difficulty": "INTEGER DEFAULT 1",
        "caretaker_id": "INTEGER",
        "doctor_id_for_caretaker": "INTEGER",
        "date_of_birth": "TEXT DEFAULT ''",
        "age": "INTEGER DEFAULT 0",
        "photo": "BYTEA",
        "id_card_number": "TEXT DEFAULT ''",
        "id_card_created_at": "TEXT DEFAULT ''",
        "phone": "TEXT DEFAULT ''",
        "email": "TEXT DEFAULT ''",
        "location": "TEXT DEFAULT ''",
        "qualification": "TEXT DEFAULT ''",
        "qualification_number": "TEXT DEFAULT ''",
        "qualification_document": "TEXT DEFAULT ''",
        "qualification_status": "TEXT DEFAULT 'Not Required'",
        "account_status": "TEXT DEFAULT 'Active'",
        "created_by_id": "INTEGER",
        "created_at": "TEXT DEFAULT ''",
    }

    for column_name, column_definition in required_columns.items():
        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE users ADD COLUMN {column_name} {column_definition}"
            )

    connection.execute("""
        UPDATE users
        SET account_status='Active'
        WHERE account_status IS NULL OR TRIM(account_status)=''
    """)

    connection.execute("""
        UPDATE users
        SET qualification_status='Not Required'
        WHERE qualification_status IS NULL OR TRIM(qualification_status)=''
    """)

    connection.execute("""
        UPDATE users
        SET created_at=CURRENT_TIMESTAMP
        WHERE created_at IS NULL OR TRIM(created_at)=''
    """)

    connection.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_users_doctor_id ON users(doctor_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_users_caretaker_id ON users(caretaker_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_reports_patient_id ON reports(patient_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_reports_doctor_id ON reports(doctor_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_cert_patient_id ON treatment_certificates(patient_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_cert_doctor_id ON treatment_certificates(doctor_id)")

    connection.commit()
    return connection


def database_health_check():
    """Return (True, message) when the current database connection is healthy."""
    try:
        conn.execute("SELECT 1").fetchone()
        if DB_BACKEND.startswith("PostgreSQL"):
            return True, f"Connected to {DB_BACKEND} ({DB_SOURCE})."
        return True, f"Connected to {DB_BACKEND}."
    except Exception as exc:
        return False, "Database health check failed. No database switch will be attempted."


try:
    conn = get_connection()
except RuntimeError as db_exc:
    st.error("🔴 SMRITISETU database is unavailable.")
    st.warning(str(db_exc))
    st.info(
        "For Streamlit Cloud, configure the Supabase Session Pooler URL in "
        "App Settings → Secrets, then restart the app. Existing data is not replaced by SQLite."
    )
    st.stop()


# ============================================================
# PROVIDER / PATIENT SECURITY HELPERS
# ============================================================

def email_is_valid(email):
    if not email:
        return False
    return re.match(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
        email.strip()
    ) is not None


def phone_is_valid(phone):
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return 10 <= len(digits) <= 15


def normalize_location(location):
    return " ".join((location or "").strip().split())


def calculate_age_from_dob(dob_value):
    """Return age in completed years from a date/datetime/date string."""
    if not dob_value:
        return 0
    try:
        if isinstance(dob_value, datetime):
            born = dob_value.date()
        elif isinstance(dob_value, date):
            born = dob_value
        else:
            born = datetime.fromisoformat(str(dob_value)).date()
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    except Exception:
        return 0


def make_id_card_pdf(person_id, role_name):
    """Create a compact one-page SMRITISETU ID card with the uploaded photo embedded."""
    row = conn.execute(
        """SELECT id, name, username, role, qualification, qualification_number,
                  phone, email, location, age, photo, id_card_number
           FROM users WHERE id=? AND role=?""",
        (person_id, role_name)
    ).fetchone()
    if not row:
        return None

    card_no = row[11] or f"MNE-{role_name[:3].upper()}-{row[0]:05d}"

    # ID-card size: 90 mm x 55 mm, kept to a single PDF page.
    card_w = 90 * mm
    card_h = 55 * mm
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(card_w, card_h))

    # Card background and border.
    c.setFillColor(colors.white)
    c.roundRect(2*mm, 2*mm, card_w-4*mm, card_h-4*mm, 3*mm, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#1F4E79"))
    c.setLineWidth(1.2)
    c.roundRect(2*mm, 2*mm, card_w-4*mm, card_h-4*mm, 3*mm, fill=0, stroke=1)

    # Header.
    c.setFillColor(colors.HexColor("#1F4E79"))
    c.roundRect(2*mm, card_h-14*mm, card_w-4*mm, 12*mm, 3*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(7*mm, card_h-8*mm, "SMRITISETU")
    c.setFont("Helvetica-Bold", 7.5)
    c.drawRightString(card_w-7*mm, card_h-8*mm, f"{role_name.title()} ID CARD")

    # Photo area on the right.
    photo_x = card_w - 34*mm
    photo_y = 13*mm
    photo_w = 25*mm
    photo_h = 30*mm
    c.setStrokeColor(colors.HexColor("#1F4E79"))
    c.setLineWidth(0.8)
    c.rect(photo_x, photo_y, photo_w, photo_h, fill=0, stroke=1)

    photo_bytes = row[10]
    if photo_bytes:
        try:
            if isinstance(photo_bytes, memoryview):
                photo_bytes = photo_bytes.tobytes()
            elif isinstance(photo_bytes, bytearray):
                photo_bytes = bytes(photo_bytes)
            elif isinstance(photo_bytes, str):
                # Backward compatibility if an older record contains base64 text.
                try:
                    photo_bytes = base64.b64decode(photo_bytes)
                except Exception:
                    photo_bytes = None

            if photo_bytes:
                # Crop/resize to the ID-card photo frame while preserving aspect ratio.
                img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
                target_ratio = photo_w / photo_h
                img_ratio = img.width / img.height
                if img_ratio > target_ratio:
                    new_w = int(img.height * target_ratio)
                    left = max(0, (img.width - new_w) // 2)
                    img = img.crop((left, 0, left + new_w, img.height))
                else:
                    new_h = int(img.width / target_ratio)
                    top = max(0, (img.height - new_h) // 2)
                    img = img.crop((0, top, img.width, top + new_h))
                img = img.resize((500, 600), Image.LANCZOS)
                photo_buf = io.BytesIO()
                img.save(photo_buf, format="JPEG", quality=92)
                photo_buf.seek(0)
                c.drawImage(
                    ImageReader(photo_buf),
                    photo_x, photo_y,
                    width=photo_w,
                    height=photo_h,
                    preserveAspectRatio=False,
                    mask="auto"
                )
        except Exception:
            # Keep a clean placeholder if an old/corrupt photo cannot be decoded.
            pass

    # Photo placeholder only when the image could not be rendered.
    if not photo_bytes:
        c.setFillColor(colors.HexColor("#F2F4F7"))
        c.rect(photo_x+0.5*mm, photo_y+0.5*mm, photo_w-mm, photo_h-mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#666666"))
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(photo_x + photo_w/2, photo_y + photo_h/2 + 2*mm, "PHOTO")
        c.drawCentredString(photo_x + photo_w/2, photo_y + photo_h/2 - 2*mm, "NOT UPLOADED")

    # Details on the left.
    left_x = 7*mm
    value_x = 29*mm
    detail_y = card_h - 19*mm
    line_gap = 5.1*mm

    details = [
        ("Name", safe_pdf_text(row[1] or "N/A")),
        ("ID", safe_pdf_text(card_no)),
        ("Age", str(row[9] or "N/A")),
        ("Qualification", safe_pdf_text(row[4] or "N/A")),
        ("Reg. No.", safe_pdf_text(row[5] or "N/A")),
        ("Phone", safe_pdf_text(row[6] or "N/A")),
    ]

    c.setFillColor(colors.HexColor("#222222"))
    for label, value in details:
        c.setFont("Helvetica-Bold", 6.8)
        c.drawString(left_x, detail_y, f"{label}:")
        c.setFont("Helvetica", 6.8)
        # Keep long values inside the left-side area before the photo.
        max_chars = 29 if label not in ("Qualification",) else 24
        if len(value) > max_chars:
            value = value[:max_chars-3] + "..."
        c.drawString(value_x, detail_y, value)
        detail_y -= line_gap

    # Footer.
    c.setStrokeColor(colors.HexColor("#D0D7DE"))
    c.setLineWidth(0.5)
    c.line(7*mm, 8.5*mm, card_w-7*mm, 8.5*mm)
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica", 5.8)
    c.drawString(7*mm, 5.2*mm, "Authorized SMRITISETU Identity Card")
    c.drawRightString(card_w-7*mm, 5.2*mm, "smritisetu")

    c.showPage()
    c.save()
    return buf.getvalue()


def make_treatment_certificate_pdf(certificate_id):
    cert = conn.execute(
        """SELECT tc.certificate_no, tc.treatment_title, tc.treatment_summary,
                  tc.treatment_start, tc.treatment_end, tc.issued_at,
                  p.name, d.name, c.name
           FROM treatment_certificates tc
           JOIN users p ON p.id=tc.patient_id
           JOIN users d ON d.id=tc.doctor_id
           LEFT JOIN users c ON c.id=tc.caretaker_id
           WHERE tc.id=?""", (certificate_id,)
    ).fetchone()
    if not cert:
        return None
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("CertTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=20, leading=24)
    body = ParagraphStyle("CertBody", parent=styles["BodyText"], fontSize=11, leading=17)
    story=[Paragraph("SMRITISETU", title), Spacer(1,8*mm),
           Paragraph("<b>MEDICAL TREATMENT CERTIFICATE</b>", title), Spacer(1,10*mm),
           Paragraph(f"This is to certify that <b>{safe_pdf_text(cert[6])}</b> has completed the treatment/care described below.", body),
           Spacer(1,5*mm),
           Paragraph(f"<b>Certificate No:</b> {safe_pdf_text(cert[0])}", body),
           Paragraph(f"<b>Treatment:</b> {safe_pdf_text(cert[1])}", body),
           Paragraph(f"<b>Summary:</b> {safe_pdf_text(cert[2]).replace(chr(10), '<br/>')}", body),
           Paragraph(f"<b>Treatment Period:</b> {safe_pdf_text(cert[3])} to {safe_pdf_text(cert[4])}", body),
           Paragraph(f"<b>Doctor:</b> Dr. {safe_pdf_text(cert[7])}", body),
           Paragraph(f"<b>Caretaker/Nurse:</b> {safe_pdf_text(cert[8] or 'Not assigned')}", body),
           Spacer(1,12*mm), Paragraph(f"<b>Issued:</b> {safe_pdf_text(cert[5])}", body),
           Spacer(1,10*mm), Paragraph("This certificate is generated by the SMRITISETU application and should be verified with the treating institution when required.", styles["Italic"])]
    doc.build(story)
    return buf.getvalue()


def provider_can_manage_patient(provider_id, provider_role, patient_id):
    """Server-side ownership check for patient privacy."""
    if provider_role == "doctor":
        row = conn.execute(
            """
            SELECT id
            FROM users
            WHERE id=?
            AND role='patient'
            AND doctor_id=?
            """,
            (patient_id, provider_id)
        ).fetchone()
        return row is not None

    if provider_role == "caretaker":
        row = conn.execute(
            """
            SELECT id
            FROM users
            WHERE id=?
            AND role='patient'
            AND caretaker_id=?
            """,
            (patient_id, provider_id)
        ).fetchone()
        return row is not None

    return False


def provider_display_name(provider_row):
    if not provider_row:
        return "Not assigned"
    role = provider_row[1]
    prefix = "Dr. " if role == "doctor" else "Caretaker: "
    return prefix + provider_row[0]

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
    },

    # North-East India regional language options.
    # Bodo, Khasi, Mizo and Meitei use Indian English as a
    # voice fallback where a dedicated voice is unavailable.
    "Assamese": {
        "code": "as",
        "speech": "as-IN"
    },

    "Bodo": {
        "code": "en",
        "speech": "en-IN"
    },

    "Khasi": {
        "code": "en",
        "speech": "en-IN"
    },

    "Mizo": {
        "code": "en",
        "speech": "en-IN"
    },

    "Meitei (Manipuri)": {
        "code": "en",
        "speech": "en-IN"
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
# SIMPLE, LANGUAGE-AWARE USER INSTRUCTIONS
# ============================================================
# These instructions are shown at the point where the user needs them.
# The language is selected before login and stored with each user account.
INSTRUCTION_TRANSLATIONS = {'English': {'login': 'Enter your username and password, then press Login. New patients, doctors, and caretakers '
                      'should use the matching Registration tab first.',
             'patient_registration': 'Enter your basic details, create a username and password, choose your language, '
                                     'and press Create Patient Account. Remember your username and password for login.',
             'provider_registration': 'Enter your personal and professional details, upload the requested '
                                      'qualification information/document, choose your language, and submit. Provider '
                                      'accounts may wait for administrator verification.',
             'home': 'Read the dashboard to see your current status. Use the menu to open games, reminders, history, '
                     'details, or reports.',
             'games': 'Choose one game. Read its instructions before starting. Complete the rounds carefully. You may '
                      'exit an unfinished game at any time. Your completed score is saved.',
             'memory': 'Watch the numbers carefully for 10 seconds. When they disappear, enter the numbers in the same '
                       'order and submit.',
             'pattern': 'Watch the pattern carefully. After it is hidden, reproduce the pattern as instructed and '
                        'submit your answer.',
             'attention': 'Watch the screen and respond to the target when it appears. Follow the on-screen '
                          'instruction and complete each round.',
             'image': 'Look at the pictures during the viewing countdown. Wait until the countdown finishes, then '
                      'choose the correct answer.',
             'schulte': 'Find the numbers in order, starting from 1. Tap them in sequence as quickly and accurately as '
                        'you can.',
             'spot': 'Look at both sides carefully. Find the different item and select it as instructed.',
             'hidden': 'Look at the picture and find the hidden target objects. Tap each target you can find.',
             'target': 'A target appears in the grid for a short time. Tap the target before it disappears. Do not tap '
                       'other cells.',
             'reminders': 'Add a reminder with a title and time. Check your reminders regularly and delete reminders '
                          'you no longer need.',
             'history': 'Review your previous game scores and performance. Use the history to see your progress over '
                        'time.',
             'details': 'Check your profile information, language, assigned provider, and other saved details.',
             'reports': 'Open available reports to review your recorded performance. Patients can listen to reports '
                        'when voice output is available.'},
 'Hindi': {'login': 'अपना यूज़रनेम और पासवर्ड डालें और लॉगिन दबाएँ। नया खाता बनाने के लिए सही रजिस्ट्रेशन टैब चुनें।',
           'patient_registration': 'अपनी जानकारी भरें, यूज़रनेम और पासवर्ड बनाएँ, भाषा चुनें और खाता बनाएँ दबाएँ। '
                                   'लॉगिन के लिए यूज़रनेम और पासवर्ड याद रखें।',
           'provider_registration': 'अपनी व्यक्तिगत और पेशेवर जानकारी भरें, मांगी गई योग्यता की जानकारी/दस्तावेज़ दें, '
                                    'भाषा चुनें और सबमिट करें। सत्यापन के लिए एडमिन की मंज़ूरी लग सकती है।',
           'home': 'डैशबोर्ड पर अपनी स्थिति देखें। गेम, रिमाइंडर, इतिहास, जानकारी और रिपोर्ट खोलने के लिए मेनू का '
                   'उपयोग करें।',
           'games': 'एक गेम चुनें और शुरू करने से पहले निर्देश पढ़ें। सभी राउंड ध्यान से पूरा करें। अधूरा गेम कभी भी '
                    'बाहर निकलकर छोड़ सकते हैं। पूरा स्कोर सेव होगा।',
           'memory': '10 सेकंड तक नंबर ध्यान से देखें। नंबर छिपने के बाद उसी क्रम में नंबर लिखें और सबमिट करें।',
           'pattern': 'पैटर्न ध्यान से देखें। छिपने के बाद दिए गए निर्देश के अनुसार पैटर्न दोबारा बनाएँ और सबमिट करें।',
           'attention': 'स्क्रीन देखें और लक्ष्य दिखाई देने पर निर्देश के अनुसार प्रतिक्रिया दें। हर राउंड पूरा करें।',
           'image': 'काउंटडाउन के दौरान चित्र देखें। काउंटडाउन खत्म होने के बाद सही उत्तर चुनें।',
           'schulte': '1 से शुरू करके नंबर क्रम में खोजें। नंबरों को सही क्रम में जल्दी और ध्यान से दबाएँ।',
           'spot': 'दोनों तरफ ध्यान से देखें। अलग वस्तु खोजें और निर्देश के अनुसार उसे चुनें।',
           'hidden': 'चित्र में छिपी हुई वस्तुओं को खोजें। जो लक्ष्य मिले उस पर टैप करें।',
           'target': 'ग्रिड में लक्ष्य थोड़े समय के लिए दिखाई देगा। गायब होने से पहले लक्ष्य पर टैप करें। दूसरे खाने '
                     'पर टैप न करें।',
           'reminders': 'नाम और समय देकर रिमाइंडर जोड़ें। अपने रिमाइंडर नियमित रूप से देखें और पुराने रिमाइंडर हटाएँ।',
           'history': 'अपने पुराने गेम स्कोर और प्रदर्शन देखें। समय के साथ अपनी प्रगति समझने के लिए इतिहास देखें।',
           'details': 'अपनी प्रोफ़ाइल, भाषा, जुड़े हुए डॉक्टर/केयरटेकर और अन्य जानकारी देखें।',
           'reports': 'उपलब्ध रिपोर्ट खोलकर अपना रिकॉर्ड किया हुआ प्रदर्शन देखें। आवाज़ उपलब्ध होने पर मरीज रिपोर्ट '
                      'सुन सकते हैं।'},
 'Marathi': {'login': 'तुमचे यूजरनेम आणि पासवर्ड टाका आणि लॉगिन दाबा. नवीन खातेासाठी योग्य रजिस्ट्रेशन टॅब निवडा.',
             'patient_registration': 'तुमची माहिती भरा, यूजरनेम आणि पासवर्ड तयार करा, भाषा निवडा आणि खाते तयार करा '
                                     'दाबा. लॉगिनसाठी माहिती लक्षात ठेवा.',
             'provider_registration': 'तुमची वैयक्तिक व व्यावसायिक माहिती भरा, मागितलेली पात्रता माहिती/कागदपत्र द्या, '
                                      'भाषा निवडा आणि सबमिट करा. पडताळणीसाठी प्रशासकाची मंजुरी लागू शकते.',
             'home': 'डॅशबोर्डवर तुमची स्थिती पहा. गेम, स्मरणपत्रे, इतिहास, माहिती आणि अहवाल उघडण्यासाठी मेनू वापरा.',
             'games': 'एक गेम निवडा आणि सुरू करण्यापूर्वी सूचना वाचा. सर्व राउंड काळजीपूर्वक पूर्ण करा. अपूर्ण गेम '
                      'कधीही बाहेर पडून थांबवू शकता. पूर्ण स्कोअर सेव्ह होईल.',
             'memory': '10 सेकंद नंबर काळजीपूर्वक पहा. नंबर लपल्यानंतर त्याच क्रमाने नंबर लिहा आणि सबमिट करा.',
             'pattern': 'पॅटर्न काळजीपूर्वक पहा. तो लपल्यानंतर दिलेल्या सूचनेनुसार पुन्हा तयार करा आणि सबमिट करा.',
             'attention': 'स्क्रीनकडे लक्ष द्या आणि लक्ष्य दिसल्यावर सूचनेनुसार प्रतिक्रिया द्या. प्रत्येक राउंड पूर्ण '
                          'करा.',
             'image': 'काउंटडाउन चालू असताना चित्रे पहा. काउंटडाउन संपल्यावर योग्य उत्तर निवडा.',
             'schulte': '1 पासून नंबर क्रमाने शोधा. योग्य क्रमाने नंबर शक्य तितक्या जलद आणि अचूकपणे दाबा.',
             'spot': 'दोन्ही बाजू काळजीपूर्वक पहा. वेगळी वस्तू शोधा आणि सूचनेनुसार निवडा.',
             'hidden': 'चित्रातील लपलेल्या वस्तू शोधा. सापडलेल्या लक्ष्यावर टॅप करा.',
             'target': 'ग्रिडमध्ये लक्ष्य थोड्या वेळासाठी दिसेल. ते गायब होण्यापूर्वी टॅप करा. इतर खाण्यांवर टॅप करू '
                       'नका.',
             'reminders': 'नाव आणि वेळ देऊन स्मरणपत्र जोडा. स्मरणपत्रे नियमित तपासा आणि गरज नसलेली हटवा.',
             'history': 'जुने गेम स्कोअर आणि कामगिरी पहा. वेळेनुसार प्रगती समजण्यासाठी इतिहास वापरा.',
             'details': 'तुमची प्रोफाइल, भाषा, जोडलेले डॉक्टर/केअरटेकर आणि इतर माहिती तपासा.',
             'reports': 'उपलब्ध अहवाल उघडून तुमची नोंदवलेली कामगिरी पहा. आवाज उपलब्ध असल्यास रुग्ण अहवाल ऐकू शकतात.'},
 'Gujarati': {'login': 'તમારું યુઝરનેમ અને પાસવર્ડ દાખલ કરો અને Login દબાવો. નવું એકાઉન્ટ બનાવવા યોગ્ય Registration '
                       'ટેબ પસંદ કરો.',
              'patient_registration': 'તમારી માહિતી ભરો, યુઝરનેમ અને પાસવર્ડ બનાવો, ભાષા પસંદ કરો અને Create Account '
                                      'દબાવો. Login માટે વિગતો યાદ રાખો.',
              'provider_registration': 'વ્યક્તિગત અને વ્યવસાયિક માહિતી ભરો, જરૂરી લાયકાતની માહિતી/દસ્તાવેજ આપો, ભાષા '
                                       'પસંદ કરો અને Submit કરો. ચકાસણી માટે એડમિનની મંજૂરી લાગી શકે છે.',
              'home': 'ડેશબોર્ડ પર તમારી સ્થિતિ જુઓ. ગેમ, રિમાઇન્ડર, ઇતિહાસ, વિગતો અને રિપોર્ટ ખોલવા મેનૂનો ઉપયોગ કરો.',
              'games': 'એક ગેમ પસંદ કરો અને શરૂ કરતા પહેલા સૂચનાઓ વાંચો. બધા રાઉન્ડ ધ્યાનથી પૂર્ણ કરો. અધૂરી ગેમમાંથી '
                       'કોઈપણ સમયે બહાર નીકળી શકો છો. પૂર્ણ સ્કોર સેવ થશે.',
              'memory': '10 સેકન્ડ સુધી નંબર ધ્યાનથી જુઓ. નંબર છુપાયા પછી એ જ ક્રમમાં નંબર દાખલ કરો અને Submit કરો.',
              'pattern': 'પેટર્ન ધ્યાનથી જુઓ. તે છુપાયા પછી સૂચના મુજબ પેટર્ન ફરી બનાવો અને Submit કરો.',
              'attention': 'સ્ક્રીન જુઓ અને લક્ષ્ય દેખાય ત્યારે સૂચના મુજબ પ્રતિસાદ આપો. દરેક રાઉન્ડ પૂર્ણ કરો.',
              'image': 'કાઉન્ટડાઉન દરમિયાન ચિત્રો જુઓ. કાઉન્ટડાઉન પૂરો થયા પછી સાચો જવાબ પસંદ કરો.',
              'schulte': '1 થી શરૂ કરીને નંબર ક્રમમાં શોધો. સાચા ક્રમમાં ઝડપથી અને ધ્યાનથી નંબર દબાવો.',
              'spot': 'બંને બાજુ ધ્યાનથી જુઓ. અલગ વસ્તુ શોધો અને સૂચના મુજબ પસંદ કરો.',
              'hidden': 'ચિત્રમાં છુપાયેલી વસ્તુઓ શોધો અને મળેલા લક્ષ્ય પર ટેપ કરો.',
              'target': 'ગ્રિડમાં લક્ષ્ય થોડા સમય માટે દેખાશે. તે ગાયબ થાય તે પહેલાં ટેપ કરો. બીજા ખાના પર ટેપ ન કરો.',
              'reminders': 'નામ અને સમય સાથે રિમાઇન્ડર ઉમેરો. રિમાઇન્ડર નિયમિત તપાસો અને જરૂર ન હોય તે કાઢી નાખો.',
              'history': 'તમારા જૂના ગેમ સ્કોર અને પ્રદર્શન જુઓ. સમય સાથે પ્રગતિ સમજવા માટે ઇતિહાસ જુઓ.',
              'details': 'તમારી પ્રોફાઇલ, ભાષા, જોડાયેલા ડૉક્ટર/કેરટેકર અને અન્ય માહિતી તપાસો.',
              'reports': 'ઉપલબ્ધ રિપોર્ટ ખોલીને તમારું નોંધાયેલ પ્રદર્શન જુઓ. અવાજ ઉપલબ્ધ હોય તો દર્દી રિપોર્ટ સાંભળી '
                         'શકે છે.'},
 'Tamil': {'login': 'உங்கள் பயனர்பெயர் மற்றும் கடவுச்சொல்லை உள்ளிட்டு Login அழுத்தவும். புதிய கணக்கிற்கு சரியான '
                    'Registration தாவலைத் தேர்ந்தெடுக்கவும்.',
           'patient_registration': 'உங்கள் தகவல்களை உள்ளிட்டு, பயனர்பெயர் மற்றும் கடவுச்சொல் உருவாக்கி, மொழியைத் '
                                   'தேர்ந்தெடுத்து Create Account அழுத்தவும்.',
           'provider_registration': 'தனிப்பட்ட மற்றும் தொழில்முறை தகவல்களை உள்ளிட்டு, தேவையான தகுதி தகவல்/ஆவணத்தை '
                                    'வழங்கி, மொழியைத் தேர்ந்தெடுத்து Submit செய்யவும். நிர்வாகி சரிபார்ப்பு '
                                    'தேவைப்படலாம்.',
           'home': 'டாஷ்போர்டில் உங்கள் நிலையைப் பார்க்கவும். கேம்கள், நினைவூட்டல்கள், வரலாறு, விவரங்கள் மற்றும் '
                   'அறிக்கைகளை மெனுவில் திறக்கவும்.',
           'games': 'ஒரு கேமைத் தேர்ந்தெடுத்து தொடங்குவதற்கு முன் வழிமுறைகளைப் படிக்கவும். அனைத்து சுற்றுகளையும் '
                    'கவனமாக முடிக்கவும். முடிக்காத கேமிலிருந்து எப்போது வேண்டுமானாலும் வெளியேறலாம்.',
           'memory': '10 விநாடிகள் எண்களை கவனமாகப் பார்க்கவும். எண்கள் மறைந்த பிறகு அதே வரிசையில் உள்ளிடவும்.',
           'pattern': 'வடிவத்தை கவனமாகப் பார்க்கவும். அது மறைந்த பிறகு வழிமுறையின்படி மீண்டும் உருவாக்கவும்.',
           'attention': 'திரையை கவனித்து இலக்கு தோன்றும்போது வழிமுறையின்படி பதிலளிக்கவும்.',
           'image': 'கவுண்ட்டவுன் இருக்கும் போது படங்களைப் பார்க்கவும். கவுண்ட்டவுன் முடிந்த பிறகு சரியான பதிலைத் '
                    'தேர்ந்தெடுக்கவும்.',
           'schulte': '1 முதல் தொடங்கி எண்களை வரிசையாகக் கண்டுபிடிக்கவும். சரியான வரிசையில் வேகமாகத் தட்டவும்.',
           'spot': 'இரு பக்கங்களையும் கவனமாகப் பார்க்கவும். வேறுபட்ட பொருளைக் கண்டுபிடித்து தேர்ந்தெடுக்கவும்.',
           'hidden': 'படத்தில் மறைந்துள்ள பொருட்களைக் கண்டுபிடித்து கிடைத்த இலக்கைத் தட்டவும்.',
           'target': 'கட்டத்தில் இலக்கு சிறிது நேரம் தோன்றும். மறையும் முன் அதைத் தட்டவும். மற்ற கட்டங்களைத் தட்ட '
                     'வேண்டாம்.',
           'reminders': 'பெயரும் நேரமும் கொடுத்து நினைவூட்டலைச் சேர்க்கவும். தேவையில்லாத நினைவூட்டல்களை நீக்கவும்.',
           'history': 'முந்தைய கேம் மதிப்பெண்கள் மற்றும் செயல்திறனைப் பார்க்கவும். உங்கள் முன்னேற்றத்தை அறிய '
                      'வரலாற்றைப் பயன்படுத்தவும்.',
           'details': 'உங்கள் சுயவிவரம், மொழி, இணைக்கப்பட்ட மருத்துவர்/பராமரிப்பாளர் மற்றும் பிற தகவல்களைப் '
                      'பார்க்கவும்.',
           'reports': 'கிடைக்கும் அறிக்கைகளைத் திறந்து பதிவு செய்யப்பட்ட செயல்திறனைப் பார்க்கவும். குரல் வசதி '
                      'இருந்தால் அறிக்கையை கேட்கலாம்.'},
 'Telugu': {'login': 'మీ వినియోగదారు పేరు మరియు పాస్\u200cవర్డ్ నమోదు చేసి Login నొక్కండి. కొత్త ఖాతా కోసం సరైన '
                     'Registration ట్యాబ్\u200cను ఎంచుకోండి.',
            'patient_registration': 'మీ వివరాలు నమోదు చేసి, వినియోగదారు పేరు మరియు పాస్\u200cవర్డ్ సృష్టించి, భాష '
                                    'ఎంచుకుని Create Account నొక్కండి.',
            'provider_registration': 'వ్యక్తిగత మరియు వృత్తిపరమైన వివరాలు నమోదు చేసి, అవసరమైన అర్హత సమాచారం/పత్రాన్ని '
                                     'అందించి, భాష ఎంచుకుని Submit చేయండి. అడ్మిన్ ధృవీకరణ అవసరం కావచ్చు.',
            'home': 'డ్యాష్\u200cబోర్డ్\u200cలో మీ స్థితిని చూడండి. గేమ్స్, రిమైండర్లు, చరిత్ర, వివరాలు మరియు '
                    'రిపోర్టులను మెనూ ద్వారా తెరవండి.',
            'games': 'ఒక గేమ్ ఎంచుకుని ప్రారంభించే ముందు సూచనలు చదవండి. అన్ని రౌండ్లు జాగ్రత్తగా పూర్తి చేయండి. పూర్తి '
                     'కాని గేమ్ నుంచి ఎప్పుడైనా బయటకు రావచ్చు.',
            'memory': '10 సెకన్ల పాటు సంఖ్యలను జాగ్రత్తగా చూడండి. అవి దాచిన తర్వాత అదే క్రమంలో నమోదు చేయండి.',
            'pattern': 'ప్యాటర్న్\u200cను జాగ్రత్తగా చూడండి. అది దాచిన తర్వాత సూచనల ప్రకారం మళ్లీ రూపొందించండి.',
            'attention': 'స్క్రీన్\u200cను గమనించి లక్ష్యం కనిపించినప్పుడు సూచనల ప్రకారం స్పందించండి.',
            'image': 'కౌంట్\u200cడౌన్ సమయంలో చిత్రాలను చూడండి. కౌంట్\u200cడౌన్ ముగిసిన తర్వాత సరైన సమాధానం ఎంచుకోండి.',
            'schulte': '1 నుండి ప్రారంభించి సంఖ్యలను క్రమంలో కనుగొనండి. సరైన క్రమంలో వేగంగా నొక్కండి.',
            'spot': 'రెండు వైపులా జాగ్రత్తగా చూడండి. తేడా ఉన్న వస్తువును కనుగొని ఎంచుకోండి.',
            'hidden': 'చిత్రంలో దాగి ఉన్న వస్తువులను కనుగొని కనిపించిన లక్ష్యాన్ని నొక్కండి.',
            'target': 'గ్రిడ్\u200cలో లక్ష్యం కొద్దిసేపు కనిపిస్తుంది. అది మాయమయ్యే ముందు నొక్కండి. ఇతర సెల్\u200cలను '
                      'నొక్కవద్దు.',
            'reminders': 'పేరు మరియు సమయంతో రిమైండర్ జోడించండి. అవసరం లేని రిమైండర్లను తొలగించండి.',
            'history': 'మునుపటి గేమ్ స్కోర్లు మరియు పనితీరును చూడండి. మీ పురోగతిని తెలుసుకోవడానికి చరిత్రను '
                       'ఉపయోగించండి.',
            'details': 'మీ ప్రొఫైల్, భాష, అనుసంధానమైన డాక్టర్/కేర్\u200cటేకర్ మరియు ఇతర వివరాలను చూడండి.',
            'reports': 'అందుబాటులో ఉన్న రిపోర్టులను తెరిచి నమోదైన పనితీరును చూడండి. వాయిస్ అందుబాటులో ఉంటే రిపోర్టులను '
                       'వినవచ్చు.'},
 'Bengali': {'login': 'আপনার ইউজারনেম ও পাসওয়ার্ড লিখে Login চাপুন। নতুন অ্যাকাউন্টের জন্য সঠিক Registration ট্যাব '
                      'বেছে নিন।',
             'patient_registration': 'আপনার তথ্য দিন, ইউজারনেম ও পাসওয়ার্ড তৈরি করুন, ভাষা বেছে নিয়ে Create Account '
                                     'চাপুন।',
             'provider_registration': 'ব্যক্তিগত ও পেশাগত তথ্য দিন, প্রয়োজনীয় যোগ্যতার তথ্য/নথি দিন, ভাষা বেছে '
                                      'Submit করুন। প্রশাসকের যাচাই লাগতে পারে।',
             'home': 'ড্যাশবোর্ডে আপনার অবস্থা দেখুন। গেম, রিমাইন্ডার, ইতিহাস, তথ্য ও রিপোর্ট মেনু থেকে খুলুন।',
             'games': 'একটি গেম বেছে নিয়ে শুরু করার আগে নির্দেশ পড়ুন। সব রাউন্ড মন দিয়ে শেষ করুন। অসম্পূর্ণ গেম '
                      'যেকোনো সময় বন্ধ করতে পারেন।',
             'memory': '১০ সেকেন্ড সংখ্যাগুলি মন দিয়ে দেখুন। সংখ্যা লুকিয়ে গেলে একই ক্রমে লিখে Submit করুন।',
             'pattern': 'প্যাটার্নটি মন দিয়ে দেখুন। লুকিয়ে গেলে নির্দেশ অনুযায়ী আবার তৈরি করুন।',
             'attention': 'স্ক্রিনে লক্ষ্য দেখুন এবং নির্দেশ অনুযায়ী প্রতিক্রিয়া দিন।',
             'image': 'কাউন্টডাউনের সময় ছবিগুলি দেখুন। কাউন্টডাউন শেষ হলে সঠিক উত্তর বেছে নিন।',
             'schulte': '১ থেকে শুরু করে সংখ্যাগুলি ক্রমে খুঁজুন। সঠিক ক্রমে দ্রুত চাপুন।',
             'spot': 'দুই পাশ মন দিয়ে দেখুন। আলাদা জিনিসটি খুঁজে নির্দেশ অনুযায়ী বেছে নিন।',
             'hidden': 'ছবিতে লুকানো জিনিস খুঁজুন এবং পাওয়া লক্ষ্যটিতে চাপুন।',
             'target': 'গ্রিডে লক্ষ্য অল্প সময়ের জন্য দেখা যাবে। অদৃশ্য হওয়ার আগে সেটিতে চাপুন। অন্য ঘরে চাপবেন না।',
             'reminders': 'নাম ও সময় দিয়ে রিমাইন্ডার যোগ করুন। দরকার নেই এমন রিমাইন্ডার মুছে দিন।',
             'history': 'আগের গেমের স্কোর ও পারফরম্যান্স দেখুন। সময়ের সঙ্গে অগ্রগতি বুঝতে ইতিহাস ব্যবহার করুন।',
             'details': 'আপনার প্রোফাইল, ভাষা, যুক্ত ডাক্তার/কেয়ারটেকার এবং অন্যান্য তথ্য দেখুন।',
             'reports': 'উপলব্ধ রিপোর্ট খুলে রেকর্ড করা পারফরম্যান্স দেখুন। ভয়েস সুবিধা থাকলে রিপোর্ট শুনতে পারবেন।'},
 'French': {'login': "Saisissez votre nom d'utilisateur et votre mot de passe, puis appuyez sur Connexion.",
            'games': 'Choisissez un jeu et lisez les instructions avant de commencer.',
            'memory': 'Regardez les nombres pendant 10 secondes, puis saisissez-les dans le même ordre.',
            'pattern': 'Regardez le modèle, puis reproduisez-le selon les instructions.',
            'attention': 'Surveillez la cible et répondez selon les instructions.',
            'image': 'Regardez les images pendant le compte à rebours, puis choisissez la bonne réponse.',
            'schulte': "Trouvez les nombres dans l'ordre à partir de 1.",
            'spot': "Cherchez l'objet différent et sélectionnez-le.",
            'hidden': "Trouvez les objets cachés dans l'image.",
            'target': "Touchez la cible avant qu'elle disparaisse.",
            'patient_registration': "Saisissez votre nom d'utilisateur et votre mot de passe, puis appuyez sur "
                                    'Connexion.',
            'provider_registration': "Saisissez votre nom d'utilisateur et votre mot de passe, puis appuyez sur "
                                     'Connexion.',
            'home': 'Choisissez un jeu et lisez les instructions avant de commencer.',
            'reminders': 'Choisissez un jeu et lisez les instructions avant de commencer.',
            'history': 'Choisissez un jeu et lisez les instructions avant de commencer.',
            'details': 'Choisissez un jeu et lisez les instructions avant de commencer.',
            'reports': 'Choisissez un jeu et lisez les instructions avant de commencer.'},
 'Spanish': {'login': 'Escriba su usuario y contraseña y pulse Iniciar sesión.',
             'games': 'Elija un juego y lea las instrucciones antes de comenzar.',
             'memory': 'Mire los números durante 10 segundos y después escríbalos en el mismo orden.',
             'pattern': 'Mire el patrón y repítalo según las instrucciones.',
             'attention': 'Observe la pantalla y responda cuando aparezca el objetivo.',
             'image': 'Mire las imágenes durante la cuenta atrás y después elija la respuesta correcta.',
             'schulte': 'Busque los números en orden empezando por 1.',
             'spot': 'Busque el objeto diferente y selecciónelo.',
             'hidden': 'Encuentre los objetos ocultos en la imagen.',
             'target': 'Toque el objetivo antes de que desaparezca.',
             'patient_registration': 'Escriba su usuario y contraseña y pulse Iniciar sesión.',
             'provider_registration': 'Escriba su usuario y contraseña y pulse Iniciar sesión.',
             'home': 'Elija un juego y lea las instrucciones antes de comenzar.',
             'reminders': 'Elija un juego y lea las instrucciones antes de comenzar.',
             'history': 'Elija un juego y lea las instrucciones antes de comenzar.',
             'details': 'Elija un juego y lea las instrucciones antes de comenzar.',
             'reports': 'Elija un juego y lea las instrucciones antes de comenzar.'},
 'German': {'login': 'Geben Sie Benutzername und Passwort ein und drücken Sie Anmelden.',
            'games': 'Wählen Sie ein Spiel und lesen Sie die Anleitung vor dem Start.',
            'memory': 'Merken Sie sich die Zahlen 10 Sekunden lang und geben Sie sie danach in derselben Reihenfolge '
                      'ein.',
            'pattern': 'Sehen Sie sich das Muster an und wiederholen Sie es nach der Anleitung.',
            'attention': 'Beobachten Sie den Bildschirm und reagieren Sie auf das Ziel.',
            'image': 'Sehen Sie die Bilder während des Countdowns an und wählen Sie danach die richtige Antwort.',
            'schulte': 'Finden Sie die Zahlen ab 1 in der richtigen Reihenfolge.',
            'spot': 'Finden Sie den Unterschied und wählen Sie ihn aus.',
            'hidden': 'Finden Sie die versteckten Objekte im Bild.',
            'target': 'Tippen Sie auf das Ziel, bevor es verschwindet.',
            'patient_registration': 'Geben Sie Benutzername und Passwort ein und drücken Sie Anmelden.',
            'provider_registration': 'Geben Sie Benutzername und Passwort ein und drücken Sie Anmelden.',
            'home': 'Wählen Sie ein Spiel und lesen Sie die Anleitung vor dem Start.',
            'reminders': 'Wählen Sie ein Spiel und lesen Sie die Anleitung vor dem Start.',
            'history': 'Wählen Sie ein Spiel und lesen Sie die Anleitung vor dem Start.',
            'details': 'Wählen Sie ein Spiel und lesen Sie die Anleitung vor dem Start.',
            'reports': 'Wählen Sie ein Spiel und lesen Sie die Anleitung vor dem Start.'},
 'Italian': {'login': 'Inserisci nome utente e password e premi Accedi.',
             'games': 'Scegli un gioco e leggi le istruzioni prima di iniziare.',
             'memory': 'Guarda i numeri per 10 secondi e inseriscili nello stesso ordine.',
             'pattern': 'Guarda il modello e ripetilo seguendo le istruzioni.',
             'attention': 'Osserva lo schermo e rispondi quando appare il bersaglio.',
             'image': 'Guarda le immagini durante il conto alla rovescia e poi scegli la risposta corretta.',
             'schulte': 'Trova i numeri in ordine partendo da 1.',
             'spot': "Trova l'oggetto diverso e selezionalo.",
             'hidden': "Trova gli oggetti nascosti nell'immagine.",
             'target': 'Tocca il bersaglio prima che scompaia.',
             'patient_registration': 'Inserisci nome utente e password e premi Accedi.',
             'provider_registration': 'Inserisci nome utente e password e premi Accedi.',
             'home': 'Scegli un gioco e leggi le istruzioni prima di iniziare.',
             'reminders': 'Scegli un gioco e leggi le istruzioni prima di iniziare.',
             'history': 'Scegli un gioco e leggi le istruzioni prima di iniziare.',
             'details': 'Scegli un gioco e leggi le istruzioni prima di iniziare.',
             'reports': 'Scegli un gioco e leggi le istruzioni prima di iniziare.'},
 'Portuguese': {'login': 'Digite seu nome de usuário e senha e pressione Login.',
                'games': 'Escolha um jogo e leia as instruções antes de começar.',
                'memory': 'Observe os números por 10 segundos e depois digite-os na mesma ordem.',
                'pattern': 'Observe o padrão e repita-o conforme as instruções.',
                'attention': 'Observe a tela e responda quando o alvo aparecer.',
                'image': 'Veja as imagens durante a contagem e depois escolha a resposta correta.',
                'schulte': 'Encontre os números em ordem começando pelo 1.',
                'spot': 'Encontre o objeto diferente e selecione-o.',
                'hidden': 'Encontre os objetos escondidos na imagem.',
                'target': 'Toque no alvo antes que ele desapareça.',
                'patient_registration': 'Digite seu nome de usuário e senha e pressione Login.',
                'provider_registration': 'Digite seu nome de usuário e senha e pressione Login.',
                'home': 'Escolha um jogo e leia as instruções antes de começar.',
                'reminders': 'Escolha um jogo e leia as instruções antes de começar.',
                'history': 'Escolha um jogo e leia as instruções antes de começar.',
                'details': 'Escolha um jogo e leia as instruções antes de começar.',
                'reports': 'Escolha um jogo e leia as instruções antes de começar.'},
 'Arabic': {'login': 'أدخل اسم المستخدم وكلمة المرور ثم اضغط تسجيل الدخول.',
            'games': 'اختر لعبة واقرأ التعليمات قبل البدء.',
            'memory': 'شاهد الأرقام لمدة 10 ثوانٍ ثم أدخلها بالترتيب نفسه.',
            'pattern': 'شاهد النمط ثم أعده حسب التعليمات.',
            'attention': 'راقب الشاشة واستجب عند ظهور الهدف.',
            'image': 'شاهد الصور أثناء العد التنازلي ثم اختر الإجابة الصحيحة.',
            'schulte': 'ابحث عن الأرقام بالترتيب بدءًا من 1.',
            'spot': 'ابحث عن العنصر المختلف واختره.',
            'hidden': 'ابحث عن العناصر المخفية في الصورة.',
            'target': 'اضغط على الهدف قبل أن يختفي.',
            'patient_registration': 'أدخل اسم المستخدم وكلمة المرور ثم اضغط تسجيل الدخول.',
            'provider_registration': 'أدخل اسم المستخدم وكلمة المرور ثم اضغط تسجيل الدخول.',
            'home': 'اختر لعبة واقرأ التعليمات قبل البدء.',
            'reminders': 'اختر لعبة واقرأ التعليمات قبل البدء.',
            'history': 'اختر لعبة واقرأ التعليمات قبل البدء.',
            'details': 'اختر لعبة واقرأ التعليمات قبل البدء.',
            'reports': 'اختر لعبة واقرأ التعليمات قبل البدء.'},
 'Chinese': {'login': '输入用户名和密码，然后点击登录。',
             'games': '选择一个游戏，开始前先阅读说明。',
             'memory': '观察数字10秒，数字消失后按相同顺序输入。',
             'pattern': '观察图案，然后按照说明重新完成图案。',
             'attention': '观察屏幕，目标出现时按照说明操作。',
             'image': '倒计时期间观察图片，倒计时结束后选择正确答案。',
             'schulte': '从1开始按顺序寻找数字。',
             'spot': '仔细比较两边，找到不同的项目。',
             'hidden': '在图片中寻找隐藏的目标。',
             'target': '在目标消失前点击它。',
             'patient_registration': '输入用户名和密码，然后点击登录。',
             'provider_registration': '输入用户名和密码，然后点击登录。',
             'home': '选择一个游戏，开始前先阅读说明。',
             'reminders': '选择一个游戏，开始前先阅读说明。',
             'history': '选择一个游戏，开始前先阅读说明。',
             'details': '选择一个游戏，开始前先阅读说明。',
             'reports': '选择一个游戏，开始前先阅读说明。'},
 'Japanese': {'login': 'ユーザー名とパスワードを入力してログインを押してください。',
              'games': 'ゲームを選び、開始前に説明を読んでください。',
              'memory': '10秒間数字を見て覚え、消えた後に同じ順番で入力してください。',
              'pattern': 'パターンを見て、説明どおりに再現してください。',
              'attention': '画面を見て、目標が出たら説明どおりに反応してください。',
              'image': 'カウントダウン中に画像を見て、終了後に正しい答えを選んでください。',
              'schulte': '1から順番に数字を探してください。',
              'spot': '左右を見比べて違うものを選んでください。',
              'hidden': '画像の中の隠れた対象を探してください。',
              'target': '消える前に目標をタップしてください。',
              'patient_registration': 'ユーザー名とパスワードを入力してログインを押してください。',
              'provider_registration': 'ユーザー名とパスワードを入力してログインを押してください。',
              'home': 'ゲームを選び、開始前に説明を読んでください。',
              'reminders': 'ゲームを選び、開始前に説明を読んでください。',
              'history': 'ゲームを選び、開始前に説明を読んでください。',
              'details': 'ゲームを選び、開始前に説明を読んでください。',
              'reports': 'ゲームを選び、開始前に説明を読んでください。'},
 'Korean': {'login': '사용자 이름과 비밀번호를 입력하고 로그인을 누르세요.',
            'games': '게임을 선택하고 시작하기 전에 안내를 읽으세요.',
            'memory': '10초 동안 숫자를 보고 기억한 뒤 같은 순서로 입력하세요.',
            'pattern': '패턴을 보고 안내에 따라 다시 만드세요.',
            'attention': '화면을 보고 목표가 나타나면 안내에 따라 반응하세요.',
            'image': '카운트다운 동안 이미지를 보고 끝난 후 정답을 선택하세요.',
            'schulte': '1부터 숫자를 순서대로 찾으세요.',
            'spot': '양쪽을 비교하여 다른 항목을 찾으세요.',
            'hidden': '그림에서 숨겨진 대상을 찾으세요.',
            'target': '목표가 사라지기 전에 누르세요.',
            'patient_registration': '사용자 이름과 비밀번호를 입력하고 로그인을 누르세요.',
            'provider_registration': '사용자 이름과 비밀번호를 입력하고 로그인을 누르세요.',
            'home': '게임을 선택하고 시작하기 전에 안내를 읽으세요.',
            'reminders': '게임을 선택하고 시작하기 전에 안내를 읽으세요.',
            'history': '게임을 선택하고 시작하기 전에 안내를 읽으세요.',
            'details': '게임을 선택하고 시작하기 전에 안내를 읽으세요.',
            'reports': '게임을 선택하고 시작하기 전에 안내를 읽으세요.'},
 'Russian': {'login': 'Введите имя пользователя и пароль и нажмите Войти.',
             'games': 'Выберите игру и прочитайте инструкцию перед началом.',
             'memory': 'Смотрите на числа 10 секунд, затем введите их в том же порядке.',
             'pattern': 'Посмотрите на образец и повторите его по инструкции.',
             'attention': 'Следите за экраном и реагируйте на цель по инструкции.',
             'image': 'Смотрите на изображения во время отсчёта, затем выберите правильный ответ.',
             'schulte': 'Найдите числа по порядку, начиная с 1.',
             'spot': 'Найдите отличающийся предмет и выберите его.',
             'hidden': 'Найдите скрытые объекты на изображении.',
             'target': 'Нажмите на цель до того, как она исчезнет.',
             'patient_registration': 'Введите имя пользователя и пароль и нажмите Войти.',
             'provider_registration': 'Введите имя пользователя и пароль и нажмите Войти.',
             'home': 'Выберите игру и прочитайте инструкцию перед началом.',
             'reminders': 'Выберите игру и прочитайте инструкцию перед началом.',
             'history': 'Выберите игру и прочитайте инструкцию перед началом.',
             'details': 'Выберите игру и прочитайте инструкцию перед началом.',
             'reports': 'Выберите игру и прочитайте инструкцию перед началом.'},
 'Turkish': {'login': "Kullanıcı adınızı ve şifrenizi girip Giriş yap'a basın.",
             'games': 'Bir oyun seçin ve başlamadan önce talimatları okuyun.',
             'memory': 'Sayıları 10 saniye izleyin, sonra aynı sırayla girin.',
             'pattern': 'Desene bakın ve talimata göre yeniden oluşturun.',
             'attention': 'Ekranı izleyin ve hedef göründüğünde talimata göre yanıt verin.',
             'image': 'Geri sayım sırasında resimlere bakın, sonra doğru cevabı seçin.',
             'schulte': "1'den başlayarak sayıları sırayla bulun.",
             'spot': 'Farklı nesneyi bulun ve seçin.',
             'hidden': 'Resimdeki gizli nesneleri bulun.',
             'target': 'Hedef kaybolmadan önce ona dokunun.',
             'patient_registration': "Kullanıcı adınızı ve şifrenizi girip Giriş yap'a basın.",
             'provider_registration': "Kullanıcı adınızı ve şifrenizi girip Giriş yap'a basın.",
             'home': 'Bir oyun seçin ve başlamadan önce talimatları okuyun.',
             'reminders': 'Bir oyun seçin ve başlamadan önce talimatları okuyun.',
             'history': 'Bir oyun seçin ve başlamadan önce talimatları okuyun.',
             'details': 'Bir oyun seçin ve başlamadan önce talimatları okuyun.',
             'reports': 'Bir oyun seçin ve başlamadan önce talimatları okuyun.'},
 'Assamese': {'login': 'আপোনাৰ ইউজাৰনেম আৰু পাছৱৰ্ড লিখি Login টিপক।',
              'games': 'এটা গেম বাছি লওক আৰু আৰম্ভ কৰাৰ আগতে নিৰ্দেশনা পঢ়ক।',
              'memory': '১০ ছেকেণ্ড সংখ্যা চাওক, তাৰ পিছত একে ক্ৰমত লিখক।',
              'pattern': 'পেটাৰ্নটো চাওক আৰু নিৰ্দেশনা অনুসৰি পুনৰ কৰক।',
              'attention': 'স্ক্ৰীনলৈ লক্ষ্য ৰাখি লক্ষ্য দেখা দিলে নিৰ্দেশনা অনুসৰি কাম কৰক।',
              'image': 'কাউণ্টডাউনৰ সময়ত ছবিবোৰ চাওক আৰু পিছত সঠিক উত্তৰ বাছক।',
              'schulte': '১ৰ পৰা সংখ্যা ক্ৰমত বিচাৰক।',
              'spot': 'বেলেগ বস্তুটো বিচাৰি বাছক।',
              'hidden': 'ছবিত লুকাই থকা লক্ষ্য বিচাৰক।',
              'target': 'লক্ষ্যটো নোহোৱা হোৱাৰ আগতে টিপক।',
              'patient_registration': 'আপোনাৰ ইউজাৰনেম আৰু পাছৱৰ্ড লিখি Login টিপক।',
              'provider_registration': 'আপোনাৰ ইউজাৰনেম আৰু পাছৱৰ্ড লিখি Login টিপক।',
              'home': 'এটা গেম বাছি লওক আৰু আৰম্ভ কৰাৰ আগতে নিৰ্দেশনা পঢ়ক।',
              'reminders': 'এটা গেম বাছি লওক আৰু আৰম্ভ কৰাৰ আগতে নিৰ্দেশনা পঢ়ক।',
              'history': 'এটা গেম বাছি লওক আৰু আৰম্ভ কৰাৰ আগতে নিৰ্দেশনা পঢ়ক।',
              'details': 'এটা গেম বাছি লওক আৰু আৰম্ভ কৰাৰ আগতে নিৰ্দেশনা পঢ়ক।',
              'reports': 'এটা গেম বাছি লওক আৰু আৰম্ভ কৰাৰ আগতে নিৰ্দেশনা পঢ়ক।'},
 'Bodo': {'login': 'Username aru password no, Login button dabao.',
          'games': 'Game khon saai, start-a agote instruction porho.',
          'memory': '10 second number saai, pise same order-a number no likho.',
          'pattern': 'Pattern saai, instruction mutabik abar bonhao.',
          'attention': 'Screen saai, target aasile instruction mutabik response koro.',
          'image': 'Countdown somoi image saai, pise correct answer saai lo.',
          'schulte': '1 niphrai number order-a saai lo.',
          'spot': 'Different item saai select koro.',
          'hidden': 'Image-a hidden target saai lo.',
          'target': 'Target disappear howar agote tap koro.',
          'patient_registration': 'Username aru password no, Login button dabao.',
          'provider_registration': 'Username aru password no, Login button dabao.',
          'home': 'Game khon saai, start-a agote instruction porho.',
          'reminders': 'Game khon saai, start-a agote instruction porho.',
          'history': 'Game khon saai, start-a agote instruction porho.',
          'details': 'Game khon saai, start-a agote instruction porho.',
          'reports': 'Game khon saai, start-a agote instruction porho.'},
 'Khasi': {'login': 'Thoh ia ka username bad password, nangta pynleit Login.',
           'games': 'Jied ia ka game bad pule ia ki jingbthah shuwa ban sdang.',
           'memory': 'Peit ia ki number 10 second, nangta thoh ia ki ha kajuh ka rukom.',
           'pattern': 'Peit ia ka pattern bad leh biang katkum ka jingbthah.',
           'attention': 'Peit ia ka screen bad jubab haba mih ka target.',
           'image': 'Peit ia ki dur ha ka countdown, nangta jied ia ka jubab kaba dei.',
           'schulte': 'Wad ia ki number ha ka jinglong naduh 1.',
           'spot': 'Wad ia ka item kaba pher bad jied ia ka.',
           'hidden': 'Wad ia ki target kiba rieh ha ka dur.',
           'target': 'Tap ia ka target shuwa ba kan jah.',
           'patient_registration': 'Thoh ia ka username bad password, nangta pynleit Login.',
           'provider_registration': 'Thoh ia ka username bad password, nangta pynleit Login.',
           'home': 'Jied ia ka game bad pule ia ki jingbthah shuwa ban sdang.',
           'reminders': 'Jied ia ka game bad pule ia ki jingbthah shuwa ban sdang.',
           'history': 'Jied ia ka game bad pule ia ki jingbthah shuwa ban sdang.',
           'details': 'Jied ia ka game bad pule ia ki jingbthah shuwa ban sdang.',
           'reports': 'Jied ia ka game bad pule ia ki jingbthah shuwa ban sdang.'},
 'Mizo': {'login': 'Username leh password ziak la Login tih rawh.',
          'games': 'Game pakhat thlang la tan hma chuan thuchhuah hi chhiar rawh.',
          'memory': '10 second chhung number en la an bo hnuah order angin ziak rawh.',
          'pattern': 'Pattern en la thuchhuah angin siam leh rawh.',
          'attention': 'Screen en la target a lo langin thuchhuah angin chhang rawh.',
          'image': 'Countdown chhung image en la a zawh hnuah chhanna dik thlang rawh.',
          'schulte': '1 atangin number chu orderin zawng rawh.',
          'spot': 'A danglam item chu zawng la thlang rawh.',
          'hidden': 'Image-ah target thup chu zawng rawh.',
          'target': 'Target bo hma in tap rawh.',
          'patient_registration': 'Username leh password ziak la Login tih rawh.',
          'provider_registration': 'Username leh password ziak la Login tih rawh.',
          'home': 'Game pakhat thlang la tan hma chuan thuchhuah hi chhiar rawh.',
          'reminders': 'Game pakhat thlang la tan hma chuan thuchhuah hi chhiar rawh.',
          'history': 'Game pakhat thlang la tan hma chuan thuchhuah hi chhiar rawh.',
          'details': 'Game pakhat thlang la tan hma chuan thuchhuah hi chhiar rawh.',
          'reports': 'Game pakhat thlang la tan hma chuan thuchhuah hi chhiar rawh.'},
 'Meitei (Manipuri)': {'login': 'Username amasung password thokpa matamda Login piba yeng-u.',
                       'games': 'Game ama amsu thokpa mapungda instruction puba yeng-u.',
                       'memory': 'Number-sing 10 second yeng-u, amagumba order-da piba yeng-u.',
                       'pattern': 'Pattern yeng-u amasung instruction matungda amuk hakpa tou-u.',
                       'attention': 'Screen yeng-u amasung target lakpa matamda instruction matungda tou-u.',
                       'image': 'Countdown matamda image-sing yeng-u amasung matungda correct answer khang-u.',
                       'schulte': '1 dagi number-sing order-da yeng-u.',
                       'spot': 'Different item khang-u amasung select tou-u.',
                       'hidden': 'Image-da thokpa target-sing yeng-u.',
                       'target': 'Target yaotpa mapungda tap tou-u.',
                       'patient_registration': 'Username amasung password thokpa matamda Login piba yeng-u.',
                       'provider_registration': 'Username amasung password thokpa matamda Login piba yeng-u.',
                       'home': 'Game ama amsu thokpa mapungda instruction puba yeng-u.',
                       'reminders': 'Game ama amsu thokpa mapungda instruction puba yeng-u.',
                       'history': 'Game ama amsu thokpa mapungda instruction puba yeng-u.',
                       'details': 'Game ama amsu thokpa mapungda instruction puba yeng-u.',
                       'reports': 'Game ama amsu thokpa mapungda instruction puba yeng-u.'},
 'Kannada': {'login': 'ನಿಮ್ಮ ಬಳಕೆದಾರ ಹೆಸರು ಮತ್ತು ಪಾಸ್\u200cವರ್ಡ್ ನಮೂದಿಸಿ Login ಒತ್ತಿರಿ. ಹೊಸ ಖಾತೆಗೆ ಸರಿಯಾದ Registration '
                      'ಆಯ್ಕೆಮಾಡಿ.',
             'patient_registration': 'ನಿಮ್ಮ ವಿವರಗಳನ್ನು ನಮೂದಿಸಿ, ಬಳಕೆದಾರ ಹೆಸರು ಮತ್ತು ಪಾಸ್\u200cವರ್ಡ್ ರಚಿಸಿ, ಭಾಷೆ ಆಯ್ಕೆ '
                                     'ಮಾಡಿ ಖಾತೆ ರಚಿಸಿ.',
             'provider_registration': 'ವೈಯಕ್ತಿಕ ಮತ್ತು ವೃತ್ತಿಪರ ವಿವರಗಳನ್ನು ನಮೂದಿಸಿ, ಅಗತ್ಯ ಅರ್ಹತಾ ಮಾಹಿತಿ/ದಾಖಲೆ ನೀಡಿ '
                                      'ಮತ್ತು Submit ಮಾಡಿ. ನಿರ್ವಾಹಕರ ಪರಿಶೀಲನೆ ಬೇಕಾಗಬಹುದು.',
             'home': 'ಡ್ಯಾಶ್\u200cಬೋರ್ಡ್\u200cನಲ್ಲಿ ನಿಮ್ಮ ಸ್ಥಿತಿಯನ್ನು ನೋಡಿ. Games, Reminders, History, Details ಮತ್ತು '
                     'Reports ತೆರೆಯಲು ಮೆನು ಬಳಸಿ.',
             'games': 'ಒಂದು ಆಟವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ ಮತ್ತು ಆರಂಭಿಸುವ ಮೊದಲು ಸೂಚನೆ ಓದಿ. ಎಲ್ಲಾ ಸುತ್ತುಗಳನ್ನು ಎಚ್ಚರಿಕೆಯಿಂದ '
                      'ಪೂರ್ಣಗೊಳಿಸಿ. ಅಪೂರ್ಣ ಆಟದಿಂದ ಯಾವಾಗ ಬೇಕಾದರೂ ಹೊರಬರಬಹುದು.',
             'memory': '10 ಸೆಕೆಂಡ್\u200cಗಳ ಕಾಲ ಸಂಖ್ಯೆಗಳನ್ನು ಗಮನಿಸಿ. ಅವು ಮರೆಯಾದ ನಂತರ ಅದೇ ಕ್ರಮದಲ್ಲಿ ನಮೂದಿಸಿ.',
             'pattern': 'ಪ್ಯಾಟರ್ನ್ ನೋಡಿ. ಅದು ಮರೆಯಾದ ನಂತರ ಸೂಚನೆಯಂತೆ ಮತ್ತೆ ರಚಿಸಿ.',
             'attention': 'ಪರದೆಯನ್ನು ಗಮನಿಸಿ. ಗುರಿ ಕಾಣಿಸಿದಾಗ ಸೂಚನೆಯಂತೆ ಪ್ರತಿಕ್ರಿಯಿಸಿ.',
             'image': 'ಕೌಂಟ್\u200cಡೌನ್ ಸಮಯದಲ್ಲಿ ಚಿತ್ರಗಳನ್ನು ನೋಡಿ. ಮುಗಿದ ನಂತರ ಸರಿಯಾದ ಉತ್ತರ ಆಯ್ಕೆಮಾಡಿ.',
             'schulte': '1ರಿಂದ ಆರಂಭಿಸಿ ಸಂಖ್ಯೆಗಳನ್ನು ಕ್ರಮವಾಗಿ ಹುಡುಕಿ ಮತ್ತು ಸರಿಯಾಗಿ ಒತ್ತಿರಿ.',
             'spot': 'ಎರಡೂ ಬದಿಗಳನ್ನು ಗಮನಿಸಿ. ವಿಭಿನ್ನ ವಸ್ತುವನ್ನು ಹುಡುಕಿ ಆಯ್ಕೆಮಾಡಿ.',
             'hidden': 'ಚಿತ್ರದಲ್ಲಿರುವ ಮರೆಮಾಡಿದ ವಸ್ತುಗಳನ್ನು ಹುಡುಕಿ ಮತ್ತು ಗುರಿಯನ್ನು ಒತ್ತಿರಿ.',
             'target': 'ಗ್ರಿಡ್\u200cನಲ್ಲಿ ಗುರಿ ಸ್ವಲ್ಪ ಸಮಯ ಕಾಣಿಸುತ್ತದೆ. ಅದು ಮರೆಯಾಗುವ ಮೊದಲು ಒತ್ತಿರಿ. ಇತರ ಕೋಶಗಳನ್ನು '
                       'ಒತ್ತಬೇಡಿ.',
             'reminders': 'ಹೆಸರು ಮತ್ತು ಸಮಯದೊಂದಿಗೆ Reminder ಸೇರಿಸಿ. ಅಗತ್ಯವಿಲ್ಲದ Reminder ಅಳಿಸಿ.',
             'history': 'ಹಿಂದಿನ ಆಟಗಳ ಸ್ಕೋರ್ ಮತ್ತು ಕಾರ್ಯಕ್ಷಮತೆಯನ್ನು ನೋಡಿ. ನಿಮ್ಮ ಪ್ರಗತಿಯನ್ನು ಪರಿಶೀಲಿಸಿ.',
             'details': 'ನಿಮ್ಮ ಪ್ರೊಫೈಲ್, ಭಾಷೆ, ಸಂಪರ್ಕಿತ ವೈದ್ಯರು/ಕೇರ್\u200cಟೇಕರ್ ಮತ್ತು ಇತರ ವಿವರಗಳನ್ನು ನೋಡಿ.',
             'reports': 'ಲಭ್ಯವಿರುವ ವರದಿಗಳನ್ನು ತೆರೆಯಿರಿ ಮತ್ತು ದಾಖಲಾದ ಕಾರ್ಯಕ್ಷಮತೆಯನ್ನು ಪರಿಶೀಲಿಸಿ.'},
 'Malayalam': {'login': 'നിങ്ങളുടെ ഉപയോക്തൃനാമവും പാസ്\u200cവേഡും നൽകി Login അമർത്തുക. പുതിയ അക്കൗണ്ടിന് ശരിയായ '
                        'Registration തിരഞ്ഞെടുക്കുക.',
               'patient_registration': 'നിങ്ങളുടെ വിവരങ്ങൾ നൽകുക, ഉപയോക്തൃനാമവും പാസ്\u200cവേഡും സൃഷ്ടിക്കുക, ഭാഷ '
                                       'തിരഞ്ഞെടുക്കുക, അക്കൗണ്ട് സൃഷ്ടിക്കുക.',
               'provider_registration': 'വ്യക്തിഗതവും പ്രൊഫഷണൽ വിവരങ്ങളും നൽകുക, ആവശ്യമായ യോഗ്യതാ വിവരങ്ങൾ/രേഖ നൽകുക, '
                                        'Submit ചെയ്യുക. അഡ്മിൻ പരിശോധന ആവശ്യമായേക്കാം.',
               'home': 'ഡാഷ്ബോർഡിൽ നിങ്ങളുടെ നില കാണുക. Games, Reminders, History, Details, Reports എന്നിവ മെനുവിൽ '
                       'നിന്ന് തുറക്കുക.',
               'games': 'ഒരു ഗെയിം തിരഞ്ഞെടുക്കുക. തുടങ്ങുന്നതിന് മുമ്പ് നിർദ്ദേശങ്ങൾ വായിക്കുക. എല്ലാ റൗണ്ടുകളും '
                        'ശ്രദ്ധയോടെ പൂർത്തിയാക്കുക.',
               'memory': '10 സെക്കന്റ് നമ്പറുകൾ ശ്രദ്ധിച്ച് കാണുക. മറഞ്ഞ ശേഷം അതേ ക്രമത്തിൽ നൽകുക.',
               'pattern': 'പാറ്റേൺ ശ്രദ്ധിച്ച് കാണുക. മറഞ്ഞ ശേഷം നിർദ്ദേശപ്രകാരം വീണ്ടും ഉണ്ടാക്കുക.',
               'attention': 'സ്ക്രീൻ ശ്രദ്ധിക്കുക. ലക്ഷ്യം കാണുമ്പോൾ നിർദ്ദേശപ്രകാരം പ്രതികരിക്കുക.',
               'image': 'കൗണ്ട്ഡൗൺ സമയത്ത് ചിത്രങ്ങൾ കാണുക. അത് കഴിഞ്ഞാൽ ശരിയായ ഉത്തരം തിരഞ്ഞെടുക്കുക.',
               'schulte': '1 മുതൽ തുടങ്ങി നമ്പറുകൾ ക്രമത്തിൽ കണ്ടെത്തി അമർത്തുക.',
               'spot': 'രണ്ടു വശങ്ങളും ശ്രദ്ധിച്ച് നോക്കുക. വ്യത്യസ്തമായ വസ്തു കണ്ടെത്തി തിരഞ്ഞെടുക്കുക.',
               'hidden': 'ചിത്രത്തിലെ മറഞ്ഞിരിക്കുന്ന വസ്തുക്കൾ കണ്ടെത്തി ലക്ഷ്യത്തിൽ ടാപ്പ് ചെയ്യുക.',
               'target': 'ഗ്രിഡിൽ ലക്ഷ്യം കുറച്ച് സമയം കാണും. അത് അപ്രത്യക്ഷമാകുന്നതിന് മുമ്പ് ടാപ്പ് ചെയ്യുക.',
               'reminders': 'പേരും സമയവും നൽകി Reminder ചേർക്കുക. ആവശ്യമില്ലാത്തവ നീക്കം ചെയ്യുക.',
               'history': 'മുൻ ഗെയിം സ്കോറുകളും പ്രകടനവും കാണുക. നിങ്ങളുടെ പുരോഗതി പരിശോധിക്കുക.',
               'details': 'നിങ്ങളുടെ പ്രൊഫൈൽ, ഭാഷ, ബന്ധിപ്പിച്ച ഡോക്ടർ/കെയർടേക്കർ, മറ്റ് വിവരങ്ങൾ കാണുക.',
               'reports': 'ലഭ്യമായ റിപ്പോർട്ടുകൾ തുറന്ന് രേഖപ്പെടുത്തിയ പ്രകടനം പരിശോധിക്കുക.'},
 'Punjabi': {'login': 'ਆਪਣਾ ਯੂਜ਼ਰਨੇਮ ਅਤੇ ਪਾਸਵਰਡ ਭਰੋ ਅਤੇ Login ਦਬਾਓ। ਨਵਾਂ ਖਾਤਾ ਬਣਾਉਣ ਲਈ ਸਹੀ Registration ਚੁਣੋ.',
             'patient_registration': 'ਆਪਣੀ ਜਾਣਕਾਰੀ ਭਰੋ, ਯੂਜ਼ਰਨੇਮ ਅਤੇ ਪਾਸਵਰਡ ਬਣਾਓ, ਭਾਸ਼ਾ ਚੁਣੋ ਅਤੇ ਖਾਤਾ ਬਣਾਓ.',
             'provider_registration': 'ਨਿੱਜੀ ਅਤੇ ਪੇਸ਼ੇਵਰ ਜਾਣਕਾਰੀ ਭਰੋ, ਲੋੜੀਂਦੀ ਯੋਗਤਾ ਦੀ ਜਾਣਕਾਰੀ/ਦਸਤਾਵੇਜ਼ ਦਿਓ ਅਤੇ Submit '
                                      'ਕਰੋ। ਐਡਮਿਨ ਜਾਂਚ ਲੋੜੀਂਦੀ ਹੋ ਸਕਦੀ ਹੈ.',
             'home': "ਡੈਸ਼ਬੋਰਡ 'ਤੇ ਆਪਣੀ ਸਥਿਤੀ ਵੇਖੋ। Games, Reminders, History, Details ਅਤੇ Reports ਮੀਨੂ ਤੋਂ ਖੋਲ੍ਹੋ.",
             'games': 'ਇੱਕ ਗੇਮ ਚੁਣੋ ਅਤੇ ਸ਼ੁਰੂ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਹਦਾਇਤਾਂ ਪੜ੍ਹੋ। ਸਾਰੇ ਰਾਊਂਡ ਧਿਆਨ ਨਾਲ ਪੂਰੇ ਕਰੋ.',
             'memory': '10 ਸਕਿੰਟ ਲਈ ਨੰਬਰ ਧਿਆਨ ਨਾਲ ਵੇਖੋ। ਲੁਕਣ ਤੋਂ ਬਾਅਦ ਉਹੀ ਕ੍ਰਮ ਵਿੱਚ ਦਰਜ ਕਰੋ.',
             'pattern': 'ਪੈਟਰਨ ਵੇਖੋ। ਲੁਕਣ ਤੋਂ ਬਾਅਦ ਹਦਾਇਤ ਅਨੁਸਾਰ ਦੁਬਾਰਾ ਬਣਾਓ.',
             'attention': "ਸਕ੍ਰੀਨ ਵੇਖੋ ਅਤੇ ਟਾਰਗੇਟ ਆਉਣ 'ਤੇ ਹਦਾਇਤ ਅਨੁਸਾਰ ਜਵਾਬ ਦਿਓ.",
             'image': 'ਕਾਊਂਟਡਾਊਨ ਦੌਰਾਨ ਤਸਵੀਰਾਂ ਵੇਖੋ। ਖਤਮ ਹੋਣ ਤੋਂ ਬਾਅਦ ਸਹੀ ਜਵਾਬ ਚੁਣੋ.',
             'schulte': '1 ਤੋਂ ਸ਼ੁਰੂ ਕਰਕੇ ਨੰਬਰ ਕ੍ਰਮ ਵਿੱਚ ਲੱਭੋ ਅਤੇ ਦਬਾਓ.',
             'spot': 'ਦੋਵੇਂ ਪਾਸੇ ਧਿਆਨ ਨਾਲ ਵੇਖੋ। ਵੱਖਰੀ ਚੀਜ਼ ਲੱਭ ਕੇ ਚੁਣੋ.',
             'hidden': "ਤਸਵੀਰ ਵਿੱਚ ਲੁਕੀਆਂ ਚੀਜ਼ਾਂ ਲੱਭੋ ਅਤੇ ਟਾਰਗੇਟ 'ਤੇ ਟੈਪ ਕਰੋ.",
             'target': 'ਗ੍ਰਿਡ ਵਿੱਚ ਟਾਰਗੇਟ ਥੋੜ੍ਹੇ ਸਮੇਂ ਲਈ ਦਿਖੇਗਾ। ਗਾਇਬ ਹੋਣ ਤੋਂ ਪਹਿਲਾਂ ਟੈਪ ਕਰੋ.',
             'reminders': 'ਨਾਮ ਅਤੇ ਸਮਾਂ ਦੇ ਕੇ Reminder ਜੋੜੋ। ਲੋੜ ਨਾ ਹੋਣ ਵਾਲੇ ਮਿਟਾਓ.',
             'history': 'ਪਿਛਲੀਆਂ ਗੇਮਾਂ ਦੇ ਸਕੋਰ ਅਤੇ ਪ੍ਰਦਰਸ਼ਨ ਵੇਖੋ ਅਤੇ ਆਪਣੀ ਤਰੱਕੀ ਜਾਂਚੋ.',
             'details': 'ਆਪਣੀ ਪ੍ਰੋਫਾਈਲ, ਭਾਸ਼ਾ, ਜੁੜੇ ਡਾਕਟਰ/ਕੇਅਰਟੇਕਰ ਅਤੇ ਹੋਰ ਜਾਣਕਾਰੀ ਵੇਖੋ.',
             'reports': 'ਉਪਲਬਧ ਰਿਪੋਰਟ ਖੋਲ੍ਹੋ ਅਤੇ ਦਰਜ ਕੀਤਾ ਪ੍ਰਦਰਸ਼ਨ ਵੇਖੋ.'},
 'Urdu': {'login': 'اپنا یوزرنیم اور پاس ورڈ درج کریں اور Login دبائیں۔ نئے اکاؤنٹ کے لیے مناسب Registration منتخب '
                   'کریں۔',
          'patient_registration': 'اپنی معلومات درج کریں، یوزرنیم اور پاس ورڈ بنائیں، زبان منتخب کریں اور اکاؤنٹ '
                                  'بنائیں۔',
          'provider_registration': 'ذاتی اور پیشہ ورانہ معلومات درج کریں، مطلوبہ اہلیت کی معلومات/دستاویز دیں اور '
                                   'Submit کریں۔ ایڈمن کی تصدیق ضروری ہو سکتی ہے۔',
          'home': 'ڈیش بورڈ پر اپنی حالت دیکھیں۔ Games، Reminders، History، Details اور Reports مینو سے کھولیں۔',
          'games': 'ایک گیم منتخب کریں اور شروع کرنے سے پہلے ہدایات پڑھیں۔ تمام راؤنڈ احتیاط سے مکمل کریں۔',
          'memory': '10 سیکنڈ تک نمبرز دیکھیں۔ چھپنے کے بعد انہیں اسی ترتیب میں درج کریں۔',
          'pattern': 'پیٹرن دیکھیں۔ چھپنے کے بعد ہدایات کے مطابق دوبارہ بنائیں۔',
          'attention': 'اسکرین دیکھیں اور ہدف ظاہر ہونے پر ہدایات کے مطابق جواب دیں۔',
          'image': 'کاؤنٹ ڈاؤن کے دوران تصاویر دیکھیں۔ ختم ہونے کے بعد درست جواب منتخب کریں۔',
          'schulte': '1 سے شروع کرکے نمبرز ترتیب سے تلاش کریں اور دبائیں۔',
          'spot': 'دونوں طرف غور سے دیکھیں۔ مختلف چیز تلاش کرکے منتخب کریں۔',
          'hidden': 'تصویر میں چھپی چیزیں تلاش کریں اور ہدف پر ٹیپ کریں۔',
          'target': 'گرڈ میں ہدف تھوڑی دیر کے لیے نظر آئے گا۔ غائب ہونے سے پہلے اسے ٹیپ کریں۔',
          'reminders': 'نام اور وقت کے ساتھ Reminder شامل کریں۔ غیر ضروری Reminder حذف کریں۔',
          'history': 'پچھلے گیمز کے اسکور اور کارکردگی دیکھیں اور اپنی پیش رفت جانچیں۔',
          'details': 'اپنی پروفائل، زبان، منسلک ڈاکٹر/کیئرٹیکر اور دیگر معلومات دیکھیں۔',
          'reports': 'دستیاب رپورٹس کھولیں اور ریکارڈ شدہ کارکردگی دیکھیں۔'},
 'Nepali': {'login': 'आफ्नो प्रयोगकर्ता नाम र पासवर्ड लेखेर Login थिच्नुहोस्। नयाँ खाताका लागि सही Registration '
                     'छान्नुहोस्।',
            'patient_registration': 'आफ्नो विवरण भर्नुहोस्, प्रयोगकर्ता नाम र पासवर्ड बनाउनुहोस्, भाषा छान्नुहोस् र '
                                    'खाता बनाउनुहोस्।',
            'provider_registration': 'व्यक्तिगत र व्यावसायिक विवरण भर्नुहोस्, आवश्यक योग्यता जानकारी/कागजात दिनुहोस् र '
                                     'Submit गर्नुहोस्। एडमिन प्रमाणीकरण आवश्यक हुन सक्छ।',
            'home': 'ड्यासबोर्डमा आफ्नो अवस्था हेर्नुहोस्। Games, Reminders, History, Details र Reports मेनुबाट '
                    'खोल्नुहोस्।',
            'games': 'एउटा खेल छान्नुहोस् र सुरु गर्नुअघि निर्देशन पढ्नुहोस्। सबै राउन्ड ध्यानपूर्वक पूरा गर्नुहोस्।',
            'memory': '१० सेकेन्डसम्म नम्बरहरू ध्यानपूर्वक हेर्नुहोस्। लुकेपछि उही क्रममा लेख्नुहोस्।',
            'pattern': 'प्याटर्न हेर्नुहोस्। लुकेपछि निर्देशनअनुसार फेरि बनाउनुहोस्।',
            'attention': 'स्क्रिन हेर्नुहोस् र लक्ष्य देखिँदा निर्देशनअनुसार प्रतिक्रिया दिनुहोस्।',
            'image': 'काउन्टडाउनमा तस्बिरहरू हेर्नुहोस्। सकिएपछि सही उत्तर छान्नुहोस्।',
            'schulte': '१ बाट सुरु गरेर नम्बरहरू क्रमसँग खोज्नुहोस् र थिच्नुहोस्।',
            'spot': 'दुवै पक्ष ध्यानपूर्वक हेर्नुहोस्। फरक वस्तु खोजेर छान्नुहोस्।',
            'hidden': 'तस्बिरमा लुकेका वस्तुहरू खोज्नुहोस् र लक्ष्यमा ट्याप गर्नुहोस्।',
            'target': 'ग्रिडमा लक्ष्य केही समय देखिन्छ। हराउनुअघि ट्याप गर्नुहोस्।',
            'reminders': 'नाम र समय दिएर Reminder थप्नुहोस्। आवश्यक नभएका हटाउनुहोस्।',
            'history': 'अघिल्ला खेलका स्कोर र प्रदर्शन हेर्नुहोस् र आफ्नो प्रगति जाँच्नुहोस्।',
            'details': 'आफ्नो प्रोफाइल, भाषा, जोडिएको डाक्टर/केयरटेकर र अन्य विवरण हेर्नुहोस्।',
            'reports': 'उपलब्ध रिपोर्टहरू खोलेर रेकर्ड गरिएको प्रदर्शन हेर्नुहोस्।'}}

INSTRUCTION_LABELS = {'English': 'Instructions',
 'Hindi': 'निर्देश',
 'Marathi': 'सूचना',
 'Bengali': 'নির্দেশনা',
 'Gujarati': 'સૂચનાઓ',
 'Tamil': 'வழிமுறைகள்',
 'Telugu': 'సూచనలు',
 'Kannada': 'ಸೂಚನೆಗಳು',
 'Malayalam': 'നിർദ്ദേശങ്ങൾ',
 'Punjabi': 'ਹਦਾਇਤਾਂ',
 'Urdu': 'ہدایات',
 'Nepali': 'निर्देशनहरू',
 'French': 'Instructions',
 'Spanish': 'Instrucciones',
 'German': 'Anleitung',
 'Italian': 'Istruzioni',
 'Portuguese': 'Instruções',
 'Arabic': 'التعليمات',
 'Chinese': '使用说明',
 'Japanese': '説明',
 'Korean': '안내',
 'Russian': 'Инструкция',
 'Turkish': 'Talimatlar',
 'Assamese': 'নিৰ্দেশনা',
 'Bodo': 'Instruction',
 'Khasi': 'Jingbthah',
 'Mizo': 'Thuchhuah',
 'Meitei (Manipuri)': 'Instruction'}

def instruction_text(key, language):
    language_data = INSTRUCTION_TRANSLATIONS.get(
        language,
        INSTRUCTION_TRANSLATIONS["English"]
    )
    return language_data.get(
        key,
        INSTRUCTION_TRANSLATIONS["English"].get(key, "")
    )

def show_instructions(key, language, expanded=False):
    title = INSTRUCTION_LABELS.get(language, "Instructions")
    message = instruction_text(key, language)
    if message:
        with st.expander("📘 " + title, expanded=expanded):
            st.info(message)



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
    message = st.session_state.get("pending_voice_message")
    language = st.session_state.get("pending_voice_language", "English")

    if not message:
        return

    st.session_state.pending_voice_message = None
    st.session_state.pending_voice_language = None

    html = generate_voice_html(message, language)

    if html:
        st.markdown(html, unsafe_allow_html=True)


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
        return None, "SpeechRecognition package is not installed."
    if not audio_bytes:
        return None, "No audio was recorded. Please speak after starting the microphone."
    try:
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 250
        recognizer.pause_threshold = 0.8
        recognizer.phrase_threshold = 0.2
        recognizer.non_speaking_duration = 0.5
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.25)
            except Exception:
                pass
            audio = recognizer.record(source)
        primary_language = LANGUAGES.get(language, LANGUAGES["English"])["speech"]
        languages_to_try = [primary_language]
        english_language = LANGUAGES["English"]["speech"]
        if primary_language != english_language:
            languages_to_try.append(english_language)
        for speech_language in languages_to_try:
            try:
                command = recognizer.recognize_google(audio, language=speech_language)
                command = re.sub(r"\s+", " ", command.lower().strip())
                if command:
                    return command, None
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                return None, "Speech recognition service is unavailable. Check your internet connection."
        return None, "I could not clearly understand your speech. Please speak louder and more slowly."
    except Exception as exc:
        return None, f"Voice input failed. Check microphone permission. ({type(exc).__name__})"


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

    "caretaker_id": None,

    "provider_role": None,

    "page": "home",

    "welcome_pending": False,

    "pending_voice_message": None,

    "pending_voice_language": None,

    "memory_sequence": None,

    "pattern_sequence": None,

    "reaction_target": None,

    "memory_round": 0,
    "memory_total_score": 0.0,
    "memory_start_time": None,
    "memory_answer_phase": False,
    "pattern_round": 0,
    "pattern_total_score": 0.0,
    "attention_round": 0,
    "attention_total_score": 0.0,

    # Image Recognition / Image Memory Game state.
    "image_memory_round": 0,
    "image_memory_total_score": 0.0,
    "image_memory_sequence": [],
    "image_memory_choices": [],
    "image_memory_start_time": None,
    "image_memory_answer_phase": False,
    "image_memory_selected": [],

    # Visible result message shown after a completed game.
    "game_result_message": None,
    "game_result_score": None,
    "game_result_old_difficulty": None,
    "game_result_new_difficulty": None,
    "selected_certificate_id": None,
    "schulte_running": False,
    "schulte_grid": [],
    "schulte_next": 1,
    "schulte_start_time": None,
    "schulte_errors": 0,
    "schulte_round": 0,
    "spot_running": False,
    "spot_grid_left": [],
    "spot_grid_right": [],
    "spot_difference": None,
    "spot_choice": None,
    "spot_round": 0,
    "hidden_running": False,
    "hidden_targets": [],
    "hidden_found": [],
    "hidden_round": 0,
    "tracker_running": False,
    "tracker_size": 4,
    "tracker_round": 0,
    "tracker_hits": 0,
    "tracker_target_pos": None,
    "tracker_target_start": None,
}


for key, value in DEFAULT_SESSION_VALUES.items():

    if key not in st.session_state:

        st.session_state[key] = value

# Backward-compatible image choice state for existing sessions.
if "image_memory_choices" not in st.session_state:
    st.session_state.image_memory_choices = []


# ============================================================
# PLAY PENDING VOICE
# ============================================================

if st.session_state.logged_in:

    play_pending_voice()


# ============================================================
# LOGIN / REGISTRATION
# ============================================================

if not st.session_state.logged_in:

    # Login / registration starts directly here.
    # The large center logo is intentionally not shown.
    st.markdown(f"# {APP_NAME}")

    st.info(
        f"{APP_NAME} is a prototype for "
        "cognitive wellness and performance tracking. "
        "It is not a medical diagnostic system."
    )

    # Choose a language before login so even first-time users can read the
    # login and registration instructions in their preferred language.
    if "prelogin_language" not in st.session_state:
        st.session_state.prelogin_language = "English"

    prelogin_language = st.selectbox(
        "🌐 Language / भाषा",
        list(LANGUAGES.keys()),
        key="prelogin_language"
    )

    show_instructions("login", prelogin_language, expanded=True)

    login_tab, signup_tab, doctor_signup_tab, caretaker_signup_tab = st.tabs(
        [
            "🔐 Login",
            "📝 Patient Registration",
            "🩺 Doctor Registration",
            "🤝 Caretaker Registration"
        ]
    )

    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        st.subheader("Login")
        show_instructions("login", prelogin_language)

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

            username_clean = username.strip()

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
                    st.session_state.provider_role = None
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
                        adaptive_difficulty,
                        caretaker_id,
                        phone,
                        email,
                        location,
                        qualification,
                        qualification_status,
                        account_status
                    FROM users
                    WHERE LOWER(username)=LOWER(?)
                    """,
                    (username_clean,)
                ).fetchone()

                if user is None:

                    st.error(
                        "Username not found."
                    )

                elif hash_password(password) != user[3]:

                    st.error(
                        "Incorrect password."
                    )

                elif user[14] != "Active":

                    status_message = {
                        "Pending Verification": (
                            "Your account is waiting for administrator verification."
                        ),
                        "Rejected": (
                            "Your account was not approved. Please contact the administrator."
                        ),
                        "Inactive": (
                            "Your account is currently inactive. Please contact the administrator."
                        ),
                    }.get(
                        user[14],
                        "Your account is not active. Please contact the administrator."
                    )

                    st.error(status_message)

                else:

                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.name = user[1]
                    st.session_state.username = user[2]
                    st.session_state.language = user[4]
                    st.session_state.role = user[5]
                    st.session_state.doctor_id = user[6]
                    st.session_state.caretaker_id = user[8]
                    st.session_state.provider_role = (
                        user[5]
                        if user[5] in ("doctor", "caretaker")
                        else None
                    )
                    st.session_state.page = "home"

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
                                "You can manage your own patients "
                                "and review their performance."
                            ),
                            user[4]
                        )

                    elif user[5] == "caretaker":

                        queue_voice(
                            (
                                f"Welcome {user[1]}. "
                                "You have logged in successfully. "
                                "You can manage your own linked patients "
                                "and review their progress."
                            ),
                            user[4]
                        )

                    st.rerun()

    # ========================================================
    # PATIENT REGISTRATION - ORIGINAL FLOW KEPT
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

        reg_phone = st.text_input(
            "Phone Number (optional)",
            key="reg_phone"
        )

        reg_email = st.text_input(
            "Email ID (optional)",
            key="reg_email"
        )

        reg_location = st.text_input(
            "Location (optional)",
            key="reg_location"
        )

        reg_dob = st.date_input(
            "Date of Birth",
            value=date(1990, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            key="reg_dob"
        )
        reg_photo = st.file_uploader(
            "Patient Photo (optional)",
            type=["png", "jpg", "jpeg"],
            key="reg_photo"
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

                st.error("Please enter your name.")

            elif not reg_username.strip():

                st.error("Please enter a username.")

            elif len(reg_password) < 6:

                st.error("Password must contain at least 6 characters.")

            elif reg_password != reg_confirm:

                st.error("Passwords do not match.")

            elif reg_phone.strip() and not phone_is_valid(reg_phone):

                st.error("Please enter a valid phone number.")

            elif reg_email.strip() and not email_is_valid(reg_email):

                st.error("Please enter a valid email address.")

            else:

                existing = conn.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE LOWER(username)=LOWER(?)
                    """,
                    (reg_username.strip(),)
                ).fetchone()

                if existing:

                    st.error("Username already exists.")

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
                            adaptive_difficulty,
                            phone,
                            email,
                            location,
                            date_of_birth,
                            age,
                            photo,
                            account_status,
                            created_at
                        )
                        VALUES(
                            ?, ?, ?, ?, 0, 'patient', 1, ?, ?, ?, ?, ?, ?, 'Active', ?
                        )
                        """,
                        (
                            reg_name.strip(),
                            reg_username.strip(),
                            hash_password(reg_password),
                            reg_language,
                            reg_phone.strip(),
                            reg_email.strip(),
                            normalize_location(reg_location),
                            reg_dob.isoformat(),
                            calculate_age_from_dob(reg_dob),
                            reg_photo.getvalue() if reg_photo else None,
                            datetime.now().isoformat(timespec="seconds")
                        )
                    )

                    conn.commit()

                    st.success(
                        "Patient account created successfully."
                    )

                    queue_voice(
                        (
                            f"Welcome {reg_name.strip()}. "
                            "Your patient account has been created successfully."
                        ),
                        reg_language
                    )

                    play_pending_voice()

    # ========================================================
    # DOCTOR REGISTRATION
    # ========================================================

    with doctor_signup_tab:

        st.subheader("🩺 Doctor Registration")
        st.info(
            "Doctor registrations require qualification details. "
            "The account remains pending until the administrator verifies the submitted qualification."
        )

        doc_name = st.text_input("Full Name", key="doctor_reg_name")
        doc_username = st.text_input("Username", key="doctor_reg_username")
        doc_password = st.text_input("Password", type="password", key="doctor_reg_password")
        doc_confirm = st.text_input("Confirm Password", type="password", key="doctor_reg_confirm")
        doc_phone = st.text_input("Phone Number", key="doctor_reg_phone")
        doc_email = st.text_input("Email ID", key="doctor_reg_email")
        doc_location = st.text_input("Location / Clinic Location", key="doctor_reg_location")
        doc_dob = st.date_input(
            "Date of Birth",
            value=date(1985, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            key="doctor_reg_dob"
        )
        doc_age = calculate_age_from_dob(doc_dob)
        st.caption(f"Calculated age: {doc_age} years. Doctor registration age limit: 25–70 years.")
        doc_photo = st.file_uploader(
            "Doctor Photo",
            type=["png", "jpg", "jpeg"],
            key="doctor_reg_photo"
        )
        doc_qualification = st.text_input(
            "Degree / Qualification",
            placeholder="Example: MBBS, MD, BDS, etc.",
            key="doctor_reg_qualification"
        )
        doc_qualification_number = st.text_input(
            "Medical Registration / Qualification Number",
            key="doctor_reg_qualification_number"
        )
        doc_document = st.file_uploader(
            "Upload Degree / Qualification Document",
            type=["pdf", "png", "jpg", "jpeg"],
            key="doctor_reg_document"
        )
        doc_language = st.selectbox(
            "Preferred Language",
            list(LANGUAGES.keys()),
            key="doctor_reg_language"
        )

        if st.button(
            "🩺 Submit Doctor Registration",
            type="primary",
            use_container_width=True
        ):

            if not doc_name.strip():
                st.error("Please enter the doctor's name.")
            elif not doc_username.strip():
                st.error("Please enter a username.")
            elif len(doc_password) < 6:
                st.error("Password must contain at least 6 characters.")
            elif doc_password != doc_confirm:
                st.error("Passwords do not match.")
            elif not phone_is_valid(doc_phone):
                st.error("Please enter a valid phone number.")
            elif not email_is_valid(doc_email):
                st.error("Please enter a valid email address.")
            elif not normalize_location(doc_location):
                st.error("Please enter the doctor's location.")
            elif doc_age < 25 or doc_age > 70:
                st.error("Doctor registration is allowed only for ages 25 to 70 years.")
            elif doc_photo is None:
                st.error("Please upload the doctor's photo.")
            elif not doc_qualification.strip():
                st.error("Please enter a degree or qualification.")
            elif not doc_qualification_number.strip():
                st.error("Please enter the medical registration/qualification number.")
            elif doc_document is None:
                st.error("Please upload the degree/qualification document.")
            else:

                existing = conn.execute(
                    "SELECT id FROM users WHERE LOWER(username)=LOWER(?)",
                    (doc_username.strip(),)
                ).fetchone()

                if existing:
                    st.error("Username already exists.")
                else:
                    # Store file bytes for document download/verification
                    doc_document_bytes = doc_document.getvalue() if doc_document else None
                    
                    conn.execute(
                        """
                        INSERT INTO users(
                            name, username, password_hash, language, baseline,
                            role, adaptive_difficulty, phone, email, location,
                            date_of_birth, age, photo,
                            qualification, qualification_number, qualification_document,
                            qualification_status, account_status, created_at
                        )
                        VALUES(
                            ?, ?, ?, ?, 0, 'doctor', 1, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            'Pending', 'Pending Verification', ?
                        )
                        """,
                        (
                            doc_name.strip(),
                            doc_username.strip(),
                            hash_password(doc_password),
                            doc_language,
                            doc_phone.strip(),
                            doc_email.strip(),
                            normalize_location(doc_location),
                            doc_dob.isoformat(),
                            doc_age,
                            doc_photo.getvalue(),
                            doc_qualification.strip(),
                            doc_qualification_number.strip(),
                            doc_document.name,
                            datetime.now().isoformat(timespec="seconds")
                        )
                    )
                    conn.commit()

                    st.success(
                        "Doctor registration submitted. Please wait for administrator verification."
                    )
                    announce(
                        "Doctor registration submitted successfully and is waiting for administrator verification.",
                        doc_language
                    )

    # ========================================================
    # CARETAKER REGISTRATION
    # ========================================================

    with caretaker_signup_tab:

        st.subheader("🤝 Caretaker Registration")
        st.info(
            "Caretakers register here. You can register freely. A doctor can later create a caretaker/nurse relationship from the doctor portal."
        )

        care_name = st.text_input("Full Name", key="caretaker_reg_name")
        care_username = st.text_input("Username", key="caretaker_reg_username")
        care_password = st.text_input("Password", type="password", key="caretaker_reg_password")
        care_confirm = st.text_input("Confirm Password", type="password", key="caretaker_reg_confirm")
        care_phone = st.text_input("Phone Number", key="caretaker_reg_phone")
        care_email = st.text_input("Email ID", key="caretaker_reg_email")
        care_location = st.text_input("Location", key="caretaker_reg_location")
        care_photo = st.file_uploader(
            "Caretaker / Nurse Photo",
            type=["png", "jpg", "jpeg"],
            key="caretaker_reg_photo"
        )
        care_relationship = st.text_input(
            "Relationship / Care Role",
            placeholder="Example: Family Caretaker, Home Care Assistant",
            key="caretaker_reg_relationship"
        )
        care_language = st.selectbox(
            "Preferred Language",
            list(LANGUAGES.keys()),
            key="caretaker_reg_language"
        )

        if st.button(
            "🤝 Create Caretaker Account",
            type="primary",
            use_container_width=True
        ):

            if not care_name.strip():
                st.error("Please enter the caretaker's name.")
            elif not care_username.strip():
                st.error("Please enter a username.")
            elif len(care_password) < 6:
                st.error("Password must contain at least 6 characters.")
            elif care_password != care_confirm:
                st.error("Passwords do not match.")
            elif not phone_is_valid(care_phone):
                st.error("Please enter a valid phone number.")
            elif not email_is_valid(care_email):
                st.error("Please enter a valid email address.")
            elif not normalize_location(care_location):
                st.error("Please enter the caretaker's location.")
            elif care_photo is None:
                st.error("Please upload the caretaker/nurse photo.")
            else:

                existing = conn.execute(
                    "SELECT id FROM users WHERE LOWER(username)=LOWER(?)",
                    (care_username.strip(),)
                ).fetchone()

                if existing:
                    st.error("Username already exists.")
                else:

                    # Store the care role in qualification for backward-compatible schema usage.
                    conn.execute(
                        """
                        INSERT INTO users(
                            name, username, password_hash, language, baseline,
                            role, adaptive_difficulty, phone, email, location,
                            photo, qualification, qualification_status, account_status, created_at
                        )
                        VALUES(
                            ?, ?, ?, ?, 0, 'caretaker', 1, ?, ?, ?, ?, ?,
                            'Not Required', 'Active', ?
                        )
                        """,
                        (
                            care_name.strip(),
                            care_username.strip(),
                            hash_password(care_password),
                            care_language,
                            care_phone.strip(),
                            care_email.strip(),
                            normalize_location(care_location),
                            care_photo.getvalue(),
                            care_relationship.strip(),
                            datetime.now().isoformat(timespec="seconds")
                        )
                    )
                    conn.commit()

                    st.success(
                        "Caretaker account created successfully."
                    )
                    announce(
                        "Caretaker account created successfully. You can use your caretaker portal to register patients. A doctor relationship can be created by the doctor who registers you.",
                        care_language
                    )

    st.stop()


# ============================================================
# CURRENT SESSION USER
# ============================================================

role = st.session_state.role
user_id = st.session_state.user_id
name = st.session_state.name
language = st.session_state.language

# ============================================================
# APP BRANDING HEADER FOR LOGGED-IN USERS
# ============================================================
brand_col1, brand_col2 = st.columns([1, 6])
with brand_col1:
    if APP_LOGO is not None:
        st.image(APP_LOGO, width=105)
with brand_col2:
    st.markdown(f"# {APP_NAME}")
    st.caption("Bridging Memory, Care & Connection")

# A simple instruction is also shown for administrator, doctor and caretaker
# portals. It uses the language saved for the logged-in account.
if role in ("admin", "doctor", "caretaker"):
    show_instructions("home", language, expanded=False)


# ============================================================
# ADMIN DASHBOARD
# ============================================================

if role == "admin":

    st.title(
        "👑 SMRITISETU — Administrator Dashboard"
    )

    admin_tabs = st.tabs(
        [
            "📊 Overview",
            "👥 Patients",
            "🩺 Doctors",
            "🤝 Caretakers",
            "✅ Verification & Management",
            "🎮 All Sessions",
            "📄 All Reports",
            "📜 Treatment Certificates"
        ]
    )

    # ========================================================
    # OVERVIEW
    # ========================================================

    with admin_tabs[0]:

        patient_count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='patient'"
        ).fetchone()[0]

        doctor_count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='doctor'"
        ).fetchone()[0]

        caretaker_count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='caretaker'"
        ).fetchone()[0]

        pending_doctors = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE role='doctor'
            AND account_status='Pending Verification'
            """
        ).fetchone()[0]

        session_count = conn.execute(
            "SELECT COUNT(*) FROM sessions"
        ).fetchone()[0]

        report_count = conn.execute(
            "SELECT COUNT(*) FROM reports"
        ).fetchone()[0]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Patients", patient_count)
        c2.metric("Doctors", doctor_count)
        c3.metric("Caretakers", caretaker_count)
        c4.metric("Pending Doctor Verification", pending_doctors)
        c5.metric("Game Sessions", session_count)

        st.metric("Reports", report_count)

        st.info(
            "The administrator verifies doctors, assigns caretakers to doctors, and assigns patients to doctors and caretakers. "
            "Patients and care providers cannot change their own assignments."
        )

        db_ok, db_message = database_health_check()
        if db_ok:
            st.success(f"🟢 Database Status: {db_message}")
        else:
            st.error("🔴 Database Status: Connection check failed. The app will not switch to another database.")

    # ========================================================
    # PATIENTS
    # ========================================================

    with admin_tabs[1]:

        patients = conn.execute(
            """
            SELECT
                id, name, username, language, baseline,
                doctor_id, caretaker_id, adaptive_difficulty,
                phone, email, location, age, photo
            FROM users
            WHERE role='patient'
            ORDER BY name
            """
        ).fetchall()

        patient_data = []
        for patient_row in patients:

            doctor_name = "Not assigned"
            caretaker_name = "Not assigned"

            if patient_row[5]:
                d = conn.execute(
                    "SELECT name FROM users WHERE id=? AND role='doctor'",
                    (patient_row[5],)
                ).fetchone()
                if d:
                    doctor_name = "Dr. " + d[0]

            if patient_row[6]:
                c = conn.execute(
                    "SELECT name FROM users WHERE id=? AND role='caretaker'",
                    (patient_row[6],)
                ).fetchone()
                if c:
                    caretaker_name = c[0]

            patient_data.append(
                {
                    "ID": patient_row[0],
                    "Name": patient_row[1],
                    "Username": patient_row[2],
                    "Language": patient_row[3],
                    "Baseline": patient_row[4],
                    "Difficulty": patient_row[7],
                    "Phone": patient_row[8],
                    "Email": patient_row[9],
                    "Location": patient_row[10],
                    "Age": patient_row[11] or "N/A",
                    "Photo": "Available" if patient_row[12] else "Not uploaded",
                    "Doctor": doctor_name,
                    "Caretaker": caretaker_name,
                }
            )

        if patient_data:
            st.dataframe(
                patient_data,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No patients registered.")

    # ========================================================
    # DOCTORS - MANAGEMENT ONLY
    # ========================================================

    with admin_tabs[2]:

        doctors = conn.execute(
            """
            SELECT
                id, name, username, phone, email, location,
                qualification, qualification_number,
                qualification_status, account_status, age, photo, id_card_number, created_at
            FROM users
            WHERE role='doctor'
            ORDER BY name
            """
        ).fetchall()

        if doctors:
            st.dataframe(
                [
                    {
                        "ID": d[0],
                        "Doctor": d[1],
                        "Username": d[2],
                        "Phone": d[3],
                        "Email": d[4],
                        "Location": d[5],
                        "Qualification": d[6],
                        "Registration No.": d[7],
                        "Qualification Status": d[8],
                        "Account Status": d[9],
                        "Age": d[10] or "N/A",
                        "Photo": "Available" if d[11] else "Not uploaded",
                        "ID Card": d[12] or "Will be generated after approval",
                        "Created": d[13],
                    }
                    for d in doctors
                ],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No doctor registrations yet.")

    # ========================================================
    # CARETAKERS - MANAGEMENT
    # ========================================================

    with admin_tabs[3]:

        caretakers = conn.execute(
            """
            SELECT
                id, name, username, phone, email, location,
                qualification, account_status, age, photo, id_card_number, doctor_id_for_caretaker, created_at
            FROM users
            WHERE role='caretaker'
            ORDER BY name
            """
        ).fetchall()

        if caretakers:
            st.dataframe(
                [
                    {
                        "ID": c[0],
                        "Caretaker": c[1],
                        "Username": c[2],
                        "Phone": c[3],
                        "Email": c[4],
                        "Location": c[5],
                        "Care Role": c[6],
                        "Account Status": c[7],
                        "Age": c[8] or "N/A",
                        "Photo": "Available" if c[9] else "Not uploaded",
                        "ID Card": c[10] or "Will be generated on first login",
                        "Doctor ID": c[11] or "Not assigned",
                        "Created": c[12],
                    }
                    for c in caretakers
                ],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No caretaker registrations yet.")

    # ========================================================
    # VERIFICATION & MANAGEMENT
    # ========================================================

    with admin_tabs[4]:

        st.subheader("✅ Doctor Qualification Verification")

        pending_doctors = conn.execute(
            """
            SELECT
                id, name, username, phone, email, location,
                qualification, qualification_number,
                qualification_document, qualification_status,
                account_status, age, photo, created_at
            FROM users
            WHERE role='doctor'
            AND qualification_status='Pending'
            ORDER BY created_at DESC
            """
        ).fetchall()

        if not pending_doctors:
            st.success("No doctor qualifications are waiting for verification.")
        else:
            for d in pending_doctors:
                with st.expander(
                    f"🩺 {d[1]} — {d[6]} — Registration No. {d[7]}"
                ):
                    st.write(f"**Username:** {d[2]}")
                    st.write(f"**Phone:** {d[3]}")
                    st.write(f"**Email:** {d[4]}")
                    st.write(f"**Location:** {d[5]}")
                    st.write(f"**Qualification:** {d[6]}")
                    st.write(f"**Registration Number:** {d[7]}")
                    st.write(f"**Uploaded Document:** {d[8]}")
                    st.write(f"**Age:** {d[11] or 'N/A'}")
                    if d[12]:
                        st.image(normalize_image_for_streamlit(d[12]), caption="Doctor Photo", width=140)
                    st.write(f"**Submitted:** {d[13]}")

                    verify_col, reject_col = st.columns(2)

                    with verify_col:
                        if st.button(
                            "✅ Verify & Activate Doctor",
                            key=f"verify_doctor_{d[0]}",
                            use_container_width=True,
                            type="primary"
                        ):
                            card_no = f"MNE-DOC-{d[0]:05d}"
                            conn.execute(
                                """
                                UPDATE users
                                SET qualification_status='Verified',
                                    account_status='Active',
                                    id_card_number=?,
                                    id_card_created_at=?
                                WHERE id=? AND role='doctor'
                                """,
                                (card_no, datetime.now().isoformat(timespec="seconds"), d[0])
                            )
                            conn.commit()
                            announce(
                                "Doctor qualification verified and account activated.",
                                "English"
                            )
                            st.rerun()

                    with reject_col:
                        if st.button(
                            "❌ Reject Verification",
                            key=f"reject_doctor_{d[0]}",
                            use_container_width=True
                        ):
                            conn.execute(
                                """
                                UPDATE users
                                SET qualification_status='Rejected',
                                    account_status='Rejected'
                                WHERE id=? AND role='doctor'
                                """,
                                (d[0],)
                            )
                            conn.commit()
                            announce(
                                "Doctor qualification verification was rejected.",
                                "English"
                            )
                            st.rerun()

        st.divider()
        st.subheader("👥 Account Status Management")

        managed_users = conn.execute(
            """
            SELECT id, name, username, role, account_status, qualification_status
            FROM users
            WHERE role IN ('doctor', 'caretaker')
            ORDER BY role, name
            """
        ).fetchall()

        for u in managed_users:
            m1, m2, m3, m4 = st.columns([3, 2, 2, 2])
            m1.write(f"**{u[1]}** ({u[2]})")
            m2.write(u[3].title())
            m3.write(f"{u[4]} | Qualification: {u[5]}")
            with m4:
                # A doctor must be qualification-verified before the admin can
                # activate the account. This prevents an Active+Pending doctor
                # from being stuck in the assignment screen.
                if u[3] == "doctor" and u[5] != "Verified":
                    st.caption("Awaiting verification")
                else:
                    action_label = "Deactivate" if u[4] == "Active" else "Activate"
                    if st.button(
                        action_label,
                        key=f"status_{u[0]}",
                        use_container_width=True
                    ):
                        new_status = "Inactive" if u[4] == "Active" else "Active"
                        conn.execute(
                            "UPDATE users SET account_status=? WHERE id=? AND role IN ('doctor','caretaker')",
                            (new_status, u[0])
                        )
                        conn.commit()
                        st.rerun()

        st.divider()
        st.subheader("🔗 Provider Relationships — View Only")
        st.caption(
            "The administrator does not assign doctors, caretakers/nurses, or patients. "
            "Doctors register their own patients and caretakers/nurses, and caretakers register their own patients. "
            "Use this section only to review the relationships created by those registration flows."
        )

        relationship_rows = conn.execute(
            """
            SELECT
                p.name,
                p.username,
                d.name,
                c.name
            FROM users p
            LEFT JOIN users d
              ON d.id=p.doctor_id
             AND LOWER(TRIM(COALESCE(d.role, '')))='doctor'
            LEFT JOIN users c
              ON c.id=p.caretaker_id
             AND LOWER(TRIM(COALESCE(c.role, '')))='caretaker'
            WHERE LOWER(TRIM(COALESCE(p.role, '')))='patient'
            ORDER BY p.name
            """
        ).fetchall()

        st.markdown("### 📋 Current Patient Relationships")
        if relationship_rows:
            st.dataframe(
                [
                    {
                        "Patient": row[0],
                        "Username": row[1],
                        "Doctor": f"Dr. {row[2]}" if row[2] else "Not linked",
                        "Caretaker / Nurse": row[3] or "Not linked"
                    }
                    for row in relationship_rows
                ],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No patient relationships have been created yet.")

        caretaker_relationships = conn.execute(
            """
            SELECT
                c.name,
                c.username,
                d.name,
                d.qualification_status,
                d.account_status
            FROM users c
            LEFT JOIN users d
              ON d.id=c.doctor_id_for_caretaker
             AND LOWER(TRIM(COALESCE(d.role, '')))='doctor'
            WHERE LOWER(TRIM(COALESCE(c.role, '')))='caretaker'
            ORDER BY c.name
            """
        ).fetchall()

        st.markdown("### 🔗 Current Caretaker / Nurse → Doctor Relationships")
        if caretaker_relationships:
            st.dataframe(
                [
                    {
                        "Caretaker / Nurse": row[0],
                        "Username": row[1],
                        "Doctor": f"Dr. {row[2]}" if row[2] else "Not linked",
                        "Doctor Qualification": row[3] or "N/A",
                        "Doctor Account": row[4] or "N/A"
                    }
                    for row in caretaker_relationships
                ],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No caretaker / nurse relationships have been created yet.")

    # ========================================================
    # ALL SESSIONS
    # ========================================================

    with admin_tabs[5]:

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
            st.info("No sessions available.")

    # ========================================================
    # ALL REPORTS
    # ========================================================

    with admin_tabs[6]:

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
                    st.write(f"Doctor: Dr. {report[2]}")
                    st.write(f"Date: {report[0]}")
                    st.write(report[4])
        else:
            st.info("No reports available.")

    with admin_tabs[7]:
        st.subheader("📜 Medical Treatment Certificates")
        certificates = conn.execute(
            """SELECT tc.id, tc.certificate_no, p.name, d.name, c.name,
                      tc.treatment_title, tc.treatment_start, tc.treatment_end, tc.issued_at
               FROM treatment_certificates tc
               JOIN users p ON p.id=tc.patient_id
               JOIN users d ON d.id=tc.doctor_id
               LEFT JOIN users c ON c.id=tc.caretaker_id
               ORDER BY tc.id DESC"""
        ).fetchall()
        if certificates:
            for cert in certificates:
                st.write(f"**{cert[2]}** — {cert[5]} — Certificate {cert[1]}")
                pdf = make_treatment_certificate_pdf(cert[0])
                if pdf:
                    st.download_button("⬇️ Download Certificate", pdf, file_name=f"{cert[1]}.pdf", mime="application/pdf", key=f"admin_cert_{cert[0]}")
        else:
            st.info("No treatment certificates issued yet.")

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

    doctor_profile = conn.execute(
        """
        SELECT
            phone, email, location, qualification,
            qualification_number, qualification_status,
            account_status, age, photo, id_card_number, id_card_created_at
        FROM users
        WHERE id=? AND role='doctor'
        """,
        (user_id,)
    ).fetchone()

    doctor_tabs = st.tabs(
        [
            "🏠 Overview",
            "📝 Register Patient / Caretaker",
            "👥 My Patients",
            "📊 Patient Performance",
            "📄 Send Report",
            "👤 My Profile"
        ]
    )

    assigned_patients = conn.execute(
        """
        SELECT
            id, name, username, language, baseline,
            phone, email, location, adaptive_difficulty, photo
        FROM users
        WHERE role='patient'
        AND doctor_id=?
        ORDER BY name
        """,
        (user_id,)
    ).fetchall()

    # ========================================================
    # DOCTOR OVERVIEW
    # ========================================================

    with doctor_tabs[0]:

        c1, c2, c3 = st.columns(3)
        c1.metric("My Patients", len(assigned_patients))
        c2.metric("Your Role", "Doctor")
        c3.metric(
            "Qualification",
            doctor_profile[4] if doctor_profile and doctor_profile[5] == "Verified" else "Pending"
        )

        st.success(
            "✅ Doctor account is active. Patient data is restricted to patients created/linked under your account."
        )

        st.info(
            "You can register patients directly from the Register Patient / Caretaker tab. Patients you register are automatically linked to your account."
        )

        st.warning(
            "🎮 Cognitive games are not available for doctor accounts."
        )

    # ========================================================
    # DOCTOR REGISTRATION OF PATIENTS / CARETAKERS
    # ========================================================

    with doctor_tabs[1]:
        st.subheader("📝 Register Patient or Caretaker / Nurse")
        st.info(
            "You can create patient accounts and caretaker/nurse accounts directly from your doctor portal. "
            "A patient registered here is automatically linked to you. "
            "A caretaker/nurse registered here is automatically linked to you."
        )

        registration_type = st.radio(
            "What would you like to register?",
            ["👤 Patient", "🤝 Caretaker / Nurse"],
            horizontal=True,
            key="doctor_registration_type"
        )

        if registration_type == "👤 Patient":
            with st.form("doctor_register_patient_form"):
                dp_name = st.text_input("Patient Full Name", key="doctor_patient_name")
                dp_username = st.text_input("Patient Username", key="doctor_patient_username")
                dp_password = st.text_input("Password", type="password", key="doctor_patient_password")
                dp_confirm = st.text_input("Confirm Password", type="password", key="doctor_patient_confirm")
                dp_phone = st.text_input("Phone Number (optional)", key="doctor_patient_phone")
                dp_email = st.text_input("Email ID (optional)", key="doctor_patient_email")
                dp_location = st.text_input("Location (optional)", key="doctor_patient_location")
                dp_dob = st.date_input(
                    "Date of Birth",
                    value=date(1990, 1, 1),
                    min_value=date(1900, 1, 1),
                    max_value=date.today(),
                    key="doctor_patient_dob"
                )
                dp_photo = st.file_uploader(
                    "Patient Photo (optional)",
                    type=["png", "jpg", "jpeg"],
                    key="doctor_patient_photo"
                )
                dp_language = st.selectbox(
                    "Language",
                    list(LANGUAGES.keys()),
                    key="doctor_patient_language"
                )

                save_patient = st.form_submit_button(
                    "👤 Create Patient Account",
                    type="primary",
                    use_container_width=True
                )

            if save_patient:
                if not dp_name.strip():
                    st.error("Please enter the patient's name.")
                elif not dp_username.strip():
                    st.error("Please enter a username.")
                elif len(dp_password) < 6:
                    st.error("Password must contain at least 6 characters.")
                elif dp_password != dp_confirm:
                    st.error("Passwords do not match.")
                elif dp_phone.strip() and not phone_is_valid(dp_phone):
                    st.error("Please enter a valid phone number.")
                elif dp_email.strip() and not email_is_valid(dp_email):
                    st.error("Please enter a valid email address.")
                else:
                    existing = conn.execute(
                        "SELECT id FROM users WHERE LOWER(username)=LOWER(?)",
                        (dp_username.strip(),)
                    ).fetchone()

                    if existing:
                        st.error("Username already exists.")
                    else:
                        conn.execute(
                            """
                            INSERT INTO users(
                                name, username, password_hash, language, baseline,
                                role, adaptive_difficulty, phone, email, location,
                                date_of_birth, age, photo, doctor_id, caretaker_id,
                                account_status, created_by_id, created_at
                            )
                            VALUES(
                                ?, ?, ?, ?, 0, 'patient', 1, ?, ?, ?, ?, ?, ?, ?, NULL,
                                'Active', ?, ?
                            )
                            """,
                            (
                                dp_name.strip(),
                                dp_username.strip(),
                                hash_password(dp_password),
                                dp_language,
                                dp_phone.strip(),
                                dp_email.strip(),
                                normalize_location(dp_location),
                                dp_dob.isoformat(),
                                calculate_age_from_dob(dp_dob),
                                dp_photo.getvalue() if dp_photo else None,
                                user_id,
                                user_id,
                                datetime.now().isoformat(timespec="seconds")
                            )
                        )
                        conn.commit()
                        st.success(
                            f"Patient account created successfully and linked to Dr. {name}."
                        )
                        announce(
                            f"Patient {dp_name.strip()} has been registered successfully.",
                            dp_language
                        )

        else:
            with st.form("doctor_register_caretaker_form"):
                dc_name = st.text_input("Caretaker / Nurse Full Name", key="doctor_caretaker_name")
                dc_username = st.text_input("Caretaker / Nurse Username", key="doctor_caretaker_username")
                dc_password = st.text_input("Password", type="password", key="doctor_caretaker_password")
                dc_confirm = st.text_input("Confirm Password", type="password", key="doctor_caretaker_confirm")
                dc_phone = st.text_input("Phone Number", key="doctor_caretaker_phone")
                dc_email = st.text_input("Email ID", key="doctor_caretaker_email")
                dc_location = st.text_input("Location", key="doctor_caretaker_location")
                dc_photo = st.file_uploader(
                    "Caretaker / Nurse Photo",
                    type=["png", "jpg", "jpeg"],
                    key="doctor_caretaker_photo"
                )
                dc_relationship = st.text_input(
                    "Relationship / Care Role",
                    placeholder="Example: Family Caretaker, Home Care Assistant",
                    key="doctor_caretaker_relationship"
                )
                dc_language = st.selectbox(
                    "Language",
                    list(LANGUAGES.keys()),
                    key="doctor_caretaker_language"
                )

                save_caretaker = st.form_submit_button(
                    "🤝 Create Caretaker / Nurse Account",
                    type="primary",
                    use_container_width=True
                )

            if save_caretaker:
                if not dc_name.strip():
                    st.error("Please enter the caretaker's name.")
                elif not dc_username.strip():
                    st.error("Please enter a username.")
                elif len(dc_password) < 6:
                    st.error("Password must contain at least 6 characters.")
                elif dc_password != dc_confirm:
                    st.error("Passwords do not match.")
                elif not phone_is_valid(dc_phone):
                    st.error("Please enter a valid phone number.")
                elif not email_is_valid(dc_email):
                    st.error("Please enter a valid email address.")
                elif not normalize_location(dc_location):
                    st.error("Please enter the caretaker's location.")
                elif dc_photo is None:
                    st.error("Please upload the caretaker/nurse photo.")
                else:
                    existing = conn.execute(
                        "SELECT id FROM users WHERE LOWER(username)=LOWER(?)",
                        (dc_username.strip(),)
                    ).fetchone()

                    if existing:
                        st.error("Username already exists.")
                    else:
                        conn.execute(
                            """
                            INSERT INTO users(
                                name, username, password_hash, language, baseline,
                                role, adaptive_difficulty, phone, email, location,
                                photo, qualification, qualification_status,
                                account_status, doctor_id_for_caretaker,
                                created_by_id, created_at
                            )
                            VALUES(
                                ?, ?, ?, ?, 0, 'caretaker', 1, ?, ?, ?, ?, ?,
                                'Not Required', 'Active', ?, ?, ?
                            )
                            """,
                            (
                                dc_name.strip(),
                                dc_username.strip(),
                                hash_password(dc_password),
                                dc_language,
                                dc_phone.strip(),
                                dc_email.strip(),
                                normalize_location(dc_location),
                                dc_photo.getvalue(),
                                dc_relationship.strip(),
                                user_id,
                                user_id,
                                datetime.now().isoformat(timespec="seconds")
                            )
                        )
                        conn.commit()
                        st.success(
                            f"Caretaker / nurse account created successfully and linked to Dr. {name}."
                        )
                        announce(
                            f"Caretaker {dc_name.strip()} has been registered successfully.",
                            dc_language
                        )

    # ========================================================
    # DOCTOR OWN PATIENTS
    # ========================================================

    with doctor_tabs[2]:

        if assigned_patients:
            st.dataframe(
                [
                    {
                        "Patient": p[1],
                        "Username": p[2],
                        "Language": p[3],
                        "Baseline": p[4],
                        "Phone": p[5],
                        "Email": p[6],
                        "Location": p[7],
                        "Photo": "Available" if p[9] else "Not uploaded",
                        "Difficulty": p[8]
                    }
                    for p in assigned_patients
                ],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No patients have been added to your account yet.")

    # ========================================================
    # DOCTOR PATIENT PERFORMANCE
    # ========================================================

    with doctor_tabs[3]:

        if assigned_patients:

            patient_map = {
                f"{p[1]} ({p[2]})": p[0]
                for p in assigned_patients
            }

            selected_patient_name = st.selectbox(
                "Select Patient",
                list(patient_map.keys()),
                key="doctor_view_patient"
            )

            selected_patient_id = patient_map[selected_patient_name]

            # Server-side privacy check.
            if not provider_can_manage_patient(
                user_id,
                "doctor",
                selected_patient_id
            ):
                st.error("You are not authorized to access this patient.")
            else:

                patient_data = conn.execute(
                    """
                    SELECT
                        id, name, username, language,
                        baseline, adaptive_difficulty,
                        phone, email, location
                    FROM users
                    WHERE id=?
                    AND role='patient'
                    AND doctor_id=?
                    """,
                    (selected_patient_id, user_id)
                ).fetchone()

                if patient_data:

                    st.subheader(f"👤 {patient_data[1]}")

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Baseline", f"{patient_data[4]:.1f}")
                    c2.metric("Difficulty", patient_data[5])

                    sessions = conn.execute(
                        """
                        SELECT game, score, difficulty, created_at
                        FROM sessions
                        WHERE user_id=?
                        ORDER BY id DESC
                        """,
                        (selected_patient_id,)
                    ).fetchall()

                    scores = [float(s[1]) for s in sessions]
                    average_score = sum(scores) / len(scores) if scores else 0
                    best_score = max(scores) if scores else 0

                    c3.metric("Average Score", f"{average_score:.1f}")
                    st.metric("Best Score", f"{best_score:.1f}")

                    st.write(f"**Phone:** {patient_data[6]}")
                    st.write(f"**Email:** {patient_data[7]}")
                    st.write(f"**Location:** {patient_data[8]}")

                    if sessions:
                        st.subheader("📊 Game Performance")
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

                        progress_df = pd.DataFrame(
                            [
                                {
                                    "Session": idx,
                                    "Score": float(s[1])
                                }
                                for idx, s in enumerate(reversed(sessions[-5:]), start=1)
                            ]
                        )
                        if not progress_df.empty:
                            st.line_chart(
                                progress_df.set_index("Session"),
                                y="Score",
                                use_container_width=True
                            )
                    else:
                        st.info("No game sessions recorded.")

    # ========================================================
    # DOCTOR REPORTS
    # ========================================================

    with doctor_tabs[4]:

        if assigned_patients:

            patient_map = {
                f"{p[1]} ({p[2]})": p[0]
                for p in assigned_patients
            }

            selected_report_patient = st.selectbox(
                "Select Patient",
                list(patient_map.keys()),
                key="doctor_report_patient"
            )

            report_patient_id = patient_map[selected_report_patient]

            if provider_can_manage_patient(
                user_id,
                "doctor",
                report_patient_id
            ):

                sessions = conn.execute(
                    "SELECT score FROM sessions WHERE user_id=?",
                    (report_patient_id,)
                ).fetchall()

                report_scores = [float(row[0]) for row in sessions]
                report_average = sum(report_scores) / len(report_scores) if report_scores else 0
                report_best = max(report_scores) if report_scores else 0

                st.write(f"Completed sessions: **{len(report_scores)}**")
                st.write(f"Average score: **{report_average:.1f}**")
                st.write(f"Best score: **{report_best:.1f}**")

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

                    if not report_text.strip():
                        st.error("Report cannot be empty.")
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
                            VALUES(?, ?, ?, ?, ?, 'Sent')
                            """,
                            (
                                report_patient_id,
                                user_id,
                                report_title.strip(),
                                report_text.strip(),
                                datetime.now().isoformat(timespec="seconds")
                            )
                        )
                        conn.commit()
                        announce(
                            "Overall performance report sent successfully to the patient.",
                            "English"
                        )
                        st.rerun()

                st.divider()
                st.subheader("📜 Issue Medical Treatment Certificate")
                treatment_title = st.text_input("Treatment / Care Title", key="treatment_cert_title")
                treatment_summary = st.text_area("Treatment Summary", key="treatment_cert_summary", height=140)
                treatment_start = st.date_input("Treatment Start Date", value=date.today(), key="treatment_cert_start")
                treatment_end = st.date_input("Treatment End Date", value=date.today(), key="treatment_cert_end")
                if st.button("📜 Issue Treatment Certificate", type="primary", key="issue_treatment_certificate"):
                    if not treatment_title.strip() or not treatment_summary.strip():
                        st.error("Please enter the treatment title and summary.")
                    elif treatment_end < treatment_start:
                        st.error("Treatment end date cannot be before the start date.")
                    else:
                        cert_no = f"MNE-TC-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
                        conn.execute(
                            """INSERT INTO treatment_certificates(
                               certificate_no, patient_id, doctor_id, caretaker_id, treatment_title,
                               treatment_summary, treatment_start, treatment_end, issued_at
                               ) VALUES(?,?,?,?,?,?,?,?,?)""",
                            (cert_no, report_patient_id, user_id,
                             conn.execute("SELECT caretaker_id FROM users WHERE id=? AND role='patient'", (report_patient_id,)).fetchone()[0],
                             treatment_title.strip(), treatment_summary.strip(), treatment_start.isoformat(), treatment_end.isoformat(),
                             datetime.now().isoformat(timespec="seconds"))
                        )
                        conn.commit()
                        new_cert_id = conn.execute("SELECT id FROM treatment_certificates WHERE certificate_no=?", (cert_no,)).fetchone()[0]
                        pdf = make_treatment_certificate_pdf(new_cert_id)
                        st.success(f"Treatment certificate {cert_no} issued successfully.")
                        st.download_button("⬇️ Download Treatment Certificate", pdf, file_name=f"{cert_no}.pdf", mime="application/pdf", key=f"doctor_new_cert_{new_cert_id}")

        else:
            st.info("Add patients before sending reports.")

    # ========================================================
    # DOCTOR PROFILE
    # ========================================================

    with doctor_tabs[5]:

        if doctor_profile:
            st.write(f"**Phone:** {doctor_profile[0]}")
            st.write(f"**Email:** {doctor_profile[1]}")
            st.write(f"**Location:** {doctor_profile[2]}")
            st.write(f"**Qualification:** {doctor_profile[3]}")
            st.write(f"**Registration Number:** {doctor_profile[4]}")
            st.write(f"**Qualification Verification:** {doctor_profile[5]}")
            st.write(f"**Account Status:** {doctor_profile[6]}")
            st.write(f"**Age:** {doctor_profile[7] or 'N/A'}")
            if doctor_profile[8]:
                st.image(normalize_image_for_streamlit(doctor_profile[8]), caption="Doctor Photo", width=160)
            if doctor_profile[6] == "Active" and doctor_profile[5] == "Verified":
                if not doctor_profile[9]:
                    card_no = f"MNE-DOC-{user_id:05d}"
                    conn.execute("UPDATE users SET id_card_number=?, id_card_created_at=? WHERE id=?", (card_no, datetime.now().isoformat(timespec="seconds"), user_id))
                    conn.commit()
                    doctor_profile = (*doctor_profile[:9], card_no, datetime.now().isoformat(timespec="seconds"))
                card_pdf = make_id_card_pdf(user_id, "doctor")
                st.success(f"🪪 Doctor ID Card ready: {doctor_profile[9]}")
                st.download_button("⬇️ Download Doctor ID Card", card_pdf, file_name=f"{doctor_profile[9]}.pdf", mime="application/pdf", key="doctor_id_card_download")

    st.divider()

    if st.button(
        "🚪 Logout",
        key="doctor_logout"
    ):
        st.session_state.clear()
        st.rerun()

    st.stop()


# ============================================================
# CARETAKER DASHBOARD
# ============================================================

if role == "caretaker":

    st.title(
        f"🤝 Caretaker Portal — {name}"
    )

    caretaker_profile = conn.execute(
        """
        SELECT phone, email, location, qualification, account_status, photo, doctor_id_for_caretaker, id_card_number
        FROM users
        WHERE id=? AND role='caretaker'
        """,
        (user_id,)
    ).fetchone()

    caretaker_tabs = st.tabs(
        [
            "🏠 Overview",
            "📝 Register Patient",
            "👥 My Patients",
            "📊 Patient Performance",
            "🔔 Patient Reminders",
            "📜 Treatment Certificates",
            "👤 My Profile"
        ]
    )

    own_patients = conn.execute(
        """
        SELECT
            id, name, username, language, baseline,
            phone, email, location, adaptive_difficulty, photo
        FROM users
        WHERE role='patient'
        AND caretaker_id=?
        ORDER BY name
        """,
        (user_id,)
    ).fetchall()

    with caretaker_tabs[0]:

        c1, c2 = st.columns(2)
        c1.metric("My Patients", len(own_patients))
        c2.metric("Your Role", "Caretaker")

        st.success(
            "✅ Caretaker access is limited to patients linked to your account."
        )
        assigned_doctor = None
        if caretaker_profile and caretaker_profile[6]:
            assigned_doctor = conn.execute("SELECT name FROM users WHERE id=? AND role='doctor'", (caretaker_profile[6],)).fetchone()
        st.info(
            f"Assigned doctor: **Dr. {assigned_doctor[0]}**" if assigned_doctor else "No doctor relationship is currently linked to your account. A doctor can create your caretaker relationship from the doctor's registration portal."
        )
        st.warning(
            "🎮 Cognitive games are available only to patient accounts."
        )

    with caretaker_tabs[1]:
        st.subheader("📝 Register Patient")
        st.info(
            "You can create patient accounts directly from your caretaker portal. "
            "The new patient is automatically linked to your caretaker account. "
            "If your caretaker account is linked to a doctor, the patient is also automatically linked to that doctor."
        )

        linked_doctor = None
        if caretaker_profile and caretaker_profile[6]:
            linked_doctor = conn.execute(
                """
                SELECT id, name
                FROM users
                WHERE id=? AND role='doctor'
                """,
                (caretaker_profile[6],)
            ).fetchone()

        if not linked_doctor:
            st.warning(
                "Your caretaker account is not currently linked to a doctor. "
                "You may still register a patient, but the patient will remain linked only to you until a doctor relationship exists."
            )

        with st.form("caretaker_register_patient_form"):
            cp_name = st.text_input("Patient Full Name", key="caretaker_patient_name")
            cp_username = st.text_input("Patient Username", key="caretaker_patient_username")
            cp_password = st.text_input("Password", type="password", key="caretaker_patient_password")
            cp_confirm = st.text_input("Confirm Password", type="password", key="caretaker_patient_confirm")
            cp_phone = st.text_input("Phone Number (optional)", key="caretaker_patient_phone")
            cp_email = st.text_input("Email ID (optional)", key="caretaker_patient_email")
            cp_location = st.text_input("Location (optional)", key="caretaker_patient_location")
            cp_dob = st.date_input(
                "Date of Birth",
                value=date(1990, 1, 1),
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                key="caretaker_patient_dob"
            )
            cp_photo = st.file_uploader(
                "Patient Photo (optional)",
                type=["png", "jpg", "jpeg"],
                key="caretaker_patient_photo"
            )
            cp_language = st.selectbox(
                "Language",
                list(LANGUAGES.keys()),
                key="caretaker_patient_language"
            )

            save_caretaker_patient = st.form_submit_button(
                "👤 Create Patient Account",
                type="primary",
                use_container_width=True
            )

        if save_caretaker_patient:
            if not cp_name.strip():
                st.error("Please enter the patient's name.")
            elif not cp_username.strip():
                st.error("Please enter a username.")
            elif len(cp_password) < 6:
                st.error("Password must contain at least 6 characters.")
            elif cp_password != cp_confirm:
                st.error("Passwords do not match.")
            elif cp_phone.strip() and not phone_is_valid(cp_phone):
                st.error("Please enter a valid phone number.")
            elif cp_email.strip() and not email_is_valid(cp_email):
                st.error("Please enter a valid email address.")
            else:
                existing = conn.execute(
                    "SELECT id FROM users WHERE LOWER(username)=LOWER(?)",
                    (cp_username.strip(),)
                ).fetchone()

                if existing:
                    st.error("Username already exists.")
                else:
                    doctor_id_for_patient = linked_doctor[0] if linked_doctor else None
                    conn.execute(
                        """
                        INSERT INTO users(
                            name, username, password_hash, language, baseline,
                            role, adaptive_difficulty, phone, email, location,
                            date_of_birth, age, photo, doctor_id, caretaker_id,
                            account_status, created_by_id, created_at
                        )
                        VALUES(
                            ?, ?, ?, ?, 0, 'patient', 1, ?, ?, ?, ?, ?, ?, ?, ?,
                            'Active', ?, ?
                        )
                        """,
                        (
                            cp_name.strip(),
                            cp_username.strip(),
                            hash_password(cp_password),
                            cp_language,
                            cp_phone.strip(),
                            cp_email.strip(),
                            normalize_location(cp_location),
                            cp_dob.isoformat(),
                            calculate_age_from_dob(cp_dob),
                            cp_photo.getvalue() if cp_photo else None,
                            doctor_id_for_patient,
                            user_id,
                            user_id,
                            datetime.now().isoformat(timespec="seconds")
                        )
                    )
                    conn.commit()
                    if linked_doctor:
                        success_message = (
                            f"Patient account created successfully and linked to you and Dr. {linked_doctor[1]}."
                        )
                    else:
                        success_message = (
                            "Patient account created successfully and linked to your caretaker account."
                        )
                    st.success(success_message)
                    announce(
                        f"Patient {cp_name.strip()} has been registered successfully.",
                        cp_language
                    )

    with caretaker_tabs[2]:

        if own_patients:
            st.dataframe(
                [
                    {
                        "Patient": p[1],
                        "Username": p[2],
                        "Language": p[3],
                        "Baseline": p[4],
                        "Phone": p[5],
                        "Email": p[6],
                        "Location": p[7],
                        "Photo": "Available" if p[9] else "Not uploaded",
                        "Difficulty": p[8]
                    }
                    for p in own_patients
                ],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No patients have been added to your caretaker account yet.")

    with caretaker_tabs[3]:

        if own_patients:

            patient_map = {
                f"{p[1]} ({p[2]})": p[0]
                for p in own_patients
            }

            selected_patient_name = st.selectbox(
                "Select Patient",
                list(patient_map.keys()),
                key="caretaker_view_patient"
            )

            selected_patient_id = patient_map[selected_patient_name]

            if not provider_can_manage_patient(
                user_id,
                "caretaker",
                selected_patient_id
            ):
                st.error("You are not authorized to access this patient.")
            else:

                patient_data = conn.execute(
                    """
                    SELECT
                        id, name, username, language,
                        baseline, adaptive_difficulty,
                        phone, email, location
                    FROM users
                    WHERE id=?
                    AND role='patient'
                    AND caretaker_id=?
                    """,
                    (selected_patient_id, user_id)
                ).fetchone()

                if patient_data:
                    st.subheader(f"👤 {patient_data[1]}")

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Baseline", f"{patient_data[4]:.1f}")
                    c2.metric("Difficulty", patient_data[5])

                    sessions = conn.execute(
                        """
                        SELECT game, score, difficulty, created_at
                        FROM sessions
                        WHERE user_id=?
                        ORDER BY id DESC
                        """,
                        (selected_patient_id,)
                    ).fetchall()

                    scores = [float(s[1]) for s in sessions]
                    c3.metric(
                        "Average Score",
                        f"{(sum(scores) / len(scores)) if scores else 0:.1f}"
                    )
                    st.metric(
                        "Best Score",
                        f"{max(scores) if scores else 0:.1f}"
                    )

                    st.write(f"**Phone:** {patient_data[6]}")
                    st.write(f"**Email:** {patient_data[7]}")
                    st.write(f"**Location:** {patient_data[8]}")

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
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No game sessions recorded.")

    with caretaker_tabs[4]:

        if own_patients:
            patient_map = {
                f"{p[1]} ({p[2]})": p[0]
                for p in own_patients
            }
            selected_reminder_patient = st.selectbox(
                "Select Patient",
                list(patient_map.keys()),
                key="caretaker_reminder_patient"
            )
            reminder_patient_id = patient_map[selected_reminder_patient]

            if provider_can_manage_patient(
                user_id,
                "caretaker",
                reminder_patient_id
            ):
                patient_reminders = conn.execute(
                    """
                    SELECT id, title, due_time, status
                    FROM reminders
                    WHERE user_id=?
                    ORDER BY id DESC
                    """,
                    (reminder_patient_id,)
                ).fetchall()

                if patient_reminders:
                    st.dataframe(
                        [
                            {
                                "Reminder": r[1],
                                "Due": r[2],
                                "Status": r[3]
                            }
                            for r in patient_reminders
                        ],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No reminders recorded for this patient.")

    with caretaker_tabs[5]:

        st.subheader("📜 Treatment Certificates")
        certs = conn.execute(
            """SELECT id, certificate_no, treatment_title, treatment_start, treatment_end, issued_at
               FROM treatment_certificates WHERE patient_id IN (SELECT id FROM users WHERE role='patient' AND caretaker_id=?)
               ORDER BY id DESC""", (user_id,)
        ).fetchall()
        if certs:
            for cert in certs:
                st.write(f"**{cert[2]}** — {cert[1]} ({cert[3]} to {cert[4]})")
                pdf = make_treatment_certificate_pdf(cert[0])
                if pdf:
                    st.download_button("⬇️ Download Certificate", pdf, file_name=f"{cert[1]}.pdf", mime="application/pdf", key=f"care_cert_{cert[0]}")
        else:
            st.info("No treatment certificates available for your assigned patients.")

    with caretaker_tabs[6]:

        st.write(f"**Phone:** {caretaker_profile[0] if caretaker_profile else ''}")
        st.write(f"**Email:** {caretaker_profile[1] if caretaker_profile else ''}")
        st.write(f"**Location:** {caretaker_profile[2] if caretaker_profile else ''}")
        st.write(f"**Care Role:** {caretaker_profile[3] if caretaker_profile else ''}")
        st.write(f"**Account Status:** {caretaker_profile[4] if caretaker_profile else ''}")
        st.write(f"**Assigned Doctor:** {('Dr. ' + conn.execute("SELECT name FROM users WHERE id=? AND role='doctor'", (caretaker_profile[6],)).fetchone()[0]) if caretaker_profile and caretaker_profile[6] and conn.execute("SELECT name FROM users WHERE id=? AND role='doctor'", (caretaker_profile[6],)).fetchone() else 'Not assigned'}")
        if caretaker_profile and caretaker_profile[5]:
            st.image(normalize_image_for_streamlit(caretaker_profile[5]), caption="Caretaker / Nurse Photo", width=160)
        if caretaker_profile and caretaker_profile[4] == "Active":
            if not caretaker_profile[7]:
                card_no=f"MNE-CARE-{user_id:05d}"
                conn.execute("UPDATE users SET id_card_number=?, id_card_created_at=? WHERE id=?", (card_no, datetime.now().isoformat(timespec="seconds"), user_id))
                conn.commit()
                caretaker_profile = (*caretaker_profile[:7], card_no)
            card_pdf=make_id_card_pdf(user_id, "caretaker")
            st.success(f"🪪 Caretaker ID Card ready: {caretaker_profile[7]}")
            st.download_button("⬇️ Download Caretaker ID Card", card_pdf, file_name=f"{caretaker_profile[7]}.pdf", mime="application/pdf", key="caretaker_id_card_download")

    st.divider()

    if st.button(
        "🚪 Logout",
        key="caretaker_logout"
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
        adaptive_difficulty,
        caretaker_id,
        phone,
        email,
        location,
        age,
        photo
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
caretaker_id = patient[8] if len(patient) > 8 else None
phone = patient[9] if len(patient) > 9 else ""
email = patient[10] if len(patient) > 10 else ""
location = patient[11] if len(patient) > 11 else ""
patient_age = patient[12] if len(patient) > 12 else 0
patient_photo = patient[13] if len(patient) > 13 else None
st.session_state.caretaker_id = caretaker_id


# ============================================================
# PATIENT PROFILE / ASSIGNMENTS
# ============================================================

with st.expander("👤 My Profile & Care Team", expanded=False):
    c1, c2 = st.columns([1, 3])
    with c1:
        if patient_photo:
            st.image(normalize_image_for_streamlit(patient_photo), caption="Patient Photo", width=150)
        else:
            st.info("No patient photo uploaded.")
    with c2:
        st.write(f"**Name:** {name}")
        st.write(f"**Age:** {patient_age or 'N/A'}")
        doctor_row = conn.execute("SELECT name, phone, email, qualification FROM users WHERE id=? AND role='doctor'", (doctor_id,)).fetchone() if doctor_id else None
        caretaker_row = conn.execute("SELECT name, phone, email FROM users WHERE id=? AND role='caretaker'", (caretaker_id,)).fetchone() if caretaker_id else None
        st.write(f"**Doctor:** {('Dr. ' + doctor_row[0]) if doctor_row else 'Not assigned by admin'}")
        st.write(f"**Caretaker / Nurse:** {caretaker_row[0] if caretaker_row else 'Not assigned by admin'}")

# ============================================================
# PATIENT TREATMENT CERTIFICATES
# ============================================================

certificates = conn.execute(
    "SELECT id, certificate_no, treatment_title, treatment_start, treatment_end, issued_at FROM treatment_certificates WHERE patient_id=? ORDER BY id DESC",
    (user_id,)
).fetchall()
if certificates:
    with st.expander("📜 Medical Treatment Certificates", expanded=False):
        for cert in certificates:
            st.write(f"**{cert[2]}** — {cert[1]} — {cert[3]} to {cert[4]}")
            pdf = make_treatment_certificate_pdf(cert[0])
            if pdf:
                st.download_button("⬇️ Download Certificate", pdf, file_name=f"{cert[1]}.pdf", mime="application/pdf", key=f"patient_cert_{cert[0]}")

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
# VOICE COMMAND HELPERS
# ============================================================
VOICE_ALIASES = {
    "logout": ["logout", "log out", "exit", "sign out", "लॉगआउट", "लॉग आउट", "выйти", "выход"],
    "games": ["game", "games", "play", "cognitive", "cognitive game", "खेल", "गेम", "खेळ", "игра", "игры"],
    "reminders": ["reminder", "reminders", "set reminder", "add reminder", "remind me", "रिमाइंडर", "स्मरणपत्र", "напоминание", "напоминания"],
    "reports": ["report", "reports", "open report", "open reports", "रिपोर्ट", "अहवाल", "отчёт", "отчет", "отчеты"],
    "history": ["history", "performance", "my history", "मेरा इतिहास", "इतिहास", "माझा इतिहास", "история"],
    "details": ["details", "profile", "my data", "my details", "मेरी जानकारी", "माहिती", "мои данные", "профиль"],
    "home": ["home", "dashboard", "go home", "main page", "होम", "मुख्यपृष्ठ", "домой", "главная"]
}

def clean_voice_command(command):
    if not command:
        return ""
    command = command.lower().strip()
    command = re.sub(r"[^\w\s:/.-]", " ", command, flags=re.UNICODE)
    return re.sub(r"\s+", " ", command).strip()

def command_matches(command, action):
    command = clean_voice_command(command)
    return any(command == alias or alias in command for alias in VOICE_ALIASES.get(action, []))


# ============================================================
# PATIENT SIDEBAR
# ============================================================

with st.sidebar:

    if APP_LOGO is not None:
        st.image(APP_LOGO, width=155)
    st.markdown(
        f"## 🧠 {APP_NAME}"
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

        st.caption("Click 🎤, speak clearly, then click ⏹️ to stop.")

        audio_data = mic_recorder(
            start_prompt="🎤 Start Listening",
            stop_prompt="⏹️ Stop Listening",
            just_once=True,
            key="patient_voice_recorder"
        )

        if audio_data:

            command, voice_error = recognize_voice(
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

                st.caption(f'🎤 I heard: "{command}"')
                command = clean_voice_command(command)

                # =================================================
                # LOGOUT
                # =================================================

                if command_matches(command, "logout"):

                    queue_voice(
                        "Logging out now.",
                        language
                    )

                    st.session_state.logged_in = False

                    st.rerun()

                # =================================================
                # GAMES
                # =================================================

                elif command_matches(command, "games"):

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

                elif command_matches(command, "reminders") or "set time" in command or "set a time" in command:

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

                elif command_matches(command, "reports"):

                    st.session_state.page = "reports"

                    queue_voice(
                        "Opening your reports.",
                        language
                    )

                    st.rerun()

                # =================================================
                # HISTORY
                # =================================================

                elif command_matches(command, "history"):

                    st.session_state.page = "history"

                    queue_voice(
                        "Opening your performance history.",
                        language
                    )

                    st.rerun()

                # =================================================
                # DETAILS
                # =================================================

                elif command_matches(command, "details"):

                    st.session_state.page = "details"

                    queue_voice(
                        "Opening your details.",
                        language
                    )

                    st.rerun()

                # =================================================
                # HOME
                # =================================================

                elif command_matches(command, "home"):

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

                if voice_error:
                    st.warning(f"🎤 {voice_error}")

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

# ------------------------------------------------------------
# PAGE-BY-PAGE SIMPLE INSTRUCTIONS
# ------------------------------------------------------------
# The user sees the instructions for the page they are currently using.
page_instruction_keys = {
    "home": "home",
    "games": "games",
    "reminders": "reminders",
    "history": "history",
    "details": "details",
    "reports": "reports",
}
if selected_page in page_instruction_keys:
    show_instructions(
        page_instruction_keys[selected_page],
        language,
        expanded=False
    )


# ============================================================
# MULTI-ROUND GAME SETTINGS
# ============================================================

GAME_ROUNDS_BY_DIFFICULTY = {
    1: 15,
    2: 18,
    3: 20,
}


def reset_memory_game():
    st.session_state.memory_sequence = None
    st.session_state.memory_round = 0
    st.session_state.memory_total_score = 0.0
    st.session_state.memory_start_time = None
    st.session_state.memory_answer_phase = False


def reset_pattern_game():
    st.session_state.pattern_sequence = None
    st.session_state.pattern_round = 0
    st.session_state.pattern_total_score = 0.0


def reset_attention_game():
    st.session_state.reaction_target = None
    st.session_state.attention_round = 0
    st.session_state.attention_total_score = 0.0


def reset_image_memory_game():
    """Reset all state for the patient-only Image Recognition game."""
    st.session_state.image_memory_round = 0
    st.session_state.image_memory_total_score = 0.0
    st.session_state.image_memory_sequence = []
    st.session_state.image_memory_choices = []
    st.session_state.image_memory_start_time = None
    st.session_state.image_memory_answer_phase = False
    st.session_state.image_memory_selected = []


def reset_schulte_game():
    st.session_state.schulte_running = False
    st.session_state.schulte_grid = []
    st.session_state.schulte_next = 1
    st.session_state.schulte_start_time = None
    st.session_state.schulte_errors = 0
    st.session_state.schulte_round = 0


def reset_spot_game():
    st.session_state.spot_running = False
    st.session_state.spot_grid_left = []
    st.session_state.spot_grid_right = []
    st.session_state.spot_difference = None
    st.session_state.spot_choice = None
    st.session_state.spot_round = 0


def reset_hidden_game():
    st.session_state.hidden_running = False
    st.session_state.hidden_targets = []
    st.session_state.hidden_found = []
    st.session_state.hidden_round = 0


def reset_tracker_game():
    st.session_state.tracker_running = False
    st.session_state.tracker_size = 4
    st.session_state.tracker_round = 0
    st.session_state.tracker_hits = 0
    st.session_state.tracker_target_pos = None
    st.session_state.tracker_target_start = None


def exit_current_game(game_name):
    if game_name == "Memory Sequence":
        reset_memory_game()
    elif game_name == "Pattern Memory":
        reset_pattern_game()
    elif game_name == "Attention Game":
        reset_attention_game()
    elif game_name == "Image Recognition":
        reset_image_memory_game()
    elif game_name == "Schulte Table":
        reset_schulte_game()
    elif game_name == "Spot the Difference":
        reset_spot_game()
    elif game_name == "Hidden Object Search":
        reset_hidden_game()
    elif game_name == "Target Tracker":
        reset_tracker_game()

    queue_voice(
        f"You exited the {game_name}. The unfinished game was not saved.",
        language
    )
    st.rerun()


def save_completed_game(game_name, final_score):
    conn.execute(
        """
        INSERT INTO sessions(
            user_id, game, score, difficulty, created_at
        )
        VALUES(?, ?, ?, ?, ?)
        """,
        (
            user_id,
            game_name,
            round(float(final_score), 1),
            difficulty,
            datetime.now().isoformat(timespec="seconds")
        )
    )
    conn.commit()


# ============================================================
# IMAGE RECOGNITION GAME ASSETS
# ============================================================
#
# The image game is fully self-contained: it does not require an external
# image directory or another Python package. Each image card is represented
# by a clean visual card containing an image-like emoji illustration.
#
# The game randomly chooses a target set, displays those image cards for
# exactly 10 seconds, hides them at 0 seconds, and only then activates the
# answer choices. A one-second Streamlit autorefresh keeps the countdown and
# phase transition synchronized without blocking the application.
# ============================================================

IMAGE_GAME_ITEMS = {
    "apple": {"label": "Apple", "emoji": "🍎", "bg": "#FFE4E6"},
    "book": {"label": "Book", "emoji": "📚", "bg": "#E0F2FE"},
    "car": {"label": "Car", "emoji": "🚗", "bg": "#FEF3C7"},
    "dog": {"label": "Dog", "emoji": "🐶", "bg": "#DCFCE7"},
    "flower": {"label": "Flower", "emoji": "🌸", "bg": "#FCE7F3"},
    "house": {"label": "House", "emoji": "🏠", "bg": "#EDE9FE"},
    "moon": {"label": "Moon", "emoji": "🌙", "bg": "#E0E7FF"},
    "parrot": {"label": "Parrot", "emoji": "🦜", "bg": "#CCFBF1"},
    "pencil": {"label": "Pencil", "emoji": "✏️", "bg": "#FEF9C3"},
    "phone": {"label": "Phone", "emoji": "📱", "bg": "#E2E8F0"},
    "sun": {"label": "Sun", "emoji": "☀️", "bg": "#FFEDD5"},
    "tree": {"label": "Tree", "emoji": "🌳", "bg": "#D1FAE5"},
    "umbrella": {"label": "Umbrella", "emoji": "☂️", "bg": "#DBEAFE"},
    "watch": {"label": "Watch", "emoji": "⌚", "bg": "#F1F5F9"},
    "ball": {"label": "Ball", "emoji": "⚽", "bg": "#E5E7EB"},
    "camera": {"label": "Camera", "emoji": "📷", "bg": "#F3F4F6"},
}

IMAGE_GAME_DIFFICULTY = {
    1: {"target_count": 4, "choice_count": 8},
    2: {"target_count": 6, "choice_count": 10},
    3: {"target_count": 8, "choice_count": 12},
}


def image_card_html(item_key, compact=False):
    """Return a clear image-like card for the image memory game."""
    item = IMAGE_GAME_ITEMS[item_key]
    width = 105 if compact else 140
    height = 125 if compact else 150
    emoji_size = 48 if compact else 64
    label_size = 12 if compact else 15

    return f"""
    <div style="
        width:{width}px;
        min-height:{height}px;
        border-radius:18px;
        padding:10px;
        box-sizing:border-box;
        background:{item['bg']};
        border:2px solid rgba(79,70,229,.18);
        display:flex;
        flex-direction:column;
        justify-content:center;
        align-items:center;
        box-shadow:0 6px 18px rgba(15,23,42,.10);
        margin:auto;
    ">
        <div style="font-size:{emoji_size}px;line-height:1.1;">{item['emoji']}</div>
        <div style="margin-top:8px;font-weight:800;font-size:{label_size}px;color:#1E293B;text-align:center;">
            {item['label']}
        </div>
    </div>
    """


def render_image_cards(item_keys, compact=False):
    """Render image cards in a centered responsive flex container."""
    cards = "".join(
        image_card_html(key, compact=compact)
        for key in item_keys
    )

    return f"""
    <div style="
        display:flex;
        flex-wrap:wrap;
        justify-content:center;
        align-items:center;
        gap:14px;
        width:100%;
        padding:8px 0;
    ">
        {cards}
    </div>
    """


def image_countdown_banner(seconds_remaining):
    """Return a large, readable countdown badge."""
    if seconds_remaining <= 0:
        return """
        <div style="
            display:block;
            width:max-content;
            margin:8px auto;
            padding:10px 20px;
            border-radius:999px;
            background:#DCFCE7;
            color:#166534;
            font-weight:900;
            font-size:18px;
            border:2px solid #86EFAC;
        ">
            ✅ 0 seconds - images hidden
        </div>
        """

    return f"""
    <div style="
        display:block;
        width:max-content;
        min-width:130px;
        margin:8px auto;
        padding:10px 22px;
        border-radius:999px;
        background:#3730A3;
        color:white;
        font-weight:900;
        text-align:center;
        font-size:21px;
        border:2px solid #818CF8;
        box-shadow:0 5px 18px rgba(55,48,163,.25);
    ">
        ⏱️ {seconds_remaining} seconds
    </div>
    """


def image_remaining_seconds():
    """Calculate remaining 10-second viewing time without time.sleep()."""
    start = st.session_state.get("image_memory_start_time")

    if start is None:
        return 0

    elapsed = pytime.time() - float(start)
    return max(0, 10 - int(elapsed))


def prepare_image_memory_round(difficulty_level, round_number):
    """Create a target image set and distractor choices for a new round."""
    config = IMAGE_GAME_DIFFICULTY[difficulty_level]
    all_keys = list(IMAGE_GAME_ITEMS.keys())

    target_keys = random.sample(
        all_keys,
        config["target_count"]
    )

    remaining_keys = [
        key
        for key in all_keys
        if key not in target_keys
    ]

    distractor_count = (
        config["choice_count"]
        - config["target_count"]
    )

    distractors = random.sample(
        remaining_keys,
        distractor_count
    )

    answer_choices = target_keys + distractors
    random.shuffle(answer_choices)

    st.session_state.image_memory_sequence = target_keys
    st.session_state.image_memory_choices = answer_choices
    st.session_state.image_memory_round = round_number
    st.session_state.image_memory_total_score = (
        st.session_state.get("image_memory_total_score", 0.0)
    )
    st.session_state.image_memory_start_time = pytime.time()
    st.session_state.image_memory_answer_phase = False
    st.session_state.image_memory_selected = []


def save_image_game_result(final_score, old_difficulty, new_difficulty):
    """Save a completed image game and populate the common result banner."""
    rounded_score = round(float(final_score), 1)

    save_completed_game(
        "Image Recognition",
        rounded_score
    )

    st.session_state.game_result_message = game_result_voice(
        "Image Recognition Game",
        rounded_score,
        old_difficulty,
        new_difficulty,
        language
    )
    st.session_state.game_result_score = rounded_score
    st.session_state.game_result_old_difficulty = old_difficulty
    st.session_state.game_result_new_difficulty = new_difficulty


# ============================================================
# PATIENT HOME
# ============================================================

if selected_page == "home":
    # Use textwrap.dedent so the HTML is rendered as HTML,
    # instead of being displayed as a code block.
    home_html = textwrap.dedent(
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
                🧠 {text("welcome", language)}, {name}!
            </h1>

         </div>
        """
    )

    st.markdown(
        home_html,
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
            SELECT name, username, phone, email, location
            FROM users
            WHERE id=?
            AND role='doctor'
            """,
            (doctor_id,)
        ).fetchone()

        if doctor:
            st.success(
                f"🩺 Assigned Doctor: Dr. {doctor[0]}"
            )
            st.caption(
                f"Phone: {doctor[2]} | Email: {doctor[3]} | Location: {doctor[4]}"
            )

    elif caretaker_id:

        caretaker = conn.execute(
            """
            SELECT name, username, phone, email, location
            FROM users
            WHERE id=?
            AND role='caretaker'
            """,
            (caretaker_id,)
        ).fetchone()

        if caretaker:
            st.success(
                f"🤝 Assigned Caretaker: {caretaker[0]}"
            )
            st.caption(
                f"Phone: {caretaker[2]} | Email: {caretaker[3]} | Location: {caretaker[4]}"
            )

    else:

        st.info(
            "🩺/🤝 No doctor or caretaker has been linked yet. "
            "A local doctor or caretaker can add you directly from their portal."
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

    # Show the most recent completed-game result once after returning
    # from the completed multi-round game.
    if st.session_state.get("game_result_message"):
        completed_score = st.session_state.get("game_result_score")
        old_level = st.session_state.get("game_result_old_difficulty")
        new_level = st.session_state.get("game_result_new_difficulty")

        if completed_score is not None and completed_score >= 70:
            st.success(
                f"🎉 Congratulations! You completed the game with a score of "
                f"{completed_score:.1f}/100."
            )

            if new_level is not None and old_level is not None and new_level > old_level:
                st.success(
                    f"⬆️ Excellent performance! Your difficulty level increased "
                    f"from {old_level} to {new_level}."
                )
            else:
                st.info(
                    f"⭐ Your current difficulty level is {new_level}."
                )
        else:
            st.info(
                f"Game completed with a score of {completed_score:.1f}/100. "
                f"Keep practicing! Your current difficulty level is {new_level}."
            )

        # Keep the message from repeating on every later games-page visit.
        st.session_state.game_result_message = None
        st.session_state.game_result_score = None
        st.session_state.game_result_old_difficulty = None
        st.session_state.game_result_new_difficulty = None

    st.title(
        "🎮 " +
        text(
            "games",
            language
        )
    )

    st.write(
        f"Adaptive difficulty level: **{difficulty} / 3**"
    )

    total_rounds = GAME_ROUNDS_BY_DIFFICULTY[difficulty]

    st.info(
        f"This game contains {total_rounds} rounds at the current difficulty. "
        "You can exit an unfinished game at any time. "
        "Strong performance (70 or above) increases the difficulty level; "
        "lower performance decreases it."
    )

    # Streamlit tabs return to the first tab after every rerun. Since the
    # games intentionally rerun for timers, answers and next rounds, tabs
    # can make an active game look like it returned to "Start Game". Use a
    # persistent game selector instead. The selected game survives every
    # rerun and each game keeps its own session state.
    if "active_game" not in st.session_state:
        st.session_state.active_game = "Memory Sequence"

    active_game = st.radio(
        "Choose Game",
        [
            "Memory Sequence",
            "Pattern Memory",
            "Attention Game",
            "Image Recognition",
            "Schulte Table",
            "Spot the Difference",
            "Hidden Object Search",
            "Target Tracker"
        ],
        key="active_game",
        horizontal=True,
        format_func=lambda x: {
            "Memory Sequence": "🧠 Memory Sequence",
            "Pattern Memory": "🔷 Pattern Memory",
            "Attention Game": "⚡ Attention Game",
            "Image Recognition": "🖼️ Image Recognition",
            "Schulte Table": "🔢 Schulte Table",
            "Spot the Difference": "🔍 Spot the Difference",
            "Hidden Object Search": "🕵️ Hidden Object Search",
            "Target Tracker": "🎯 Target Tracker"
        }[x]
    )

    st.divider()

    game_instruction_keys = {
        "Memory Sequence": "memory",
        "Pattern Memory": "pattern",
        "Attention Game": "attention",
        "Image Recognition": "image",
        "Schulte Table": "schulte",
        "Spot the Difference": "spot",
        "Hidden Object Search": "hidden",
        "Target Tracker": "target",
    }
    show_instructions(
        game_instruction_keys.get(active_game, "games"),
        language,
        expanded=True
    )

    # ========================================================
    # MEMORY SEQUENCE
    # ========================================================

    if active_game == "Memory Sequence":

        st.subheader("🧠 Memory Sequence")

        sequence_length = {
            1: 4,
            2: 6,
            3: 8
        }[difficulty]

        if st.session_state.memory_round == 0:

            st.write(
                f"You will play {total_rounds} rounds. "
                f"Remember {sequence_length} numbers in each round."
            )

            if st.button(
                "▶️ Start Memory Game",
                type="primary",
                key="memory_start"
            ):

                st.session_state.memory_round = 1
                st.session_state.memory_total_score = 0.0
                st.session_state.memory_sequence = random.sample(
                    range(1, 10),
                    sequence_length
                )
                st.session_state.memory_start_time = pytime.time()
                st.session_state.memory_answer_phase = False

                queue_voice(
                    f"Memory game started. Round 1 of {total_rounds}. "
                    f"You have 10 seconds to remember {sequence_length} numbers. "
                    "The numbers will then disappear. Enter the sequence from memory.",
                    language
                )

                st.rerun()

        else:

            current_round = st.session_state.memory_round
            sequence = st.session_state.memory_sequence

            st.progress(
                current_round / total_rounds,
                text=f"Round {current_round} of {total_rounds}"
            )

            # --------------------------------------------------------
            # 10-SECOND MEMORY DISPLAY / ANSWER LOCK
            # --------------------------------------------------------
            # The timer is stored in session_state so every Streamlit rerun
            # continues the SAME round instead of starting it again.
            if not st.session_state.get("memory_answer_phase", False):
                if st.session_state.get("memory_start_time") is None:
                    st.session_state.memory_start_time = pytime.time()

                elapsed = pytime.time() - float(st.session_state.memory_start_time)
                remaining = max(0, 10 - int(elapsed))

                # IMPORTANT: create the text before displaying it.
                sequence_text = "   •   ".join(str(number) for number in sequence)

                # Use normal Streamlit rendering so the numbers are clearly
                # visible in every browser/theme.
                st.markdown(
                    "<div style=\"text-align:center; font-size:20px; font-weight:700; margin-top:15px;\">"
                    "🧠 MEMORIZE THESE NUMBERS"
                    "</div>",
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"<div style=\"background:#EEF2FF; border:3px solid #4F46E5; "
                    f"border-radius:18px; padding:28px 12px; text-align:center; "
                    f"margin:12px 0;\">"
                    f"<div style=\"font-size:42px; font-weight:900; "
                    f"letter-spacing:6px; color:#111827;\">{sequence_text}</div>"
                    f"<div style=\"font-size:30px; font-weight:900; "
                    f"margin-top:18px; color:#B91C1C;\">⏱️ {remaining}</div>"
                    f"<div style=\"font-size:15px; margin-top:8px; color:#374151;\">"
                    f"Numbers disappear at 0 seconds</div></div>",
                    unsafe_allow_html=True
                )

                st.info(
                    f"🔒 Answer locked — memorize the numbers. "
                    f"Time remaining: **{remaining} seconds**"
                )

                if remaining > 0:
                    if st_autorefresh is not None:
                        st_autorefresh(
                            interval=250,
                            limit=50,
                            key=f"memory_timer_{user_id}_{current_round}"
                        )
                    else:
                        st.warning(
                            "Please add **streamlit-autorefresh** to requirements.txt "
                            "for the live countdown."
                        )
                else:
                    # Switch permanently to answer phase. Do NOT clear
                    # memory_start_time, otherwise the next rerun would
                    # accidentally restart the 10-second timer.
                    st.session_state.memory_answer_phase = True
                    st.rerun()

            else:
                # --------------------------------------------------------
                # ANSWER PHASE — numbers are hidden and input is enabled
                # --------------------------------------------------------
                st.markdown(
                    "<div style=\"text-align:center; padding:22px; "
                    "border:3px solid #16A34A; border-radius:18px; "
                    "background:#F0FDF4; margin:12px 0;\">"
                    "<div style=\"font-size:30px; font-weight:900; color:#15803D;\">"
                    "⏱️ 0 — NUMBERS DISAPPEARED</div>"
                    "<div style=\"font-size:18px; margin-top:8px;\">"
                    "Now enter the numbers in the same order.</div>"
                    "</div>",
                    unsafe_allow_html=True
                )
                st.success("✅ Answer box is now active!")
            answer = st.text_input(
                "Enter the numbers in the same order",
                key=f"memory_answer_{current_round}",
                disabled=not st.session_state.get("memory_answer_phase", False)
            )

            exit_col, submit_col = st.columns(2)

            with exit_col:

                if st.button(
                    "🚪 Exit Game",
                    key=f"memory_exit_{current_round}",
                    use_container_width=True
                ):
                    exit_current_game("Memory Sequence")

            with submit_col:

                if st.button(
                    "Submit Round",
                    key=f"memory_submit_{current_round}",
                    type="primary",
                    use_container_width=True
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

                            st.error(
                                f"Enter exactly {len(sequence)} numbers."
                            )

                        else:

                            correct = sum(
                                a == b
                                for a, b in zip(
                                    sequence,
                                    user_answer
                                )
                            )

                            round_score = (
                                correct /
                                len(sequence)
                            ) * 100

                            st.session_state.memory_total_score += round_score

                            if current_round >= total_rounds:

                                final_score = (
                                    st.session_state.memory_total_score /
                                    total_rounds
                                )

                                save_completed_game(
                                    "Memory Sequence",
                                    final_score
                                )

                                old_difficulty, new_difficulty, result = (
                                    update_adaptive_difficulty(
                                        user_id,
                                        final_score
                                    )
                                )

                                st.session_state.game_result_message = game_result_voice(
                                    "Memory Game",
                                    round(final_score, 1),
                                    old_difficulty,
                                    new_difficulty,
                                    language
                                )
                                st.session_state.game_result_score = round(final_score, 1)
                                st.session_state.game_result_old_difficulty = old_difficulty
                                st.session_state.game_result_new_difficulty = new_difficulty

                                reset_memory_game()

                                queue_voice(
                                    game_result_voice(
                                        "Memory Game",
                                        round(final_score, 1),
                                        old_difficulty,
                                        new_difficulty,
                                        language
                                    ),
                                    language
                                )

                                st.rerun()

                            else:

                                next_round = current_round + 1
                                st.session_state.memory_round = next_round
                                st.session_state.memory_sequence = random.sample(
                                    range(1, 10),
                                    sequence_length
                                )
                                st.session_state.memory_start_time = pytime.time()
                                st.session_state.memory_answer_phase = False

                                st.rerun()

                    except ValueError:

                        st.error(
                            "Please enter numbers only."
                        )

    # ========================================================
    # PATTERN MEMORY
    # ========================================================

    if active_game == "Pattern Memory":

        st.subheader("🔷 Pattern Memory")

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

        if st.session_state.pattern_round == 0:

            st.write(
                f"You will play {total_rounds} rounds. "
                f"Remember {pattern_length} symbols in each round."
            )

            if st.button(
                "▶️ Start Pattern Game",
                type="primary",
                key="pattern_start"
            ):

                st.session_state.pattern_round = 1
                st.session_state.pattern_total_score = 0.0
                st.session_state.pattern_sequence = [
                    random.choice(symbols)
                    for _ in range(pattern_length)
                ]

                queue_voice(
                    f"Pattern game started. Round 1 of {total_rounds}. "
                    f"Remember {pattern_length} symbols.",
                    language
                )

                st.rerun()

        else:

            current_round = st.session_state.pattern_round
            pattern = st.session_state.pattern_sequence

            st.progress(
                current_round / total_rounds,
                text=f"Round {current_round} of {total_rounds}"
            )

            st.success("Remember this pattern:")

            st.markdown(
                "## " +
                " ".join(pattern)
            )

            pattern_answer = st.text_input(
                "Enter the pattern using symbols",
                placeholder="Example: ▲ ● ■ ◆",
                key=f"pattern_answer_{current_round}"
            )

            exit_col, submit_col = st.columns(2)

            with exit_col:

                if st.button(
                    "🚪 Exit Game",
                    key=f"pattern_exit_{current_round}",
                    use_container_width=True
                ):
                    exit_current_game("Pattern Memory")

            with submit_col:

                if st.button(
                    "Submit Round",
                    key=f"pattern_submit_{current_round}",
                    type="primary",
                    use_container_width=True
                ):

                    answer_symbols = (
                        pattern_answer
                        .strip()
                        .split()
                    )

                    if len(answer_symbols) != len(pattern):

                        st.error(
                            f"Enter exactly {len(pattern)} symbols."
                        )

                    else:

                        correct = sum(
                            a == b
                            for a, b in zip(
                                pattern,
                                answer_symbols
                            )
                        )

                        round_score = (
                            correct /
                            len(pattern)
                        ) * 100

                        st.session_state.pattern_total_score += round_score

                        if current_round >= total_rounds:

                            final_score = (
                                st.session_state.pattern_total_score /
                                total_rounds
                            )

                            save_completed_game(
                                "Pattern Memory",
                                final_score
                            )

                            old_difficulty, new_difficulty, result = (
                                update_adaptive_difficulty(
                                    user_id,
                                    final_score
                                )
                            )

                            st.session_state.game_result_message = game_result_voice(
                                "Pattern Memory Game",
                                round(final_score, 1),
                                old_difficulty,
                                new_difficulty,
                                language
                            )
                            st.session_state.game_result_score = round(final_score, 1)
                            st.session_state.game_result_old_difficulty = old_difficulty
                            st.session_state.game_result_new_difficulty = new_difficulty

                            reset_pattern_game()

                            queue_voice(
                                game_result_voice(
                                    "Pattern Memory Game",
                                    round(final_score, 1),
                                    old_difficulty,
                                    new_difficulty,
                                    language
                                ),
                                language
                            )

                            st.rerun()

                        else:

                            next_round = current_round + 1
                            st.session_state.pattern_round = next_round
                            st.session_state.pattern_sequence = [
                                random.choice(symbols)
                                for _ in range(pattern_length)
                            ]

                            st.rerun()

    # ========================================================
    # ATTENTION GAME
    # ========================================================

    if active_game == "Attention Game":

        st.subheader("⚡ Attention Game")

        st.write(
            "Click the target number."
        )

        if st.session_state.attention_round == 0:

            st.write(
                f"You will play {total_rounds} rounds. "
                "Find the target number in each round."
            )

            if st.button(
                "▶️ Start Attention Game",
                type="primary",
                key="attention_start"
            ):

                st.session_state.attention_round = 1
                st.session_state.attention_total_score = 0.0
                st.session_state.reaction_target = random.randint(1, 9)

                queue_voice(
                    f"Attention game started. Round 1 of {total_rounds}. "
                    "Find the target number.",
                    language
                )

                st.rerun()

        else:

            current_round = st.session_state.attention_round
            target = st.session_state.reaction_target

            st.progress(
                current_round / total_rounds,
                text=f"Round {current_round} of {total_rounds}"
            )

            st.markdown(
                f"## Find: **{target}**"
            )

            if st.button(
                "🚪 Exit Game",
                key=f"attention_exit_{current_round}",
                use_container_width=True
            ):
                exit_current_game("Attention Game")

            cols = st.columns(3)
            numbers = list(range(1, 10))
            random.shuffle(numbers)

            for index, number in enumerate(numbers):

                with cols[index % 3]:

                    if st.button(
                        str(number),
                        key=f"attention_{current_round}_{number}"
                    ):

                        round_score = (
                            100
                            if number == target
                            else 0
                        )

                        st.session_state.attention_total_score += round_score

                        if current_round >= total_rounds:

                            final_score = (
                                st.session_state.attention_total_score /
                                total_rounds
                            )

                            save_completed_game(
                                "Attention Game",
                                final_score
                            )

                            old_difficulty, new_difficulty, result = (
                                update_adaptive_difficulty(
                                    user_id,
                                    final_score
                                )
                            )

                            st.session_state.game_result_message = game_result_voice(
                                "Attention Game",
                                round(final_score, 1),
                                old_difficulty,
                                new_difficulty,
                                language
                            )
                            st.session_state.game_result_score = round(final_score, 1)
                            st.session_state.game_result_old_difficulty = old_difficulty
                            st.session_state.game_result_new_difficulty = new_difficulty

                            reset_attention_game()

                            queue_voice(
                                game_result_voice(
                                    "Attention Game",
                                    round(final_score, 1),
                                    old_difficulty,
                                    new_difficulty,
                                    language
                                ),
                                language
                            )

                            st.rerun()

                        else:

                            st.session_state.attention_round = current_round + 1
                            st.session_state.reaction_target = random.randint(1, 9)

                            st.rerun()


    # ========================================================
    # IMAGE RECOGNITION / IMAGE MEMORY GAME
    # ========================================================

    if active_game == "Image Recognition":

        st.subheader("🖼️ Image Recognition Game")

        image_game_config = IMAGE_GAME_DIFFICULTY[difficulty]
        image_target_count = image_game_config["target_count"]
        image_choice_count = image_game_config["choice_count"]

        st.write(
            f"Remember {image_target_count} images. "
            "They remain visible for exactly 10 seconds. "
            "The answer choices activate only after the timer reaches 0."
        )

        st.info(
            "🧠 How it works: memorize the image cards → watch the countdown "
            "10 → 9 → 8 → ... → 1 → 0 → images disappear → answer section activates."
        )

        # ----------------------------------------------------
        # START IMAGE GAME
        # ----------------------------------------------------
        if st.session_state.image_memory_round == 0:

            st.markdown(
                f"### 🎯 {total_rounds} rounds | "
                f"{image_target_count} images to remember | "
                f"{image_choice_count} answer choices"
            )

            st.markdown(
                "**Important:** Do not select anything during the 10-second "
                "viewing phase. Selection becomes available automatically at 0 seconds."
            )

            if st.button(
                "▶️ Start Image Recognition Game",
                type="primary",
                key="image_memory_start",
                use_container_width=True
            ):

                st.session_state.image_memory_total_score = 0.0

                prepare_image_memory_round(
                    difficulty,
                    1
                )

                queue_voice(
                    f"Image Recognition Game started. Round 1 of {total_rounds}. "
                    f"Remember {image_target_count} images for 10 seconds.",
                    language
                )

                st.rerun()

        # ----------------------------------------------------
        # ACTIVE IMAGE GAME
        # ----------------------------------------------------
        else:

            current_round = st.session_state.image_memory_round

            target_images = st.session_state.image_memory_sequence

            answer_choices = st.session_state.get(
                "image_memory_choices",
                []
            )

            st.progress(
                current_round / total_rounds,
                text=f"Round {current_round} of {total_rounds}"
            )

            # ------------------------------------------------
            # VIEWING PHASE
            # ------------------------------------------------
            remaining = image_remaining_seconds()

            if remaining > 0:

                st.session_state.image_memory_answer_phase = False

                st.markdown(
                    "### 👀 Memorize these images"
                )

                st.markdown(
                    render_image_cards(target_images),
                    unsafe_allow_html=True
                )

                st.markdown(
                    image_countdown_banner(remaining),
                    unsafe_allow_html=True
                )

                st.caption(
                    "🔒 Answer controls are locked. They will appear after the countdown reaches 0."
                )

                if st_autorefresh is not None:

                    st_autorefresh(
                        interval=1000,
                        limit=11,
                        key=f"image_memory_timer_{user_id}_{current_round}"
                    )

                else:

                    st.error(
                        "Countdown dependency is missing. "
                        "Install streamlit-autorefresh and restart the app."
                    )

            # ------------------------------------------------
            # ANSWER PHASE
            # ------------------------------------------------
            else:

                if not st.session_state.image_memory_answer_phase:

                    st.session_state.image_memory_answer_phase = True
                    st.session_state.image_memory_start_time = None
                    st.session_state.image_memory_selected = []

                    st.rerun()

                st.markdown(
                    image_countdown_banner(0),
                    unsafe_allow_html=True
                )

                st.success(
                    "✅ Time is up! The images have disappeared. "
                    "The answer choices are now active."
                )

                st.markdown(
                    f"### 🧠 Select exactly {image_target_count} images you remember"
                )

                selected_keys = []

                choice_columns = st.columns(4)

                for index, image_key in enumerate(answer_choices):

                    with choice_columns[index % 4]:

                        st.markdown(
                            render_image_cards(
                                [image_key],
                                compact=True
                            ),
                            unsafe_allow_html=True
                        )

                        checked = st.checkbox(
                            f"Select {IMAGE_GAME_ITEMS[image_key]['label']}",
                            key=(
                                f"image_choice_{user_id}_"
                                f"{current_round}_{image_key}"
                            )
                        )

                        if checked:
                            selected_keys.append(image_key)

                st.session_state.image_memory_selected = selected_keys

                st.markdown(
                    f"**Selected: {len(selected_keys)} / {image_target_count}**"
                )

                exit_col, submit_col = st.columns(2)

                with exit_col:

                    if st.button(
                        "🚪 Exit Image Game",
                        key=f"image_exit_{current_round}",
                        use_container_width=True
                    ):

                        exit_current_game(
                            "Image Recognition"
                        )

                with submit_col:

                    if st.button(
                        "✅ Submit Image Answer",
                        key=f"image_submit_{current_round}",
                        type="primary",
                        use_container_width=True
                    ):

                        if len(selected_keys) != image_target_count:

                            st.error(
                                f"Please select exactly {image_target_count} images before submitting."
                            )

                        else:

                            correct = sum(
                                image_key in target_images
                                for image_key in selected_keys
                            )

                            round_score = (
                                correct /
                                image_target_count
                            ) * 100

                            st.session_state.image_memory_total_score += round_score

                            st.success(
                                f"Round {current_round}: {correct} of "
                                f"{image_target_count} images correct "
                                f"({round_score:.0f}/100)."
                            )

                            if current_round >= total_rounds:

                                final_score = (
                                    st.session_state.image_memory_total_score /
                                    total_rounds
                                )

                                old_difficulty, new_difficulty, result = (
                                    update_adaptive_difficulty(
                                        user_id,
                                        final_score
                                    )
                                )

                                save_image_game_result(
                                    final_score,
                                    old_difficulty,
                                    new_difficulty
                                )

                                reset_image_memory_game()

                                queue_voice(
                                    game_result_voice(
                                        "Image Recognition Game",
                                        round(final_score, 1),
                                        old_difficulty,
                                        new_difficulty,
                                        language
                                    ),
                                    language
                                )

                                st.rerun()

                            else:

                                next_round = current_round + 1

                                prepare_image_memory_round(
                                    difficulty,
                                    next_round
                                )

                                queue_voice(
                                    f"Round {current_round} completed. "
                                    f"Starting image round {next_round} of {total_rounds}. "
                                    f"You have 10 seconds to remember the images.",
                                    language
                                )

                                st.rerun()


# ========================================================
# SCHULTE TABLE
# ========================================================

    if active_game == "Schulte Table":

        st.subheader("🔢 Schulte Table")
        st.write(
            "Tap numbers from 1 upward as quickly as possible. "
            "For training, keep your gaze anchored near the center square "
            "and use peripheral vision to locate the next number."
        )

        schulte_size = {1: 5, 2: 6, 3: 7}[difficulty]
        schulte_total = schulte_size * schulte_size

        if not st.session_state.schulte_running:
            st.info(
                f"Level {difficulty}: {schulte_size}×{schulte_size} table "
                f"with {schulte_total} numbers. Your time starts on Start."
            )
            if st.button("▶️ Start Schulte Table", type="primary", use_container_width=True):
                nums = list(range(1, schulte_total + 1))
                random.shuffle(nums)
                st.session_state.schulte_grid = nums
                st.session_state.schulte_next = 1
                st.session_state.schulte_start_time = pytime.time()
                st.session_state.schulte_errors = 0
                st.session_state.schulte_running = True
                st.rerun()
        else:
            elapsed = pytime.time() - float(st.session_state.schulte_start_time or pytime.time())
            st.metric("Time", f"{elapsed:.1f} seconds")
            st.caption(f"Find: **{st.session_state.schulte_next}**  | Errors: {st.session_state.schulte_errors}")

            grid = st.session_state.schulte_grid
            for r in range(schulte_size):
                cols = st.columns(schulte_size)
                for c in range(schulte_size):
                    idx = r * schulte_size + c
                    number = grid[idx]
                    with cols[c]:
                        if st.button(str(number), key=f"schulte_{st.session_state.schulte_next}_{idx}", use_container_width=True):
                            if number == st.session_state.schulte_next:
                                if number == schulte_total:
                                    final_time = pytime.time() - float(st.session_state.schulte_start_time)
                                    # Faster completion produces a higher score.
                                    expected = 45 + (difficulty - 1) * 20
                                    score = max(0.0, min(100.0, 100 - max(0, final_time - expected) * 1.8 - st.session_state.schulte_errors * 3))
                                    old_d, new_d, _ = update_adaptive_difficulty(user_id, score)
                                    save_completed_game("Schulte Table", score)
                                    st.session_state.game_result_message = game_result_voice("Schulte Table", score, old_d, new_d, language)
                                    st.session_state.game_result_score = round(score, 1)
                                    st.session_state.game_result_old_difficulty = old_d
                                    st.session_state.game_result_new_difficulty = new_d
                                    st.session_state.schulte_running = False
                                    st.session_state.schulte_round = 0
                                    st.success(f"🎉 Schulte Table completed in {final_time:.1f} seconds. Score: {score:.1f}/100")
                                else:
                                    st.session_state.schulte_next += 1
                                    st.rerun()
                            else:
                                st.session_state.schulte_errors += 1
                                st.warning(f"Try again — next number is {st.session_state.schulte_next}.")

            if st.button("⏹️ Exit Schulte Table"):
                st.session_state.schulte_running = False
                st.rerun()


# ========================================================
# SPOT THE DIFFERENCE
# ========================================================

    if active_game == "Spot the Difference":

        st.subheader("🔍 Spot the Difference")
        st.write(
            "Compare the two illustrations and identify the one changed location. "
            "Look carefully for a tiny visual detail such as a missing, added, "
            "or changed object."
        )

        spot_size = {1: 4, 2: 5, 3: 6}[difficulty]
        spot_items = ["🏠", "🌳", "☀️", "🚗", "🌸", "🐶", "📚", "☁️", "🪟", "🪴"]

        if not st.session_state.spot_running:
            if st.button("▶️ Start Spot the Difference", type="primary", use_container_width=True):
                base = [random.choice(spot_items) for _ in range(spot_size * spot_size)]
                diff = random.randrange(len(base))
                right = base.copy()
                alternatives = [x for x in spot_items if x != base[diff]]
                right[diff] = random.choice(alternatives)
                st.session_state.spot_grid_left = base
                st.session_state.spot_grid_right = right
                st.session_state.spot_difference = diff
                st.session_state.spot_choice = None
                st.session_state.spot_running = True
                st.session_state.spot_round += 1
                st.rerun()
        else:
            left = st.session_state.spot_grid_left
            right = st.session_state.spot_grid_right
            st.markdown("**Left illustration**      **Right illustration**")
            for r in range(spot_size):
                lcols = st.columns(spot_size)
                for c in range(spot_size):
                    idx = r * spot_size + c
                    with lcols[c]:
                        st.markdown(f"<div style='font-size:30px;text-align:center;padding:8px'>{left[idx]}</div>", unsafe_allow_html=True)
            st.write("")
            for r in range(spot_size):
                rcols = st.columns(spot_size)
                for c in range(spot_size):
                    idx = r * spot_size + c
                    with rcols[c]:
                        st.markdown(f"<div style='font-size:30px;text-align:center;padding:8px'>{right[idx]}</div>", unsafe_allow_html=True)

            choice = st.selectbox(
                "Which cell is different?",
                list(range(1, spot_size * spot_size + 1)),
                key=f"spot_select_{st.session_state.spot_round}"
            )
            if st.button("✅ Check Difference", type="primary", use_container_width=True):
                chosen_idx = choice - 1
                if chosen_idx == st.session_state.spot_difference:
                    score = 100.0
                    st.success("🎉 Correct! You found the difference.")
                else:
                    score = 0.0
                    st.error(f"Not quite. The difference was at cell {st.session_state.spot_difference + 1}.")

                old_d, new_d, _ = update_adaptive_difficulty(user_id, score)
                save_completed_game("Spot the Difference", score)
                st.session_state.game_result_message = game_result_voice("Spot the Difference", score, old_d, new_d, language)
                st.session_state.game_result_score = round(score, 1)
                st.session_state.game_result_old_difficulty = old_d
                st.session_state.game_result_new_difficulty = new_d
                st.session_state.spot_running = False

            if st.button("⏹️ Exit Spot the Difference"):
                st.session_state.spot_running = False
                st.rerun()


# ========================================================
# HIDDEN OBJECT SEARCH
# ========================================================

    if active_game == "Hidden Object Search":

        st.subheader("🕵️ Hidden Object Search")
        st.write(
            "Find the requested objects inside the cluttered visual field. "
            "Use the checklist to filter visual clutter and maintain prolonged focus."
        )

        hidden_size = {1: 5, 2: 6, 3: 7}[difficulty]
        hidden_pool = ["🍎", "📚", "🚗", "🐶", "🌸", "🏠", "🌙", "🦜", "✏️", "📱", "☀️", "🌳", "⚽", "📷", "☂️"]
        hidden_labels = {"🍎":"Apple", "📚":"Book", "🚗":"Car", "🐶":"Dog", "🌸":"Flower", "🏠":"House", "🌙":"Moon", "🦜":"Parrot", "✏️":"Pencil", "📱":"Phone", "☀️":"Sun", "🌳":"Tree", "⚽":"Ball", "📷":"Camera", "☂️":"Umbrella"}
        target_count = {1: 3, 2: 4, 3: 5}[difficulty]

        if not st.session_state.hidden_running:
            if st.button("▶️ Start Hidden Object Search", type="primary", use_container_width=True):
                targets = random.sample(hidden_pool, target_count)
                clutter = [random.choice(hidden_pool) for _ in range(hidden_size * hidden_size - target_count)]
                grid = targets + clutter
                random.shuffle(grid)
                st.session_state.hidden_targets = targets
                st.session_state.hidden_grid = grid
                st.session_state.hidden_selected = []
                st.session_state.hidden_running = True
                st.session_state.hidden_round += 1
                st.rerun()
        else:
            targets = st.session_state.hidden_targets
            st.markdown("**Find these:** " + "  •  ".join(f"{x} {hidden_labels[x]}" for x in targets))
            grid = st.session_state.hidden_grid
            for r in range(hidden_size):
                cols = st.columns(hidden_size)
                for c in range(hidden_size):
                    idx = r * hidden_size + c
                    with cols[c]:
                        st.markdown(f"<div style='font-size:30px;text-align:center;padding:8px;background:#f8fafc;border-radius:10px'>{grid[idx]}</div>", unsafe_allow_html=True)

            selected = st.multiselect(
                "Select the objects you found",
                options=sorted(hidden_pool, key=lambda x: hidden_labels[x]),
                format_func=lambda x: f"{x} {hidden_labels[x]}",
                key=f"hidden_select_{st.session_state.hidden_round}"
            )
            if st.button("✅ Check Objects", type="primary", use_container_width=True):
                correct = set(selected) & set(targets)
                missing = set(targets) - set(selected)
                false = set(selected) - set(targets)
                score = max(0.0, min(100.0, 100 * len(correct) / len(targets) - 10 * len(false)))
                if not missing and not false:
                    st.success("🎉 Excellent! You found every hidden object.")
                else:
                    st.info(f"Found {len(correct)}/{len(targets)} target objects.")
                old_d, new_d, _ = update_adaptive_difficulty(user_id, score)
                save_completed_game("Hidden Object Search", score)
                st.session_state.game_result_message = game_result_voice("Hidden Object Search", score, old_d, new_d, language)
                st.session_state.game_result_score = round(score, 1)
                st.session_state.game_result_old_difficulty = old_d
                st.session_state.game_result_new_difficulty = new_d
                st.session_state.hidden_running = False

            if st.button("⏹️ Exit Hidden Object Search"):
                st.session_state.hidden_running = False
                st.rerun()


# ========================================================
# TARGET TRACKER
# ========================================================

    if active_game == "Target Tracker":

        st.subheader("🎯 Target Tracker")
        st.write(
            "A slow-moving, stress-free target appears in different grid locations. "
            "Tap it before it disappears to train spatial precision and selective attention."
        )

        tracker_rounds = {1: 10, 2: 15, 3: 20}[difficulty]
        tracker_size = {1: 4, 2: 5, 3: 6}[difficulty]
        # Target is visible for exactly 2 seconds at every difficulty level.
        # The autorefresh below updates the timer and removes the target when
        # the 2-second visibility window expires.
        target_duration = 2.0

        if not st.session_state.tracker_running:
            if st.button("▶️ Start Target Tracker", type="primary", use_container_width=True):
                st.session_state.tracker_round = 1
                st.session_state.tracker_hits = 0
                st.session_state.tracker_target_pos = random.randrange(tracker_size * tracker_size)
                st.session_state.tracker_target_start = pytime.time()
                st.session_state.tracker_running = True
                st.rerun()
        else:
            # Refresh once per second. Frequent 250 ms redraws can make
            # Streamlit Cloud look faded/flickery while the page rerenders.
            if st_autorefresh is not None:
                st_autorefresh(
                    interval=1000,
                    limit=None,
                    key=f"target_tracker_timer_{st.session_state.tracker_round}"
                )

            start_time = st.session_state.tracker_target_start
            if start_time is None:
                start_time = pytime.time()
                st.session_state.tracker_target_start = start_time

            elapsed = pytime.time() - float(start_time)
            remaining = max(0.0, target_duration - elapsed)

            # Image-Recognition-style whole-second countdown: 2 -> 1 -> 0.
            # No math.ceil() is used here.
            countdown = max(0, int(remaining + 0.999999))

            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    font-size:30px;
                    font-weight:700;
                    margin:12px 0;
                    padding:8px;
                ">
                    ⏱️ Target disappears in: {countdown}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption(
                f"Round {st.session_state.tracker_round}/{tracker_rounds} "
                f"• Hits: {st.session_state.tracker_hits}"
            )

            # Check expiry BEFORE rendering the target buttons. This means
            # an expired target can never remain visible on the screen.
            if remaining <= 0:
                if st.session_state.tracker_round >= tracker_rounds:
                    score = (
                        100.0
                        * st.session_state.tracker_hits
                        / tracker_rounds
                    )
                    old_d, new_d, _ = update_adaptive_difficulty(
                        user_id, score
                    )
                    save_completed_game(
                        "Target Tracker", score
                    )
                    st.session_state.game_result_message = game_result_voice(
                        "Target Tracker", score, old_d, new_d, language
                    )
                    st.session_state.game_result_score = round(score, 1)
                    st.session_state.game_result_old_difficulty = old_d
                    st.session_state.game_result_new_difficulty = new_d
                    st.session_state.tracker_running = False
                    st.success(
                        f"🎉 Target Tracker completed. Hits: "
                        f"{st.session_state.tracker_hits}/{tracker_rounds}"
                    )
                else:
                    # The old target is discarded before a new one is drawn.
                    st.session_state.tracker_round += 1
                    st.session_state.tracker_target_pos = random.randrange(
                        tracker_size * tracker_size
                    )
                    st.session_state.tracker_target_start = pytime.time()
                    st.rerun()

            else:
                # Draw the target ONLY while its 2-second visibility window
                # is active.
                for r in range(tracker_size):
                    cols = st.columns(tracker_size)
                    for c in range(tracker_size):
                        idx = r * tracker_size + c
                        with cols[c]:
                            label = (
                                "🎯"
                                if idx == st.session_state.tracker_target_pos
                                else "·"
                            )
                            if st.button(
                                label,
                                key=(
                                    f"tracker_{st.session_state.tracker_round}_{idx}"
                                ),
                                use_container_width=True,
                            ):
                                # Double-check elapsed time at click time so a
                                # late click cannot score after the 2 seconds.
                                click_elapsed = (
                                    pytime.time()
                                    - float(st.session_state.tracker_target_start)
                                )
                                if click_elapsed >= target_duration:
                                    st.rerun()

                                elif idx == st.session_state.tracker_target_pos:
                                    st.session_state.tracker_hits += 1
                                    st.session_state.tracker_round += 1

                                    if st.session_state.tracker_round > tracker_rounds:
                                        score = (
                                            100.0
                                            * st.session_state.tracker_hits
                                            / tracker_rounds
                                        )
                                        old_d, new_d, _ = update_adaptive_difficulty(
                                            user_id, score
                                        )
                                        save_completed_game(
                                            "Target Tracker", score
                                        )
                                        st.session_state.game_result_message = game_result_voice(
                                            "Target Tracker", score, old_d, new_d, language
                                        )
                                        st.session_state.game_result_score = round(score, 1)
                                        st.session_state.game_result_old_difficulty = old_d
                                        st.session_state.game_result_new_difficulty = new_d
                                        st.session_state.tracker_running = False
                                    else:
                                        st.session_state.tracker_target_pos = random.randrange(
                                            tracker_size * tracker_size
                                        )
                                        st.session_state.tracker_target_start = pytime.time()
                                    st.rerun()

            if st.button("⏹️ Exit Target Tracker"):
                st.session_state.tracker_running = False
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
        (user_id,)
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

        st.subheader(
            "📈 Last 5 Games Progress"
        )

        last_five = sessions[:5][::-1]

        graph_df = pd.DataFrame(
            [
                {
                    "Game": f"{index}. {row[0]}",
                    "Score": float(row[1])
                }
                for index, row in enumerate(last_five, start=1)
            ]
        )

        if not graph_df.empty:

            st.line_chart(
                graph_df.set_index("Game"),
                y="Score",
                use_container_width=True
            )

            st.caption(
                "The graph shows the five most recently completed games, "
                "with the oldest of those five first. Scores are final "
                "scores saved for each completed multi-round game."
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

    st.write(f"**Phone:** {phone}")
    st.write(f"**Email:** {email}")
    st.write(f"**Location:** {location}")

    if doctor_id:

        doctor = conn.execute(
            """
            SELECT name, username, phone, email, location
            FROM users
            WHERE id=?
            AND role='doctor'
            """,
            (doctor_id,)
        ).fetchone()

        if doctor:
            st.success(
                f"🩺 Assigned Doctor: Dr. {doctor[0]}"
            )
            st.write(f"Doctor Username: {doctor[1]}")
            st.write(f"Doctor Phone: {doctor[2]}")
            st.write(f"Doctor Email: {doctor[3]}")
            st.write(f"Doctor Location: {doctor[4]}")

    elif caretaker_id:

        caretaker = conn.execute(
            """
            SELECT name, username, phone, email, location
            FROM users
            WHERE id=?
            AND role='caretaker'
            """,
            (caretaker_id,)
        ).fetchone()

        if caretaker:
            st.success(
                f"🤝 Assigned Caretaker: {caretaker[0]}"
            )
            st.write(f"Caretaker Username: {caretaker[1]}")
            st.write(f"Caretaker Phone: {caretaker[2]}")
            st.write(f"Caretaker Email: {caretaker[3]}")
            st.write(f"Caretaker Location: {caretaker[4]}")

    else:

        st.info(
            "No doctor or caretaker linked yet. A provider can add the patient directly."
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

    # ------------------------------------------------------------
    # CLINICAL-STYLE APPLICATION REPORT
    # ------------------------------------------------------------

    st.subheader("🧾 Cognitive Progress Report")
    st.caption(
        "This report uses the same sectioned, professional visual style as the "
        "reference document, but only includes data available in SMRITISETU."
    )

    if REPORTLAB_AVAILABLE:

        clinical_pdf = build_patient_progress_pdf(
            user_id
        )

        if clinical_pdf:
            st.download_button(
                "⬇️ Download Cognitive Progress Report PDF",
                data=clinical_pdf,
                file_name=(
                    f"SMRITISETU_Cognitive_Report_"
                    f"{username}.pdf"
                ),
                mime="application/pdf",
                use_container_width=True
            )

            st.success(
                "Report generated successfully. "
                "The PDF contains your profile, longitudinal metrics, "
                "game performance, reminders, and session audit log."
            )

    else:
        st.warning(
            "PDF generation requires ReportLab. "
            "Install it with: pip install reportlab"
        )

    st.divider()

    # ------------------------------------------------------------
    # DOCTOR REPORTS ALREADY SENT TO THE PATIENT
    # ------------------------------------------------------------

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

        st.subheader("📨 Reports Sent by Doctor")

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
    f"🧠 {APP_NAME} | Cognitive Wellness Prototype"
)

st.caption(
    "For demonstration and educational purposes only. "
    "This prototype does not provide medical diagnosis."
)
