"""Premium UI styling for the Streamlit app."""

PREMIUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

:root {
    --bg-deep: #06080f;
    --bg-card: rgba(14, 18, 32, 0.72);
    --bg-card-hover: rgba(20, 26, 46, 0.88);
    --border: rgba(255, 255, 255, 0.08);
    --border-glow: rgba(99, 102, 241, 0.35);
    --text: #f4f6fb;
    --text-muted: #9aa3b8;
    --accent: #818cf8;
    --accent-2: #22d3ee;
    --success: #34d399;
    --gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 45%, #22d3ee 100%);
}

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    color: var(--text);
}

.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(99, 102, 241, 0.18), transparent 28%),
        radial-gradient(circle at 85% 0%, rgba(34, 211, 238, 0.12), transparent 24%),
        radial-gradient(circle at 50% 100%, rgba(139, 92, 246, 0.10), transparent 30%),
        linear-gradient(180deg, #06080f 0%, #0b1020 45%, #070a14 100%);
    animation: bgShift 12s ease-in-out infinite alternate;
}

@keyframes bgShift {
    0% { background-position: 0% 0%, 100% 0%, 50% 100%, 0% 0%; }
    100% { background-position: 5% 3%, 95% 2%, 50% 98%, 0% 0%; }
}

#MainMenu, footer, header { visibility: hidden; }
.block-container {
    max-width: 980px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero-wrap {
    text-align: center;
    padding: 2.4rem 1.5rem 2rem;
    margin-bottom: 1.5rem;
    border: 1px solid var(--border);
    border-radius: 28px;
    background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255,255,255,0.05);
    animation: fadeUp 0.8s ease both;
    position: relative;
    overflow: hidden;
}

.hero-wrap::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(120deg, transparent 30%, rgba(129,140,248,0.08) 50%, transparent 70%);
    transform: translateX(-120%);
    animation: shimmer 4.5s ease-in-out infinite;
}

.hero-badge {
    display: inline-block;
    padding: 0.35rem 0.9rem;
    border-radius: 999px;
    border: 1px solid rgba(129, 140, 248, 0.35);
    background: rgba(99, 102, 241, 0.12);
    color: #c7d2fe;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.2rem, 5vw, 3.4rem);
    line-height: 1.05;
    margin: 0;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    color: var(--text-muted);
    font-size: 1.05rem;
    max-width: 620px;
    margin: 0.95rem auto 0;
    line-height: 1.65;
}

.section-card {
    padding: 1.35rem 1.25rem 0.4rem;
    margin: 1rem 0 1.4rem;
    border-radius: 22px;
    border: 1px solid var(--border);
    background: var(--bg-card);
    backdrop-filter: blur(14px);
    box-shadow: 0 10px 40px rgba(0,0,0,0.22);
    animation: fadeUp 0.7s ease both;
    transition: border-color 0.25s ease, transform 0.25s ease, background 0.25s ease;
}

.section-card:hover {
    border-color: var(--border-glow);
    background: var(--bg-card-hover);
    transform: translateY(-2px);
}

.section-card.delay-1 { animation-delay: 0.08s; }
.section-card.delay-2 { animation-delay: 0.16s; }
.section-card.delay-3 { animation-delay: 0.24s; }
.section-card.delay-4 { animation-delay: 0.32s; }

.section-title {
    font-size: 0.82rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #a5b4fc;
    margin: 0 0 0.35rem 0;
    font-weight: 600;
}

.section-heading {
    font-size: 1.35rem;
    margin: 0 0 0.2rem 0;
    font-weight: 600;
}

.section-copy {
    color: var(--text-muted);
    font-size: 0.92rem;
    margin: 0 0 0.8rem 0;
}

.stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.55rem 0.9rem;
    border-radius: 999px;
    background: rgba(52, 211, 153, 0.10);
    border: 1px solid rgba(52, 211, 153, 0.25);
    color: #6ee7b7;
    font-size: 0.92rem;
    animation: pulseGlow 2.4s ease-in-out infinite;
}

.footer-note {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.86rem;
    margin-top: 2rem;
    padding: 1rem;
    border-top: 1px solid var(--border);
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(18px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes shimmer {
    0% { transform: translateX(-120%); }
    50% { transform: translateX(120%); }
    100% { transform: translateX(120%); }
}

@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 0 rgba(52, 211, 153, 0); }
    50% { box-shadow: 0 0 24px rgba(52, 211, 153, 0.18); }
}

div.stButton > button {
    border-radius: 14px !important;
    border: 1px solid rgba(129, 140, 248, 0.35) !important;
    background: linear-gradient(135deg, rgba(99,102,241,0.95), rgba(139,92,246,0.92)) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.72rem 1.2rem !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease !important;
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.28) !important;
}

div.stButton > button:hover {
    transform: translateY(-2px) scale(1.01) !important;
    box-shadow: 0 16px 36px rgba(99, 102, 241, 0.38) !important;
    filter: brightness(1.05) !important;
}

div.stDownloadButton > button {
    border-radius: 14px !important;
    border: 1px solid rgba(34, 211, 238, 0.35) !important;
    background: rgba(34, 211, 238, 0.12) !important;
    color: #a5f3fc !important;
}

.stTextInput > div > div > input,
.stTextArea textarea,
.stSelectbox > div > div,
div[data-baseweb="select"] {
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    background: rgba(255,255,255,0.03) !important;
    color: var(--text) !important;
}

.stFileUploader > div {
    border-radius: 16px !important;
    border: 1px dashed rgba(129, 140, 248, 0.35) !important;
    background: rgba(255,255,255,0.02) !important;
    transition: border-color 0.25s ease, background 0.25s ease !important;
}

.stFileUploader > div:hover {
    border-color: rgba(34, 211, 238, 0.55) !important;
    background: rgba(34, 211, 238, 0.04) !important;
}

.stProgress > div > div > div > div {
    background: var(--gradient) !important;
}

.stImage img {
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 20px 50px rgba(0,0,0,0.35);
    animation: fadeUp 0.6s ease both;
}

div[data-testid="stAlert"] {
    border-radius: 14px;
    animation: fadeUp 0.45s ease both;
}
</style>
"""


def render_hero() -> None:
    import streamlit as st

    st.markdown(
        """
        <div class="hero-wrap">
            <div class="hero-badge">Automated Certificate Delivery</div>
            <h1 class="hero-title">Certi Sender</h1>
            <p class="hero-sub">
                Upload your template, add participants, and let the platform personalize
                and deliver every certificate while you focus on the event.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_card(title: str, heading: str, copy: str, delay_class: str = "") -> None:
    import streamlit as st

    st.markdown(
        f"""
        <div class="section-card {delay_class}">
            <p class="section-title">{title}</p>
            <h2 class="section-heading">{heading}</h2>
            <p class="section-copy">{copy}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
