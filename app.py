"""
AI Code Explainer & Translator
A Streamlit app that auto-detects programming language and offers three output modes:
Explain, Pseudocode, and annotated translation.
"""

import hashlib
import os

import anthropic
import streamlit as st
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound

# ── Constants ──────────────────────────────────────────────────────────────────

MODEL = "claude-sonnet-4-20250514"
MAX_LINES = 500
TARGET_LANGUAGES = ["Python", "JavaScript", "TypeScript", "C++", "Java", "Go", "Rust", "SQL"]
SUPPORTED_EXTENSIONS = [
    "py", "js", "ts", "jsx", "tsx", "cpp", "c", "h", "cc", "cxx",
    "java", "go", "rs", "sql", "cs", "rb", "php", "swift", "kt",
    "r", "sh", "bash", "html", "css", "scala", "hs", "lua", "dart",
]

st.set_page_config(
    page_title="AI Code Explainer & Translator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Clean header area */
.main-header {
    padding-bottom: 0.5rem;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 12px 16px;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    font-weight: 500;
}

/* Buttons */
.stButton > button {
    font-weight: 600;
    border-radius: 6px;
}

/* Subtle section labels */
.section-label {
    font-size: 0.8rem;
    color: #6c757d;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
}

/* Warning box */
.stAlert {
    border-radius: 8px;
}

/* Code area */
.stTextArea textarea {
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.88rem;
}
</style>
""", unsafe_allow_html=True)

# ── Core Logic ─────────────────────────────────────────────────────────────────

def detect_language(code: str) -> str:
    """Auto-detect programming language using pygments."""
    try:
        return guess_lexer(code).name
    except ClassNotFound:
        return "Unknown"


def build_system_prompt(mode: str, src_lang: str, tgt_lang: str = "") -> str:
    """Return the appropriate system prompt for Claude based on output mode."""
    lang_ctx = f"The code is written in {src_lang}."

    if mode == "explain_high":
        return (
            f"You are an expert code analyst. {lang_ctx}\n\n"
            "Write ONE concise paragraph in plain English that covers:\n"
            "• What this program does\n"
            "• What problem it solves\n"
            "• Who would use it and why\n\n"
            "Target audience: someone who doesn't code. Avoid technical jargon. "
            "Be warm, clear, and direct. No bullet lists — just a well-written paragraph."
        )

    if mode == "explain_deep":
        return (
            f"You are an expert code analyst. {lang_ctx}\n\n"
            "Provide a detailed block-by-block breakdown of the code.\n"
            "For every significant function, class, module, or code section:\n"
            "  - Use a Markdown heading (e.g., ## `calculate_total()`)\n"
            "  - Explain what it does in plain English\n"
            "  - Explain WHY it exists and how it fits the overall program\n"
            "  - Note any important implementation decisions or patterns\n\n"
            "Target audience: a developer who can read code but wants deeper context and understanding."
        )

    if mode == "pseudocode":
        return (
            f"You are an expert at translating code into pseudocode. {lang_ctx}\n\n"
            "Convert the code into clean, readable pseudocode that a non-programmer can follow.\n"
            "Rules:\n"
            "  - No programming syntax (no braces, semicolons, type annotations, imports, etc.)\n"
            "  - Use plain English: 'FOR each item in list...', 'IF condition THEN...', 'REPEAT UNTIL...'\n"
            "  - Preserve logical hierarchy using indentation\n"
            "  - Show the logic and flow — not the implementation details\n"
            "  - Keep it concise but complete\n\n"
            "Format the pseudocode in a code block for readability."
        )

    if mode == "translate":
        return (
            f"You are an expert code translator and programming educator. {lang_ctx}\n\n"
            f"Translate the code to idiomatic {tgt_lang}.\n\n"
            "CRITICAL REQUIREMENT: Add inline comments explaining WHY specific changes were made — "
            "not just WHAT the code does. The goal is teaching, not just converting.\n\n"
            "Examples of excellent translation comments:\n"
            f'  # Python list comprehension → for loop (no direct equivalent in {tgt_lang})\n'
            '  // Explicit type required — unlike Python, this is statically typed\n'
            '  /* Using smart pointer — Python\'s garbage collector handles this automatically */\n\n'
            f"Write idiomatic, professional {tgt_lang} code. Do not do a literal line-by-line translation.\n"
            "The reader should understand both what changed and why it had to change."
        )

    return ""


def stream_claude(client: anthropic.Anthropic, code: str, system_prompt: str):
    """Generator that yields text chunks from Claude's streaming response."""
    with client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": f"```\n{code}\n```"}],
    ) as stream:
        yield from stream.text_stream


def render_output_actions(result: str, filename: str) -> None:
    """Show a copy-friendly expander and a download button below any result."""
    col_copy, col_dl = st.columns(2)
    with col_copy:
        with st.expander("Copy to clipboard"):
            st.code(result, language=None)
    with col_dl:
        st.download_button(
            label="Download as .txt",
            data=result,
            file_name=filename,
            mime="text/plain",
            use_container_width=True,
        )


# ── UI ─────────────────────────────────────────────────────────────────────────

def main() -> None:

    # ── Sidebar ─────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## AI Code Explainer")
        st.caption("Powered by Claude")
        st.divider()

        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=os.environ.get("ANTHROPIC_API_KEY", ""),
            placeholder="sk-ant-...",
            help="Get your key at console.anthropic.com",
        )

        st.divider()
        st.markdown("**Supported file types**")
        st.caption(
            ".py .js .ts .jsx .tsx .cpp .c .h .java .go .rs .sql "
            ".cs .rb .php .swift .kt .r .sh .html .css .scala .lua .dart"
        )
        st.divider()
        st.caption(f"Model: `{MODEL}`")
        st.caption(f"Max lines for full analysis: `{MAX_LINES}`")

    # ── Auth gate ────────────────────────────────────────────────────────────────
    if not api_key:
        st.title("AI Code Explainer & Translator")
        st.info(
            "Enter your Anthropic API key in the sidebar to get started. "
            "You can get one at [console.anthropic.com](https://console.anthropic.com)."
        )
        st.stop()

    client = anthropic.Anthropic(api_key=api_key)

    # ── Session state ────────────────────────────────────────────────────────────
    st.session_state.setdefault("results", {})
    st.session_state.setdefault("code_hash", None)

    # ── Header ───────────────────────────────────────────────────────────────────
    st.title("AI Code Explainer & Translator")
    st.caption(
        "Auto-detect any programming language · Plain English explanations · "
        "Pseudocode · Annotated translations"
    )
    st.divider()

    # ── Code Input ───────────────────────────────────────────────────────────────
    input_method = st.radio(
        "Input method",
        ["Paste code", "Upload file"],
        horizontal=True,
        label_visibility="collapsed",
    )

    code = ""

    if input_method == "Paste code":
        code_input = st.text_area(
            "Code",
            height=300,
            placeholder="# Paste your code here...",
            label_visibility="collapsed",
        )
        code = code_input.strip()

    else:
        uploaded = st.file_uploader(
            "Upload a code file",
            type=SUPPORTED_EXTENSIONS,
            label_visibility="collapsed",
        )
        if uploaded:
            try:
                code = uploaded.read().decode("utf-8").strip()
                with st.expander(f"Preview — {uploaded.name}", expanded=True):
                    preview = code[:3000] + ("\n\n... [truncated for preview]" if len(code) > 3000 else "")
                    st.code(preview, language="text")
            except UnicodeDecodeError:
                st.error("Could not read this file. Please upload a plain-text source file.")

    if not code:
        st.stop()

    # ── Language detection & invalidation ────────────────────────────────────────
    current_hash = hashlib.md5(code.encode()).hexdigest()
    if current_hash != st.session_state.code_hash:
        st.session_state.results = {}
        st.session_state.code_hash = current_hash

    detected_lang = detect_language(code)
    line_count = len(code.splitlines())
    char_count = len(code)

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Detected Language", detected_lang)
    m2.metric("Lines", f"{line_count:,}")
    m3.metric("Characters", f"{char_count:,}")

    # ── Long-file warning ────────────────────────────────────────────────────────
    working_code = code
    if line_count > MAX_LINES:
        st.warning(
            f"This file has **{line_count:,} lines**, which is over the recommended limit of {MAX_LINES}. "
            "Very large files may produce less focused results."
        )
        col_a, col_b = st.columns(2)
        with col_a:
            truncate = st.checkbox(
                f"Truncate to first {MAX_LINES} lines (top-level structure only)",
                help="Recommended for files over 500 lines to get a cleaner, faster result.",
            )
        if truncate:
            working_code = "\n".join(code.splitlines()[:MAX_LINES])
            st.info(f"Analyzing the first {MAX_LINES} lines only.")

    # ── Output Tabs ───────────────────────────────────────────────────────────────
    st.divider()
    tab_explain, tab_pseudo, tab_translate = st.tabs(["Explain", "Pseudocode", "Translate"])

    # ── TAB: EXPLAIN ──────────────────────────────────────────────────────────────
    with tab_explain:
        st.markdown("#### Plain English explanation")

        depth = st.radio(
            "Depth",
            ["High-level overview", "Deep-dive breakdown"],
            horizontal=True,
            help=(
                "**High-level:** One paragraph — what the program does, what problem it solves, who uses it.\n\n"
                "**Deep-dive:** Block-by-block breakdown of every function and class."
            ),
        )
        explain_key = f"explain_{depth}"

        gen_explain = st.button("Generate Explanation", key="btn_explain")

        if gen_explain:
            mode = "explain_high" if "High-level" in depth else "explain_deep"
            prompt = build_system_prompt(mode, detected_lang)
            try:
                result = st.write_stream(stream_claude(client, working_code, prompt))
                st.session_state.results[explain_key] = result
            except anthropic.AuthenticationError:
                st.error("Invalid API key. Please check your key in the sidebar.")
            except anthropic.RateLimitError:
                st.error("Rate limit reached. Please wait a moment and try again.")
            except anthropic.APIError as e:
                st.error(f"API error: {e.message}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

        elif st.session_state.results.get(explain_key):
            st.markdown(st.session_state.results[explain_key])

        if st.session_state.results.get(explain_key):
            st.divider()
            render_output_actions(st.session_state.results[explain_key], "code_explanation.txt")

    # ── TAB: PSEUDOCODE ───────────────────────────────────────────────────────────
    with tab_pseudo:
        st.markdown("#### Readable pseudocode")
        st.caption("Plain logic without any programming syntax — readable by anyone.")

        gen_pseudo = st.button("Generate Pseudocode", key="btn_pseudo")

        if gen_pseudo:
            prompt = build_system_prompt("pseudocode", detected_lang)
            try:
                result = st.write_stream(stream_claude(client, working_code, prompt))
                st.session_state.results["pseudocode"] = result
            except anthropic.AuthenticationError:
                st.error("Invalid API key. Please check your key in the sidebar.")
            except anthropic.RateLimitError:
                st.error("Rate limit reached. Please wait a moment and try again.")
            except anthropic.APIError as e:
                st.error(f"API error: {e.message}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

        elif st.session_state.results.get("pseudocode"):
            st.markdown(st.session_state.results["pseudocode"])

        if st.session_state.results.get("pseudocode"):
            st.divider()
            render_output_actions(st.session_state.results["pseudocode"], "pseudocode.txt")

    # ── TAB: TRANSLATE ────────────────────────────────────────────────────────────
    with tab_translate:
        st.markdown("#### Annotated code translation")
        st.caption(
            "Translates your code to another language and adds inline comments explaining "
            "**why** things changed — a learning tool, not just a converter."
        )

        tgt_lang = st.selectbox("Target language", TARGET_LANGUAGES)
        translate_key = f"translate_{tgt_lang}"

        gen_translate = st.button("Translate", key="btn_translate")

        if gen_translate:
            prompt = build_system_prompt("translate", detected_lang, tgt_lang)
            try:
                result = st.write_stream(stream_claude(client, working_code, prompt))
                st.session_state.results[translate_key] = result
            except anthropic.AuthenticationError:
                st.error("Invalid API key. Please check your key in the sidebar.")
            except anthropic.RateLimitError:
                st.error("Rate limit reached. Please wait a moment and try again.")
            except anthropic.APIError as e:
                st.error(f"API error: {e.message}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

        elif st.session_state.results.get(translate_key):
            st.markdown(st.session_state.results[translate_key])

        if st.session_state.results.get(translate_key):
            st.divider()
            safe_name = tgt_lang.lower().replace("+", "p").replace("#", "sharp").replace(" ", "_")
            render_output_actions(
                st.session_state.results[translate_key],
                f"translated_to_{safe_name}.txt",
            )


if __name__ == "__main__":
    main()
