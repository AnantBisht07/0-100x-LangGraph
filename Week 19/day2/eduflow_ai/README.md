# EduFlow AI – Adaptive Learning System

A modular Python project that demonstrates how to build adaptive AI systems using persistent memory and student profiles — **without any LLM or external API**.

---

## Why No `.env` or LLM API Key?

Most AI projects require an API key (e.g. OpenAI, Anthropic) because they send prompts to a hosted language model to generate responses. **EduFlow AI does not do this.**

Here is why:

| Capability | How EduFlow handles it |
|---|---|
| Question generation | Pre-written question banks in `quiz_engine.py` |
| Difficulty adjustment | Rule-based accuracy thresholds in `difficulty_manager.py` |
| Learning path | Ordered topic sequence + conditional logic in `learning_path.py` |
| Memory / persistence | JSON file (`data/students.json`) read and written locally |
| Personalization | Profile lookup + arithmetic (accuracy = correct / total) |

Every decision the system makes — adapt the difficulty, suggest the next topic, pick a question — is computed locally using **pure Python logic and a JSON file**. There is no network call, no prompt, no token, no model.

> This is intentional. The goal of this project is to teach the *architecture* of adaptive systems: persistent memory, feedback loops, and personalization. You do not need a language model to build intelligent, adaptive behavior.

---

## Project Structure

```
eduflow_ai/
├── data/
│   └── students.json        # Persistent student profiles
├── profile_manager.py       # Load, save, create, update profiles
├── quiz_engine.py           # Question banks for easy / medium / hard
├── difficulty_manager.py    # Adaptive difficulty logic (rule-based)
├── learning_path.py         # 21-topic learning progression
├── eduflow_core.py          # Main pipeline orchestrator
├── main.py                  # CLI entry point
├── streamlit_app.py         # Bonus: browser dashboard
└── requirements.txt         # streamlit + pandas only
```

---

## Installation

```bash
pip install -r requirements.txt
```

No API keys. No `.env`. No sign-ups.

---

## Running the App

**CLI:**
```bash
python main.py
```

**Streamlit dashboard:**
```bash
streamlit run streamlit_app.py
```

---

## How Adaptive Behavior Works

```
Student answers a question
        ↓
accuracy = correct_answers / total_answers
        ↓
accuracy > 80%  →  difficulty moves UP
accuracy < 50%  →  difficulty moves DOWN
otherwise       →  difficulty stays the same
        ↓
Profile saved to students.json
        ↓
Next session loads updated profile automatically
```

The system re-evaluates difficulty **after every single answer**, so adaptation happens in real time within a session.

---

## Demo Students

Three pre-loaded profiles demonstrate different learning paths:

| Student | Difficulty | Accuracy | Next Topic |
|---|---|---|---|
| Rahul | Easy | New student | Variables and Data Types |
| Priya | Medium | 80% | Conditionals |
| Aman | Hard | 83% | Lists and Tuples |

Same system — three completely different learning experiences.

---

## Key Concepts Demonstrated

- **Persistent memory** — profiles survive across sessions via JSON
- **Adaptive difficulty** — accuracy-driven feedback loop
- **Multi-student personalization** — isolated profiles per student
- **Learning path generation** — rule-based topic progression
- **Modular architecture** — each concern in its own file

---

*Week 19 – Day 2 | EduFlow AI*
