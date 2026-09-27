"""PocketPlate's two page themes and small presentation helpers."""
from html import escape
import streamlit as st


def apply_theme(page):
    planner = page == 'Meal Planner'
    palette = (
        ('#F8F7F0', '#E8EEDC', '#173E31', '#DCEAB6', '#F5D9C6', '#D5DDCB', '#F1F4E9', '#315E44')
        if planner else
        ('#F5F9FF', '#E3EEFB', '#172B4D', '#FFE17D', '#D7E9FF', '#CEDCEE', '#EDF4FC', '#0369A1')
    )
    bg, side, ink, accent, soft, line, field, primary = palette
    
    
    css = '''
    [data-testid="stSidebar"] [data-testid="stRadio"] label,
    [data-testid="stSidebar"] [data-testid="stRadio"] label p {
        color: var(--pp-ink) !important;
        font-size: 17px !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }

    [data-testid="stSpinner"] {
        color: var(--pp-ink) !important;
    }
    
    [data-testid="stSpinner"] > div:first-child {
        border-color: var(--pp-line) !important;
        border-top-color: var(--pp-ink) !important;
    }
    <style>
    :root { --pp-bg: BG; --pp-side: SIDE; --pp-ink: INK; --pp-accent: ACCENT;
        --pp-soft: SOFT; --pp-line: LINE; --pp-field: FIELD; --pp-primary: PRIMARY; }
    [data-testid="stAppViewContainer"], [data-testid="stMain"] {background:var(--pp-bg);color:var(--pp-ink)}
    [data-testid="stHeader"] {background:var(--pp-bg)}
    [data-testid="stMainBlockContainer"] {padding-top:3.6rem;padding-bottom:3rem;max-width:1250px}
    [data-testid="stSidebar"] {background:var(--pp-side);border-right:1px solid var(--pp-line)}
    [data-testid="stSidebarUserContent"] {padding-top:0}
    [data-testid="stSidebarCollapseButton"], [data-testid="stExpandSidebarButton"] {visibility:visible!important;opacity:1!important}
    /* Keep ordinary text comfortable while native grid headings use the theme's heavier base weight. */
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
    input, textarea, [data-baseweb="select"] {font-weight:400}
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
    [data-testid="stCaptionContainer"] li, [data-testid="stCaptionContainer"] span,
    [data-testid="stImageCaption"] {font-size:1rem!important;line-height:1.6!important;font-weight:600!important;color:var(--pp-ink)!important;opacity:1!important}
    [data-testid="stTable"] th {font-size:1rem!important;font-weight:750!important;color:var(--pp-ink)!important;background:var(--pp-field)!important}
    [data-testid="stTable"] td {font-size:1rem;font-weight:400;color:var(--pp-ink)}
    [data-testid="stWidgetLabel"] p {font-size:1rem!important}
    [data-testid="stExpander"] summary p {font-size:1rem!important;font-weight:650!important}
    [data-testid="stImage"] {box-sizing:border-box;border:2px solid var(--pp-ink);border-radius:18px;padding:14px;background:#fff;box-shadow:3px 3px 0 var(--pp-line)}
    [data-testid="stImageCaption"] {margin-top:10px}
    .pp-nutrient small {font-size:1rem!important;font-weight:600;color:var(--pp-ink)!important}
    .pp-step {font-size:15px!important}.pp-step small {font-size:14px!important;font-weight:600!important}
    .pp-side-note {font-size:15px!important}.pp-tagline {font-size:16px!important}
    h1,h2,h3 {color:var(--pp-ink)!important;letter-spacing:-.035em}
    h2 {font-size:1.65rem!important} h3 {font-size:1.25rem!important}
    [data-testid="stCaptionContainer"] p {font-weight:600;color:#4D5D61}
    [data-testid="stWidgetLabel"] p {font-weight:650;color:var(--pp-ink)}
    [data-testid="stSidebar"] [data-testid="stRadio"] > label p {font-size:20px;font-weight:800}
    [data-testid="stSidebar"] [role="radiogroup"] {gap:10px}
    [data-testid="stSidebar"] [role="radiogroup"] label {padding:12px 14px;border-radius:14px;border:1px solid var(--pp-line);background:#ffffff90}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:var(--pp-accent);border-color:var(--pp-ink);box-shadow:3px 3px 0 var(--pp-ink)}
    [data-testid="stForm"] {background:#fff;border:1px solid var(--pp-line);border-radius:22px;padding:24px}
    [data-testid="stExpander"] {background:#ffffffb8;border-radius:18px}
    [data-testid="stMetric"] {background:#fff;border:1px solid var(--pp-line);border-radius:18px;padding:18px 20px;border-top:5px solid var(--pp-accent)}
    [data-testid="stMetricValue"] {color:var(--pp-ink);font-size:1.9rem;font-weight:750}
    [data-testid="stMetricLabel"] p {font-weight:650}
    [data-testid="stNumberInput"] [data-baseweb="input"],
    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {background:var(--pp-field)!important;border-radius:10px;border-color:var(--pp-line)!important}
    [data-testid="stFileUploaderDropzone"] {background:var(--pp-field);border:2px dashed var(--pp-primary);border-radius:20px;padding:24px}
    [data-testid="stFileUploader"] > label p {font-size:20px;font-weight:750}
    [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button,
    [data-testid="stDownloadButton"] button, [data-testid="stFileUploaderDropzone"] button {
        border:1.5px solid var(--pp-ink)!important;border-radius:12px!important;padding:10px 20px;
        color:var(--pp-ink)!important;background:var(--pp-accent)!important;
        box-shadow:3px 3px 0 var(--pp-ink);transition:transform .15s,box-shadow .15s;margin-bottom:6px}
    [data-testid="stButton"] button p, [data-testid="stFormSubmitButton"] button p,
    [data-testid="stDownloadButton"] button p, [data-testid="stFileUploaderDropzone"] button p {font-weight:800;color:var(--pp-ink)!important}
    [data-testid="stButton"] button:hover:not(:disabled), [data-testid="stFormSubmitButton"] button:hover:not(:disabled),
    [data-testid="stDownloadButton"] button:hover:not(:disabled), [data-testid="stFileUploaderDropzone"] button:hover:not(:disabled) {transform:translate(-1px,-2px);box-shadow:4px 5px 0 var(--pp-ink)}
    [data-testid="stButton"] button:active:not(:disabled), [data-testid="stFormSubmitButton"] button:active:not(:disabled),
    [data-testid="stDownloadButton"] button:active:not(:disabled) {transform:translate(2px,2px);box-shadow:1px 1px 0 var(--pp-ink)}
    button:focus-visible {outline:3px solid var(--pp-primary)!important;outline-offset:4px}
    button:disabled {opacity:.5;box-shadow:none!important}
    [data-testid="stImage"] img {border-radius:16px;max-height:330px;object-fit:contain}
    [data-testid="stDataFrame"], [data-testid="stTable"] {border-radius:14px;overflow:hidden;border:1px solid var(--pp-line)}
    .pp-brand {font-size:29px;font-weight:850;letter-spacing:-1px;color:var(--pp-ink);margin:2px 0}
    .pp-tagline {font-size:14px;font-weight:650;margin:0 0 28px 4px;color:var(--pp-ink)}
    .pp-eyebrow {font-size:12px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
    .pp-hero {position:relative;border:1.5px solid var(--pp-ink);border-radius:26px;padding:34px 36px;margin-bottom:22px;background:var(--pp-soft);box-shadow:5px 5px 0 var(--pp-ink);overflow:hidden}
    .pp-hero h1 {font-size:clamp(32px,4vw,55px)!important;line-height:1.06;margin:14px 0!important;padding:0!important;max-width:700px;font-weight:850}
    .pp-hero p {font-size:17px;max-width:620px;margin:0;line-height:1.55;color:var(--pp-ink)}
    .pp-pill {display:inline-block;background:var(--pp-accent);border:1px solid var(--pp-ink);border-radius:99px;padding:6px 11px;font-size:12px;font-weight:800;margin:18px 7px 0 0}
    .pp-steps {display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:4px 0 24px}
    .pp-step {border:1px solid var(--pp-line);background:#fff;border-radius:13px;padding:12px;font-size:13px;font-weight:700}
    .pp-step.done {background:var(--pp-accent);border-color:var(--pp-ink)}
    .pp-step small {display:block;font-weight:500;margin-top:3px}
    .pp-side-note {border-top:1px solid var(--pp-line);padding-top:18px;margin-top:28px;font-size:13px;line-height:1.6;color:var(--pp-ink)}
    .pp-meter {height:8px;background:var(--pp-field);border-radius:99px;overflow:hidden;margin:10px 0}
    .pp-meter span {display:block;height:100%;background:var(--pp-primary);border-radius:99px}
    .pp-nutrient {background:white;padding:18px;border:1px solid var(--pp-line);border-radius:16px;margin-bottom:12px}
    .pp-nutrient strong {font-size:23px}.pp-nutrient small {color:#4D5D61}
    @media(max-width:700px) { [data-testid="stMainBlockContainer"]{padding:3.5rem 1rem 2rem}.pp-hero{padding:24px}.pp-steps{grid-template-columns:repeat(2,1fr)} }
    @media(prefers-reduced-motion:reduce) {button {transition:none!important;transform:none!important}}
    </style>
    '''
    import re
    mapping = dict(zip(['BG','SIDE','INK','ACCENT','SOFT','LINE','FIELD','PRIMARY'], palette))
    css = re.sub(r'\b(BG|SIDE|INK|ACCENT|SOFT|LINE|FIELD|PRIMARY)\b', lambda m: mapping[m.group()], css)
    st.markdown(css, unsafe_allow_html=True)


def hero(page):
    if page == 'Meal Planner':
        eyebrow, title, text = ('THE EVERYDAY FOOD PLAN', 'Good food.<br>Better budget.', 'Build a practical food plan around your routine, your preferences, and what you want to spend.')
        pills = ['Your goals', 'Local prices', 'A plan to take away']
    else:
        eyebrow, title, text = ('YOUR LABEL, MADE SIMPLE', 'Small print.<br>Big clarity.', 'Scan a food label, understand the numbers, and see what is in the portion you actually eat.')
        pills = ['Read the label', 'Check your portion', 'Know your food']
    st.markdown(f'<section class="pp-hero"><div class="pp-eyebrow">{eyebrow}</div><h1>{title}</h1><p>{text}</p>'+''.join(f'<span class="pp-pill">{p}</span>' for p in pills)+'</section>', unsafe_allow_html=True)


def planner_steps():
    entries = [('01 · Profile','Your routine','personal_profile'),('02 · Targets','Your nutrition','nutrition_targets'),('03 · Prices','Your local shop','food_catalogue'),('04 · Plan','Your daily portions','meal_plan')]
    st.markdown('<div class="pp-steps">'+''.join(f'<div class="pp-step {"done" if st.session_state.get(key) else ""}">{title}<small>{"Saved · " if st.session_state.get(key) else ""}{desc}</small></div>' for title,desc,key in entries)+'</div>', unsafe_allow_html=True)


def nutrient_cards(plan, targets):
    entries = [('Calories','calories',targets['calories'],'kcal'),('Protein','protein_g',targets['protein'],'g')]
    if targets.get('fibre') is not None:
        entries.append(('Fibre','fibre_g',targets['fibre'],'g'))
    for col,(name,key,goal,unit) in zip(st.columns(len(entries)),entries):
        actual = float(plan['totals'][key])
        percent = min(100,max(0,actual / goal * 100)) if goal > 0 else 0
        difference = actual-goal
        status = f'{abs(difference):.1f} {unit} '+('below target' if difference < -0.05 else 'above target' if difference > .05 else 'difference')
        with col:
            st.markdown(f'<div class="pp-nutrient"><div class="pp-eyebrow">{name}</div><strong>{actual:.1f}</strong> <small>{unit} / {goal:g} target</small><div class="pp-meter"><span style="width:{percent}%"></span></div><small>{escape(status)}</small></div>', unsafe_allow_html=True)
