"""
streamlit_app.py
----------------
Optional Streamlit dashboard for EduFlow AI.

Run with:
    streamlit run streamlit_app.py

Shows:
  - Student selector / creator
  - Live progress stats
  - Difficulty indicator
  - Correct vs Incorrect bar chart
  - Learning path progress
  - Interactive quiz inside the browser
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from profile_manager    import ProfileManager
from quiz_engine         import generate_question, check_answer
from difficulty_manager  import adjust_difficulty, get_accuracy
from learning_path       import get_next_topic, get_topic_progress, TOPIC_SEQUENCE, HARD_TOPICS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EduFlow AI",
    page_icon="🎓",
    layout="wide",
)

# ── Session state helpers ──────────────────────────────────────────────────────
def init_state():
    defaults = {
        "student_name": None,
        "current_question": None,
        "answered": False,
        "answer_result": None,
        "session_correct": 0,
        "session_wrong": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
pm = ProfileManager()


# ── Sidebar – student selector ────────────────────────────────────────────────
st.sidebar.title("🎓 EduFlow AI")
st.sidebar.markdown("---")

all_names = list(pm.profiles.keys())
display_names = [pm.profiles[k]["name"] for k in all_names]

st.sidebar.subheader("Select Student")
selected_display = st.sidebar.selectbox(
    "Existing students", ["-- New Student --"] + display_names
)

if selected_display == "-- New Student --":
    new_name = st.sidebar.text_input("Enter new student name")
    if st.sidebar.button("Create Profile") and new_name.strip():
        pm.get_or_create(new_name.strip())
        st.session_state.student_name = new_name.strip().lower()
        st.session_state.current_question = None
        st.rerun()
else:
    idx = display_names.index(selected_display)
    key = all_names[idx]
    if st.session_state.student_name != key:
        st.session_state.student_name = key
        st.session_state.current_question = None
        st.session_state.answered = False
        st.session_state.session_correct = 0
        st.session_state.session_wrong = 0

# ── Main content ───────────────────────────────────────────────────────────────
if not st.session_state.student_name:
    st.title("Welcome to EduFlow AI")
    st.info("Select a student from the sidebar or create a new profile to get started.")
    st.stop()

student_key = st.session_state.student_name
profile     = pm.get_student(student_key)

if not profile:
    st.error("Profile not found. Please select or create a student.")
    st.stop()

name       = profile["name"]
difficulty = profile["difficulty"]
correct    = profile["correct_answers"]
wrong      = profile["wrong_answers"]
total      = correct + wrong
accuracy   = get_accuracy(profile)
next_topic = get_next_topic(profile)

# ── Header ────────────────────────────────────────────────────────────────────
st.title(f"👋 Welcome back, {name}!")
st.markdown(f"**Current Difficulty:** `{difficulty.upper()}`  |  **Last Topic:** {profile['last_topic']}")
st.markdown("---")

# ── Stats row ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

diff_color = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(difficulty, "⚪")
col1.metric("Difficulty", f"{diff_color} {difficulty.capitalize()}")
col2.metric("Correct ✓", correct)
col3.metric("Wrong ✗", wrong)
col4.metric("Accuracy", f"{accuracy:.0%}" if total > 0 else "N/A")

st.markdown("---")

# ── Two-column layout: chart + learning path ──────────────────────────────────
left, right = st.columns([1, 1])

with left:
    st.subheader("📊 Performance Chart")
    if total > 0:
        import pandas as pd
        chart_data = pd.DataFrame({
            "Category": ["Correct", "Wrong"],
            "Count": [correct, wrong],
        })
        st.bar_chart(chart_data.set_index("Category"))
    else:
        st.info("No answers recorded yet. Start a quiz!")

with right:
    st.subheader("🗺️ Learning Path")
    full_sequence = TOPIC_SEQUENCE + HARD_TOPICS
    last_topic    = profile["last_topic"]

    current_pos = 0
    if last_topic in full_sequence:
        current_pos = full_sequence.index(last_topic)

    for i, topic in enumerate(full_sequence[:current_pos + 3]):
        if i < current_pos:
            st.markdown(f"✅ ~~{topic}~~")
        elif i == current_pos:
            st.markdown(f"📍 **{topic}** ← You are here")
        else:
            st.markdown(f"⬜ {topic}")

    st.caption(get_topic_progress(profile))
    st.markdown(f"**Next suggested topic:** {next_topic}")

st.markdown("---")

# ── Quiz section ──────────────────────────────────────────────────────────────
st.subheader("🧠 Quiz")

session_col1, session_col2 = st.columns(2)
session_col1.metric("Session Correct", st.session_state.session_correct)
session_col2.metric("Session Wrong",   st.session_state.session_wrong)

if st.button("Get New Question"):
    st.session_state.current_question = generate_question(difficulty)
    st.session_state.answered         = False
    st.session_state.answer_result    = None

if st.session_state.current_question:
    q = st.session_state.current_question
    st.markdown(f"**Question [{difficulty.upper()}]:** {q['question']}")

    if not st.session_state.answered:
        user_ans = st.text_input("Your answer:", key="quiz_answer")
        if st.button("Submit Answer") and user_ans.strip():
            is_correct = check_answer(user_ans, q["answer"])
            st.session_state.answered      = True
            st.session_state.answer_result = is_correct

            if is_correct:
                st.session_state.session_correct += 1
                pm.update_progress(student_key, correct=1, wrong=0)
            else:
                st.session_state.session_wrong += 1
                pm.update_progress(student_key, correct=0, wrong=1)

            # Adjust difficulty after answer
            updated_profile = pm.get_student(student_key)
            new_diff        = adjust_difficulty(updated_profile)
            pm.update_difficulty(student_key, new_diff)
            pm.update_topic(student_key, next_topic)
            st.rerun()

    else:
        q = st.session_state.current_question
        if st.session_state.answer_result:
            st.success("✅ Correct!")
        else:
            st.error(f"❌ Wrong. Correct answer: **{q['answer']}**")

        # Refresh profile after update
        profile = pm.get_student(student_key)
        st.info(f"Difficulty is now: **{profile['difficulty'].upper()}**")

st.markdown("---")
st.caption("EduFlow AI – Adaptive Learning System | Week 19 Day 2")
