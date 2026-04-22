import uuid
import os
import tempfile
from datetime import date, timedelta
from urllib.parse import quote
import re
import streamlit as st
import streamlit.components.v1 as components
from langchain_core.messages import HumanMessage

from agents.agent import Agent

st.set_page_config(
    page_title="Voyager AI - Travel Planner",
    page_icon="🌍",
    layout="wide"
)


def initialize_agent():
    if 'agent' not in st.session_state:
        st.session_state.agent = Agent()


def initialize_theme():
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'


def get_theme_vars():
    dark = st.session_state.theme == 'dark'
    return {
        'is_dark': dark,
        'bg': '#0a0f1e' if dark else '#f0f4ff',
        'card_bg': '#ffffff',
        'card_border': '#e2e8f0',
        'text': '#1e293b',
        'text_muted': '#64748b',
        'input_bg': '#f8faff',
        'input_border': '#e2e8f0',
        'section_bg': '#0f172a' if dark else '#f8fafc',
        'section_text': '#ffffff' if dark else '#0f172a',
        'form_section_bg': '#0a0f1e' if dark else '#f0f4ff',
    }


def render_css():
    t = get_theme_vars()
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        margin: 0; padding: 0;
    }}
    .stApp {{
        background: {t['bg']};
        min-height: 100vh;
    }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{
        padding: 0 !important;
        max-width: 100% !important;
    }}
    div[data-testid="stTextInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stNumberInput"] input {{
        background: {t['input_bg']} !important;
        border: 1.5px solid {t['input_border']} !important;
        border-radius: 10px !important;
        color: {t['text']} !important;
        font-size: 0.95rem !important;
    }}
    div[data-testid="stTextInput"] input::placeholder {{ color: #94a3b8 !important; }}
    div[data-testid="stSelectbox"] > div > div {{
        background: {t['input_bg']} !important;
        border: 1.5px solid {t['input_border']} !important;
        border-radius: 10px !important;
        color: {t['text']} !important;
    }}
    textarea {{
        background: {t['input_bg']} !important;
        border: 1.5px solid {t['input_border']} !important;
        border-radius: 10px !important;
        color: {t['text']} !important;
        font-size: 0.9rem !important;
        resize: none !important;
    }}
    textarea::placeholder {{ color: #94a3b8 !important; }}
    .stButton > button {{
        width: 100%;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        background: linear-gradient(135deg, #6366f1, #0ea5e9) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 6px 20px rgba(99,102,241,0.35) !important;
        margin-top: 0.5rem !important;
        transition: all 0.25s ease !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 32px rgba(99,102,241,0.5) !important;
    }}
    .result-card {{
        background: white;
        border: 1.5px solid #e2e8f0;
        border-radius: 20px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    }}
    .card-header {{
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: #6366f1;
        margin-bottom: 1.2rem;
        padding-bottom: 1rem;
        border-bottom: 1.5px solid #e2e8f0;
    }}
    .btn-link {{
        display: block;
        background: linear-gradient(135deg, #6366f1, #818cf8);
        color: white !important;
        padding: 0.75rem 1.4rem;
        border-radius: 10px;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 0.88rem;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(99,102,241,0.25);
    }}
    .btn-secondary {{
        background: linear-gradient(135deg, #10b981, #34d399) !important;
    }}
    .stSpinner > div {{ border-top-color: #6366f1 !important; }}
    </style>
    """, unsafe_allow_html=True)


def render_navbar():
    col1, col2, col3 = st.columns([3, 6, 3])
    with col1:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.8rem;padding-top:0.8rem;">
            <div style="width:38px;height:38px;background:linear-gradient(135deg,#6366f1,#0ea5e9);
                        border-radius:10px;display:flex;align-items:center;
                        justify-content:center;font-size:1.1rem;">🌍</div>
            <div>
                <div style="font-weight:700;font-size:1rem;color:#1e293b;">Voyager AI</div>
                <div style="font-size:0.68rem;color:#6366f1;font-weight:500;">Travel Planner</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:center;
                    gap:2rem;padding-top:1.1rem;">
            <span style="color:#64748b;font-size:0.9rem;font-weight:500;">Home</span>
            <span style="color:#64748b;font-size:0.9rem;font-weight:500;">Features</span>
            <span style="color:#64748b;font-size:0.9rem;font-weight:500;">About</span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        theme = st.session_state.theme
        b1, b2 = st.columns([2, 1])
        with b1:
            label = "☀️ Light Mode" if theme == 'dark' else "🌙 Dark Mode"
            if st.button(label, key="theme_toggle"):
                st.session_state.theme = 'light' if theme == 'dark' else 'dark'
                st.rerun()
        with b2:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#6366f1,#0ea5e9);color:white;
                        padding:0.5rem 1rem;border-radius:8px;font-weight:600;
                        font-size:0.85rem;text-align:center;margin-top:0.7rem;">
                Get Started
            </div>
            """, unsafe_allow_html=True)


def render_hero():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0a0f1e 0%,#0f172a 60%,#0a1628 100%);
                padding:8rem 2rem 5rem;text-align:center;position:relative;
                overflow:hidden;min-height:480px;display:flex;flex-direction:column;
                align-items:center;justify-content:center;">
        <div style="position:absolute;left:5%;top:40%;font-size:2.5rem;opacity:0.3;transform:rotate(-20deg);">✈️</div>
        <div style="position:absolute;right:5%;top:35%;font-size:2.5rem;opacity:0.3;transform:rotate(20deg);">✈️</div>
        <div style="display:inline-block;background:rgba(99,102,241,0.2);
                    border:1px solid rgba(99,102,241,0.4);color:#a5b4fc;
                    padding:0.4rem 1.2rem;border-radius:50px;font-size:0.78rem;
                    font-weight:600;letter-spacing:0.15em;text-transform:uppercase;
                    margin-bottom:1.5rem;position:relative;z-index:1;">
            ✦ AI-Powered Travel Planning
        </div>
        <h1 style="font-family:'Playfair Display',serif;font-size:clamp(2.8rem,6vw,4.5rem);
                   font-weight:700;color:white;line-height:1.15;margin-bottom:1.2rem;
                   position:relative;z-index:1;">
            Your Perfect Journey,<br>
            <span style="background:linear-gradient(90deg,#6366f1,#38bdf8);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                         background-clip:text;">Instantly Planned</span>
        </h1>
        <p style="color:#94a3b8;font-size:1.05rem;max-width:560px;line-height:1.7;
                  margin:0 auto;position:relative;z-index:1;font-family:'Inter',sans-serif;">
            Real-time flights, luxury hotels, interactive maps, weather forecasts
            and curated attractions — all powered by AI.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_trip_cards():
    t = get_theme_vars()
    trips = [
        {"img": "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=400",
         "icon": "✈️", "title": "Madrid → Amsterdam", "sub": "Explore the charming canals"},
        {"img": "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=400",
         "icon": "🏨", "title": "5⭐ Paris luxury",    "sub": "Experience luxury in Paris"},
        {"img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400",
         "icon": "🌴", "title": "Bali 7-day escape",  "sub": "Tropical paradise awaits"},
        {"img": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=400",
         "icon": "🗽", "title": "NYC weekend vibe",   "sub": "The city that never sleeps"},
        {"img": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=400",
         "icon": "🏯", "title": "Tokyo adventure",    "sub": "Discover Japan's culture"},
        {"img": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?w=400",
         "icon": "🏖️", "title": "Maldives honeymoon","sub": "Romantic island getaway"},
    ]
    cards_html = ""
    for trip in trips:
        cards_html += f"""
        <div style="position:relative;height:200px;border-radius:16px;overflow:hidden;
                    cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,0.2);">
            <img src="{trip['img']}" style="width:100%;height:100%;object-fit:cover;" />
            <div style="position:absolute;inset:0;background:linear-gradient(to top,
                        rgba(0,0,0,0.85) 0%,rgba(0,0,0,0.2) 60%,transparent 100%);"></div>
            <div style="position:absolute;top:12px;left:12px;width:30px;height:30px;
                        background:rgba(255,255,255,0.2);border-radius:8px;display:flex;
                        align-items:center;justify-content:center;font-size:0.9rem;">
                {trip['icon']}</div>
            <div style="position:absolute;bottom:14px;left:14px;right:14px;">
                <div style="font-weight:700;font-size:0.9rem;color:white;
                            margin-bottom:0.2rem;">{trip['title']}</div>
                <div style="font-size:0.75rem;color:#cbd5e1;">{trip['sub']}</div>
            </div>
        </div>"""

    components.html(f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <div style="background:{t['section_bg']};padding:2.5rem 2rem 3rem;font-family:'Inter',sans-serif;">
        <div style="max-width:1100px;margin:0 auto;">
            <div style="font-weight:700;font-size:1.1rem;color:{t['section_text']};margin-bottom:1.5rem;">
                ✦ Popular Trips</div>
            <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:1rem;">
                {cards_html}
            </div>
        </div>
    </div>
    """, height=320)


def render_features():
    t = get_theme_vars()
    features = [
        {"icon": "🕐", "bg": "#dbeafe", "title": "Real-time Data",    "sub": "Live flights, weather & prices"},
        {"icon": "🗺️", "bg": "#dcfce7", "title": "Interactive Maps",  "sub": "Explore destinations visually"},
        {"icon": "🏨", "bg": "#ede9fe", "title": "Best Hotels",        "sub": "Curated hotels & attractions"},
        {"icon": "🔒", "bg": "#fef3c7", "title": "Secure & Reliable", "sub": "Trusted APIs & live data"},
    ]
    items_html = ""
    for f in features:
        items_html += f"""
        <div style="display:flex;align-items:flex-start;gap:1rem;">
            <div style="width:44px;height:44px;background:{f['bg']};border-radius:12px;
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.2rem;flex-shrink:0;">{f['icon']}</div>
            <div>
                <div style="font-weight:600;font-size:0.9rem;color:{t['text']};
                            margin-bottom:0.2rem;">{f['title']}</div>
                <div style="font-size:0.78rem;color:{t['text_muted']};line-height:1.4;">
                    {f['sub']}</div>
            </div>
        </div>"""

    components.html(f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <div style="background:{t['card_bg']};border-top:1px solid {t['card_border']};
                padding:2rem;font-family:'Inter',sans-serif;">
        <div style="max-width:1100px;margin:0 auto;
                    display:grid;grid-template-columns:repeat(4,1fr);gap:1.5rem;">
            {items_html}
        </div>
    </div>
    """, height=120)


def generate_booking_links(origin, destination, depart_date, return_date=None, adults=1, children=0):
    depart_str = depart_date.strftime('%Y-%m-%d')
    if return_date:
        rs     = return_date.strftime('%Y-%m-%d')
        kayak  = f"https://www.kayak.com/flights/{origin}-{destination}/{depart_str}/{rs}?adults={adults}"
        gf     = f"https://www.google.com/travel/flights?hl=en#flt={origin}.{destination}.{depart_str}*{destination}.{origin}.{rs}"
    else:
        kayak  = f"https://www.kayak.com/flights/{origin}-{destination}/{depart_str}?adults={adults}"
        gf     = f"https://www.google.com/travel/flights?hl=en#flt={origin}.{destination}.{depart_str}"
    stay_end = return_date.strftime('%Y-%m-%d') if return_date else (depart_date + timedelta(days=7)).strftime('%Y-%m-%d')
    return {
        'kayak':          kayak,
        'google_flights': gf,
        'booking':  f"https://www.booking.com/searchresults.html?ss={quote(destination)}&checkin={depart_str}&checkout={stay_end}&group_adults={adults}",
        'hotels':   f"https://www.hotels.com/search.do?destination={quote(destination)}&checkIn={depart_str}&checkOut={stay_end}&adults={adults}",
    }


def render_form():
    t = get_theme_vars()
    components.html(f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <div style="background:{t['form_section_bg']};padding:3rem 2rem 1rem;font-family:'Inter',sans-serif;">
        <div style="background:white;border-radius:24px;padding:2rem 2.5rem;
                    max-width:1100px;margin:0 auto;
                    box-shadow:0 8px 32px rgba(0,0,0,0.08);border:1px solid #e2e8f0;">
            <div style="display:flex;align-items:center;gap:1rem;">
                <div style="width:48px;height:48px;
                            background:linear-gradient(135deg,#6366f1,#0ea5e9);
                            border-radius:12px;display:flex;align-items:center;
                            justify-content:center;font-size:1.4rem;">✈️</div>
                <div>
                    <div style="font-weight:700;font-size:1.2rem;color:#1e293b;">
                        Plan Your Perfect Trip</div>
                    <div style="font-size:0.9rem;color:#64748b;">
                        Tell us your preferences and let AI create your dream itinerary</div>
                </div>
            </div>
        </div>
    </div>
    """, height=160)

    # Centred form using padding columns
    _, mid, _ = st.columns([1, 10, 1])
    with mid:
        st.markdown("### ✈️ Travel Details")
        c1, c2, c3, c4 = st.columns([1, 2, 2, 2])
        with c1:
            trip_type = st.selectbox("Trip Type", ["✈️ One Way", "🔄 Round Trip"])
        with c2:
            origin = st.text_input("From", placeholder="e.g. Chennai (MAA)")
        with c3:
            destination = st.text_input("To", placeholder="e.g. Bangalore (BLR)")
        with c4:
            today = date.today()
            if "Round Trip" in trip_type:
                depart_date = st.date_input("Departure", value=today + timedelta(days=7))
                return_date = st.date_input("Return",    value=today + timedelta(days=14))
            else:
                depart_date = st.date_input("Departure Date", value=today + timedelta(days=7))
                return_date = None

        st.markdown("---")

        c5, c6, c7 = st.columns([1, 1, 2])
        with c5:
            adults   = st.number_input("Adults",   min_value=1, max_value=10, value=1)
            children = st.number_input("Children", min_value=0, max_value=10, value=0)
        with c6:
            hotel_class = st.selectbox("Hotel Preference",
                                       ["Any ⭐", "3⭐ Standard", "4⭐ Superior", "5⭐ Luxury"])
        with c7:
            notes = st.text_area("Special Requests", height=80,
                                 placeholder="Window seats, meals, transfers...")

        search = st.button("✨ Generate My Perfect Itinerary", use_container_width=True)

    links        = generate_booking_links(origin, destination, depart_date, return_date, adults, children)
    hotel_stars  = hotel_class.split("⭐")[0].strip()
    return_str   = f" returning {return_date}" if return_date else " one way"
    hotel_str    = f"{hotel_stars}⭐ " if hotel_stars and hotel_stars != "Any" else ""
    children_str = f" and {children} children" if children > 0 else ""
    query = (
        f"Create a detailed travel plan: Flights from {origin} to {destination} "
        f"departing {depart_date}{return_str} for {adults} adults{children_str}. "
        f"Recommend {hotel_str}hotels in {destination}. "
        f"Include weather forecast, top attractions and daily itinerary. "
        f"Special requests: {notes or 'None'}"
    )
    return query, search, destination, origin, links


@st.cache_data
def get_places_to_visit(destination: str):
    try:
        from serpapi import GoogleSearch
        search = GoogleSearch({
            "api_key": os.environ.get("SERPAPI_API_KEY"),
            "engine": "google",
            "q": f"top tourist attractions {destination}",
            "num": 8
        })
        results = search.get_dict()
        places  = []
        for place in results.get("local_results", [])[:6]:
            places.append({
                "name":        place.get("title", ""),
                "rating":      place.get("rating", 4.5),
                "reviews":     place.get("reviews", 0),
                "type":        place.get("type", "Landmark"),
                "description": place.get("description", f"A must-visit in {destination}"),
                "address":     place.get("address", ""),
                "google_link": f"https://www.google.com/maps/search/?api=1&query={quote(place.get('title',''))}+{quote(destination)}"
            })
        return places[:6] if places else _fallback_places(destination)
    except Exception:
        return _fallback_places(destination)


def _fallback_places(destination: str):
    d = destination
    return [
        {"name": f"{d} Historic Center",  "rating": 4.7, "reviews": 3500, "type": "Heritage",
         "description": "Centuries-old architecture and hidden gems.", "address": "Old Town",
         "google_link": f"https://www.google.com/maps/search/?api=1&query={quote(d)}+historic+center"},
        {"name": f"{d} Waterfront",       "rating": 4.6, "reviews": 2800, "type": "Scenic",
         "description": "Stunning views and waterfront dining.", "address": "Waterfront",
         "google_link": f"https://www.google.com/maps/search/?api=1&query={quote(d)}+waterfront"},
        {"name": f"{d} Central Market",   "rating": 4.5, "reviews": 4200, "type": "Food & Culture",
         "description": "Authentic local food and crafts.", "address": "Market Square",
         "google_link": f"https://www.google.com/maps/search/?api=1&query={quote(d)}+market"},
        {"name": f"{d} Art Museum",       "rating": 4.8, "reviews": 5100, "type": "Cultural",
         "description": "World-class art collection.", "address": "Museum District",
         "google_link": f"https://www.google.com/maps/search/?api=1&query={quote(d)}+museum"},
        {"name": f"{d} Botanical Garden", "rating": 4.4, "reviews": 1900, "type": "Nature",
         "description": "Beautiful gardens and plant collections.", "address": "Garden Quarter",
         "google_link": f"https://www.google.com/maps/search/?api=1&query={quote(d)}+garden"},
        {"name": f"{d} Cathedral",        "rating": 4.9, "reviews": 6200, "type": "Architecture",
         "description": "Breathtaking historic architecture.", "address": "Cathedral Square",
         "google_link": f"https://www.google.com/maps/search/?api=1&query={quote(d)}+cathedral"},
    ]


def render_booking_links(links, origin, destination):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="result-card">
            <div class="card-header">✈️ Book Your Flights</div>
            <a href="{links['kayak']}"          target="_blank" class="btn-link">🛫 Search on Kayak</a>
            <a href="{links['google_flights']}" target="_blank" class="btn-link btn-secondary">📱 Google Flights</a>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="result-card">
            <div class="card-header">🏨 Book Hotels in {destination}</div>
            <a href="{links['booking']}" target="_blank" class="btn-link">🏠 Booking.com</a>
            <a href="{links['hotels']}"  target="_blank" class="btn-link btn-secondary">⭐ Hotels.com</a>
        </div>""", unsafe_allow_html=True)


def render_places(destination, places):
    if not places:
        return
    bad = ["<", ">", "THE 15 BEST", "25 Unique", "BEST Things", "Amazing Places",
           "List of tourist", "Top Activities", "div class", "place-desc"]
    clean = [p for p in places if not any(k in p.get("name", "") for k in bad)]
    if not clean:
        clean = _fallback_places(destination)

    st.markdown(f"""
    <div class="result-card">
        <div class="card-header">📍 Top Places to Visit in {destination}</div>
    </div>""", unsafe_allow_html=True)

    cols = st.columns(2)
    for i, place in enumerate(clean[:6]):
        rating  = place.get("rating", 4.5)
        reviews = place.get("reviews", 0)
        stars   = "⭐" * int(float(rating))
        with cols[i % 2]:
            st.markdown(f"""
            <div style="background:#f8faff;border:1.5px solid #e2e8f0;border-radius:14px;
                        padding:1.2rem;margin-bottom:1rem;">
                <div style="font-weight:700;color:#1e293b;font-size:1rem;margin-bottom:0.3rem;">
                    📍 {place.get('name','')}</div>
                <div style="color:#f59e0b;font-size:0.85rem;margin-bottom:0.4rem;">
                    {stars} {rating} · {reviews:,} reviews</div>
                <div style="color:#6366f1;font-size:0.75rem;font-weight:600;margin-bottom:0.5rem;">
                    {place.get('type','')}
                    {' · ' + place['address'] if place.get('address') else ''}</div>
                <div style="color:#64748b;font-size:0.85rem;line-height:1.6;">
                    {place.get('description','')}</div>
                <a href="{place.get('google_link','#')}" target="_blank"
                   style="display:inline-block;margin-top:0.8rem;
                          background:linear-gradient(135deg,#6366f1,#0ea5e9);
                          color:white;padding:0.45rem 1rem;border-radius:8px;
                          font-size:0.78rem;font-weight:600;text-decoration:none;">
                    🗺️ View on Maps →</a>
            </div>""", unsafe_allow_html=True)


def render_travel_plan(content):
    sections = re.split(r'\n(?=✈️|🏨|🌤️|🗺️|⭐|👉|Day \d)', content)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # ── FLIGHTS ──
        if section.startswith("✈️") and "Flight" in section:
            options = re.findall(r'Option\s*\d+[^O]*', section)
            if options:
                st.markdown('<div class="result-card"><div class="card-header">✈️ Flight Options</div></div>',
                            unsafe_allow_html=True)
                cols = st.columns(len(options))
                for i, opt in enumerate(options):
                    airline  = re.search(r'-\s*([^,]+),', opt)
                    times    = re.search(r'(\d+:\d+)\s*-\s*(\d+:\d+)', opt)
                    duration = re.search(r'(\d+h\s*\d*m?)', opt)
                    price    = re.search(r'₹[\d,]+', opt)
                    with cols[i]:
                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg,#f0f4ff,#e8f0ff);
                                    border:1.5px solid #c7d2fe;border-radius:16px;
                                    padding:1.4rem;text-align:center;margin-bottom:1rem;">
                            <div style="font-size:0.7rem;font-weight:700;color:#6366f1;
                                        letter-spacing:0.15em;text-transform:uppercase;
                                        margin-bottom:0.4rem;">Option {i+1}</div>
                            <div style="font-size:1.05rem;font-weight:700;color:#1e293b;
                                        margin-bottom:0.7rem;">
                                ✈️ {airline.group(1).strip() if airline else 'Airline'}</div>
                            <div style="font-size:1.2rem;font-weight:800;color:#1e293b;
                                        margin-bottom:0.2rem;">
                                {times.group(1) if times else ''} → {times.group(2) if times else ''}</div>
                            <div style="font-size:0.78rem;color:#64748b;margin-bottom:0.8rem;">
                                ⏱ {duration.group(1) if duration else ''}</div>
                            <div style="background:linear-gradient(135deg,#6366f1,#0ea5e9);
                                        color:white;padding:0.45rem 1rem;border-radius:10px;
                                        font-weight:700;font-size:1rem;">
                                {price.group(0) if price else ''}</div>
                        </div>""", unsafe_allow_html=True)

        # ── HOTELS ──
        elif section.startswith("🏨"):
            options = re.findall(r'Option\s*\d+[^O]*', section)
            if options:
                st.markdown('<div class="result-card"><div class="card-header">🏨 Hotel Options</div></div>',
                            unsafe_allow_html=True)
                cols = st.columns(len(options))
                for i, opt in enumerate(options):
                    name     = re.search(r'Option\s*\d+:\s*([^-\n]+)', opt)
                    amenity  = re.search(r'-\s*([^,\n]+),', opt)
                    location = re.search(r'located in ([^,\n]+)', opt)
                    price    = re.search(r'₹[\d,]+', opt)
                    with cols[i]:
                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);
                                    border:1.5px solid #86efac;border-radius:16px;
                                    padding:1.4rem;text-align:center;margin-bottom:1rem;">
                            <div style="font-size:0.7rem;font-weight:700;color:#16a34a;
                                        letter-spacing:0.15em;text-transform:uppercase;
                                        margin-bottom:0.4rem;">Option {i+1}</div>
                            <div style="font-size:1rem;font-weight:700;color:#1e293b;
                                        margin-bottom:0.5rem;">
                                🏨 {name.group(1).strip() if name else f'Hotel {i+1}'}</div>
                            <div style="font-size:0.8rem;color:#64748b;margin-bottom:0.2rem;">
                                ✨ {amenity.group(1).strip() if amenity else ''}</div>
                            <div style="font-size:0.75rem;color:#64748b;margin-bottom:0.8rem;">
                                📍 {location.group(1).strip() if location else ''}</div>
                            <div style="background:linear-gradient(135deg,#10b981,#34d399);
                                        color:white;padding:0.45rem 1rem;border-radius:10px;
                                        font-weight:700;font-size:1rem;">
                                {price.group(0) if price else ''}/night</div>
                        </div>""", unsafe_allow_html=True)

        # ── WEATHER ──
        elif section.startswith("🌤️"):
            lines = [l.strip().lstrip("* ") for l in section.split("\n")
                     if l.strip() and "Weather Forecast" not in l]
            temp = desc = humid = wind = ""
            for line in lines:
                if "Temperature" in line: temp  = line.split(":")[-1].strip()
                if "Description" in line: desc  = line.split(":")[-1].strip()
                if "Humidity"    in line: humid = line.split(":")[-1].strip()
                if "Wind"        in line: wind  = line.split(":")[-1].strip()
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#fef9c3,#fef3c7);
                        border:1.5px solid #fcd34d;border-radius:20px;
                        padding:1.8rem;margin-bottom:1.5rem;
                        box-shadow:0 4px 16px rgba(0,0,0,0.06);">
                <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.2em;
                            text-transform:uppercase;color:#d97706;margin-bottom:1.2rem;
                            padding-bottom:1rem;border-bottom:1.5px solid #fcd34d;">
                    🌤️ Weather Forecast</div>
                <div style="display:flex;gap:1.5rem;flex-wrap:wrap;justify-content:space-around;">
                    <div style="text-align:center;">
                        <div style="font-size:2rem;">🌡️</div>
                        <div style="font-weight:700;font-size:1.2rem;color:#1e293b;">{temp}</div>
                        <div style="font-size:0.75rem;color:#64748b;">Temperature</div></div>
                    <div style="text-align:center;">
                        <div style="font-size:2rem;">⛅</div>
                        <div style="font-weight:700;font-size:1rem;color:#1e293b;">{desc}</div>
                        <div style="font-size:0.75rem;color:#64748b;">Condition</div></div>
                    <div style="text-align:center;">
                        <div style="font-size:2rem;">💧</div>
                        <div style="font-weight:700;font-size:1.2rem;color:#1e293b;">{humid}</div>
                        <div style="font-size:0.75rem;color:#64748b;">Humidity</div></div>
                    <div style="text-align:center;">
                        <div style="font-size:2rem;">💨</div>
                        <div style="font-weight:700;font-size:1.2rem;color:#1e293b;">{wind}</div>
                        <div style="font-size:0.75rem;color:#64748b;">Wind</div></div>
                </div>
            </div>""", unsafe_allow_html=True)

        # ── RECOMMENDATION ──
        elif section.startswith("⭐"):
            text = re.sub(r'^⭐[^\n]*\n?', '', section).strip()
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#6366f1,#0ea5e9);
                        border-radius:20px;padding:1.8rem;margin-bottom:1.5rem;
                        box-shadow:0 4px 16px rgba(99,102,241,0.3);">
                <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.2em;
                            text-transform:uppercase;color:rgba(255,255,255,0.8);
                            margin-bottom:1rem;">⭐ Our Recommendation</div>
                <div style="color:white;font-size:1rem;line-height:1.7;">{text}</div>
            </div>""", unsafe_allow_html=True)

        elif re.match(r'Day \d+', section):
            day_match = re.match(r'(Day \d+:[^\n]*)', section)
            day_title = day_match.group(1) if day_match else "Day"
            day_body = section[len(day_title):].strip()
            lines = [l.strip() for l in day_body.split("\n") if l.strip()]
            activities = []
            for l in lines:
                if l.startswith("*"):
                    activities.append(l.lstrip("* ").strip())
                else:
                    activities.append(l)  # ← accept normal text too
            acts_html = "".join([
                f'<div style="padding:0.5rem 0;border-bottom:1px solid #f1f5f9;'
                f'color:#475569;font-size:0.9rem;">• {a}</div>'
                for a in activities
                ])
            st.markdown(f"""
            <div style="background:white;border:1.5px solid #e2e8f0;border-radius:16px;
                         padding:1.2rem 1.5rem;margin-bottom:1rem;
                        box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                    <div style="font-weight:700;color:#6366f1;font-size:0.95rem;
                         margin-bottom:0.8rem;">📅 {day_title}</div>
                 {acts_html}
             </div>""", unsafe_allow_html=True)

        
        # ── NEXT STEPS ──
        elif section.startswith("👉"):
            steps = [l.strip() for l in section.split("\n") if re.match(r'\d+\.', l.strip())]
            steps_html = "".join([
                f'<div style="padding:0.6rem 0;border-bottom:1px solid #f1f5f9;'
                f'color:#475569;font-size:0.9rem;">{s}</div>'
                for s in steps
            ])
            st.markdown(f"""
            <div class="result-card">
                <div class="card-header">👉 Next Steps</div>
                {steps_html}
            </div>""", unsafe_allow_html=True)

        # ── MAP text — skip, rendered via components.html below ──
        elif section.startswith("🗺️"):
            pass


def render_results():
    if 'travel_result' not in st.session_state:
        return

    dest  = st.session_state.get('destination', '')
    orig  = st.session_state.get('origin', '')
    links = st.session_state.get('links', {})

    # Centred wrapper
    _, mid, _ = st.columns([1, 10, 1])
    with mid:
        if links:
            render_booking_links(links, orig, dest)

        st.markdown("""
        <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.2em;
                    text-transform:uppercase;color:#6366f1;margin:1.5rem 0 1rem;">
            ✦ Your AI Travel Plan
        </div>""", unsafe_allow_html=True)

        render_travel_plan(st.session_state.travel_result)

        if 'map_path' in st.session_state:
            st.markdown("""
            <div class="result-card">
                <div class="card-header">🗺️ Interactive Travel Map</div>
            </div>""", unsafe_allow_html=True)
            with open(st.session_state.map_path, "r", encoding="utf-8") as f:
                map_html = f.read()
            components.html(map_html, height=480)

        if 'places' in st.session_state and dest:
            render_places(dest, st.session_state.places)


def process_query(user_input, destination, origin, links):
    try:
        thread_id = str(uuid.uuid4())
        result    = st.session_state.agent.graph.invoke(
            {'messages': [HumanMessage(content=user_input)], 'tool_call_count': 0},
            config={'configurable': {'thread_id': thread_id}}
        )
        content = result['messages'][-1].content
        # Strip only div/span/a tags but keep text — avoids showing raw HTML
        content = re.sub(r'<(div|span|a|img)[^>]*>', '', content)
        content = re.sub(r'</(div|span|a|img)>', '', content)

        st.session_state.travel_result = content
        st.session_state.destination   = destination
        st.session_state.origin        = origin
        st.session_state.links         = links
        st.session_state.places        = get_places_to_visit(destination)

        map_path = os.path.join(tempfile.gettempdir(), "travel_map.html")
        if os.path.exists(map_path):
            st.session_state.map_path = map_path

    except Exception as e:
        st.error(f"Error: {str(e)}")


def main():
    initialize_agent()
    initialize_theme()
    render_css()
    render_navbar()
    render_hero()
    render_trip_cards()

    query, search, destination, origin, links = render_form()
    render_features()

    if search:
        if origin.strip() and destination.strip():
            with st.spinner("✦ Crafting your perfect itinerary..."):
                process_query(query, destination, origin, links)
            st.success("✦ Your personalised travel plan is ready! Scroll down to explore.")
        else:
            st.warning("⚠️ Please enter both origin and destination.")

    render_results()


if __name__ == '__main__':
    main()
