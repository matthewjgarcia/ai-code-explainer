# AI Code Explainer & Translator

A web app that takes any code file, auto-detects the programming language, and transforms it into three types of output — plain English explanations, pseudocode, and annotated translations into another language. Built as a practical tool for developers, students, and anyone trying to understand code they didn't write.

---

## What it does

Paste any code or upload a file and choose from three modes:

**Explain** — Two depth levels you can toggle between:
- *High-level*: A single plain-English paragraph describing what the program does, what problem it solves, and who would use it
- *Deep-dive*: A block-by-block breakdown of every function and class, explaining what each piece does and why it exists

**Pseudocode** — Converts the code into clean, readable logic with no syntax. No brackets, no semicolons — just the flow of the program in plain English that anyone can follow.

**Translate** — Converts the code into a target language of your choice (Python, JavaScript, TypeScript, C++, Java, Go, Rust, or SQL) and adds inline comments explaining *why* specific things changed during translation. For example: *"Python list comprehension → for loop because C++ has no direct equivalent."* The goal is learning, not just converting.

All outputs can be copied to clipboard or downloaded as a `.txt` file.

---

## High Level

> Paste or upload code → auto-detect language → pick a mode → get instant details

**Supported input formats:** `.py` `.js` `.ts` `.jsx` `.tsx` `.cpp` `.c` `.h` `.java` `.go` `.rs` `.sql` `.cs` `.rb` `.php` `.swift` `.kt` `.r` `.sh` `.html` `.css` `.scala` `.lua` `.dart`

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend / UI | [Streamlit](https://streamlit.io) |
| AI model | Claude (`claude-sonnet-4-20250514`) via [Anthropic API](https://docs.anthropic.com) |
| Language detection | [Pygments](https://pygments.org) (`guess_lexer`) |
| Streaming | `client.messages.stream()` → `st.write_stream()` |

---

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/matthewjgarcia/ai-code-explainer.git
cd ai-code-explainer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your Anthropic API key

Get a key at [console.anthropic.com](https://console.anthropic.com), then either:

**Option A — environment variable (recommended):**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**Option B — enter it in the app sidebar** when the app is running.

### 4. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Project highlights

This project demonstrates several practical skills:

- **File upload + text input handling** in a Streamlit UI
- **Language auto-detection** using the Pygments lexer library
- **Dynamic system prompts** — the prompt sent to Claude changes depending on the selected mode and detected language
- **Streaming responses** — output appears token-by-token rather than waiting for the full response
- **Session state management** — results are cached per mode so switching tabs doesn't clear your output
- **Clean error handling** — typed Anthropic exceptions with user-facing messages for auth errors, rate limits, and API failures
- **Secure API key handling** — key is read from an environment variable or a masked sidebar input; never hardcoded

---

## How the AI prompting works

Each mode sends a different system prompt to Claude along with the detected language name and the full code as context:

| Mode | What Claude is instructed to do |
|---|---|
| Explain (high-level) | Write one plain-English paragraph: what it does, what problem it solves, who uses it |
| Explain (deep-dive) | Break down every function/class with headings, explain what each does and why it exists |
| Pseudocode | Convert to syntax-free logic using plain English flow constructs |
| Translate | Rewrite in the target language idiomatically, with inline comments explaining *why* each change was made |

---

## Future improvements (v2)

- PDF export of any output
- Usage-based rate limiting (free tier / paid tier)
- Support for multi-file uploads or GitHub repo URLs
- Diff view for translate mode (side-by-side original vs. translated)

---

