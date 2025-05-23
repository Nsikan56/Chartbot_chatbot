import streamlit as st
import os
import warnings

# Compatibility setup
try:
    from fix_torch_streamlit import fix_torch_classes, suppress_warnings
    fix_torch_classes()
    suppress_warnings()
except ImportError:
    warnings.filterwarnings('ignore')

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Page config
st.set_page_config(
    page_title="ChartBot 🎶", 
    page_icon="🎧",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Session state initialization
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Import chatbot logic
try:
    from chatbot_logic import respond_to_query
    from data_utils import get_dataset_stats
except ImportError as e:
    st.error(f"❌ Error importing chatbot logic: {e}")
    st.stop()

# Styling
st.markdown("""
<style>
    /* Make header transparent instead of hiding */
    header[data-testid="stHeader"] {
        background: transparent !important;
        backdrop-filter: none !important;
    }
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
        font-weight: bold;
    }

    .instructions {
        text-align: center;
        font-size: 17px;
        margin-bottom: 2rem;
        padding: 2rem 1.5rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 16px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .instructions:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }

    .instructions h3 {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 1.2rem;
    }

    .instructions h3 .emoji {
        display: inline-block;
        transition: transform 0.3s ease-in-out;
    }

    .instructions:hover h3 .emoji {
        animation: pop 0.6s infinite alternate;
    }

    @keyframes pop {
        from { transform: scale(1) rotate(-5deg); }
        to { transform: scale(1.15) rotate(5deg); }
    }

    .stats-container {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 2rem 0;
        flex-wrap: wrap;
    }

    .stat-box {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        min-width: 120px;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .stat-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4);
    }

    .stat-number {
        font-size: 1.5rem;
        font-weight: bold;
        display: block;
        margin-bottom: 0.5rem;
    }

    .stat-label {
        font-size: 0.85rem;
        opacity: 0.9;
    }

     /* Suggestions box */
    .suggestions {
        margin-top: 1.5rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .suggestions:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .suggestions h4 {
        color: white;
        margin-top: 0;
        margin-bottom: 1rem;
    }
    
    .suggestions ul {
        margin-bottom: 0;
    }
    
    .suggestions li {
        margin-bottom: 0.5rem;
    }
    
    .suggestions strong {
        color: #fff;
    }
    
    .suggestions em {
        color: #f0f0f0;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;
        color: white !important;
        font-weight: 600;
        border: none;
        border-radius: 999px;
        padding: 0.6rem 1.2rem;
        margin: 0.3rem 0;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 20px rgba(76, 175, 80, 0.4);
    }

    /* Make dataset info text darker */
    .stAlert > div {
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }

    /* Make text input label clearer */
    .stTextInput > label {
        color: #1a1a1a !important;
        font-weight: 600 !important;
        font-size: 16px !important;
    }

    /* Style success/output boxes with darker text */
    .stSuccess > div {
        color: #0d4f3c !important;
        font-weight: 500 !important;
        font-size: 15px !important;
    }

    /* Style chat history expander */
    .streamlit-expanderHeader {
        background: #f8f9fa !important;
        color: #1a1a1a !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: 1px solid #dee2e6 !important;
    }

    /* Chat history content styling */
    .streamlit-expanderContent {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%) !important;
        border-radius: 0 0 12px 12px !important;
        padding: 1rem !important;
        color: #155724 !important;
    }

    /* Chat history text styling */
    .streamlit-expanderContent p, 
    .streamlit-expanderContent div {
        color: #155724 !important;
        font-weight: 600 !important;
    }

    /* Make chat history text even darker */
    .streamlit-expanderContent strong {
        color: #0a3d1a !important;
        font-weight: 700 !important;
    }

    /* Clear chat history button - make it white */
    div.stButton > button[kind="primary"],
    div.stButton > button:contains("Clear Chat History") {
        background: white !important;
        color: #1a1a1a !important;
        border: 2px solid #f093fb !important;
        font-weight: 600 !important;
    }

    div.stButton > button[kind="primary"]:hover,
    div.stButton > button:contains("Clear Chat History"):hover {
        background: #f093fb !important;
        color: white !important;
        transform: translateY(-2px);
    }

    .footer {
        text-align: center;
        color: #666;
        font-size: 14px;
        margin-top: 2rem;
        padding: 1rem;
        border-top: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>🎶 ChartBot – Billboard Music Trends Chatbot</h1>", unsafe_allow_html=True)

# Instruction block
st.markdown("""
<div class='instructions'>
    <h3><span class="emoji">🎯</span> Ask me about the Billboard Hot 100 charts!</h3>
</div>
""", unsafe_allow_html=True)

# Example input buttons (green style)
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Top 10 songs of 2020"):
        st.session_state.user_input = "Top 10 songs of 2020"
with col2:
    if st.button("Best songs from the 90s"):
        st.session_state.user_input = "Best songs from the 90s"
with col3:
    if st.button("Shape of You duration"):
        st.session_state.user_input = "How long did Shape of You stay on the chart?"

# Dataset info
st.info("📌 **Dataset:** Billboard Hot 100 data from 1958 to 2021 (63+ years of music history!)")

# Dataset stats
try:
    stats = get_dataset_stats()
    st.markdown("""
    <div class='stats-container'>
        <div class='stat-box'>
            <span class='stat-number'>{:,}</span>
            <span class='stat-label'>Total Records</span>
        </div>
        <div class='stat-box'>
            <span class='stat-number'>{:,}</span>
            <span class='stat-label'>Unique Songs</span>
        </div>
        <div class='stat-box'>
            <span class='stat-number'>{:,}</span>
            <span class='stat-label'>Artists</span>
        </div>
        <div class='stat-box'>
            <span class='stat-number'>{}</span>
            <span class='stat-label'>Years</span>
        </div>
    </div>
    """.format(
        stats.get('total_records', 0),
        stats.get('unique_songs', 0),
        stats.get('unique_artists', 0),
        stats.get('total_years', 0)
    ), unsafe_allow_html=True)
except Exception as e:
    st.warning(f"⚠️ Could not load dataset statistics: {e}")

# Chat input
query = st.text_input("💬 Ask ChartBot something:", key="user_input")

# Generate response
if query and query.strip():
    with st.spinner("🔍 Analyzing the charts..."):
        try:
            response = respond_to_query(query.strip())
            st.session_state.chat_history.append({
                'query': query,
                'response': response
            })
            st.success(response)
        except Exception as e:
            st.error(f"⚠️ Something went wrong: {str(e)}")

# Chat history
if st.session_state.chat_history:
    with st.expander("💬 Chat History", expanded=False):
        for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):
            st.write(f"**Q{len(st.session_state.chat_history)-i}:** {chat['query']}")
            st.write(f"**A:** {chat['response']}")
            st.write("---")

# Clear history button
if st.session_state.chat_history:
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# Follow-up suggestions
st.markdown("""
<div class='suggestions'>
    <h4>💡 Try asking about:</h4>
    <ul style='list-style-type: none; padding-left: 0;'>
        <li>🎵 <strong>Top songs:</strong> <em>"Top 10 songs of 1985"</em> or <em>"Best 5 hits from 2010"</em></li>
        <li>⏱ <strong>Song duration:</strong> <em>"How long was Blinding Lights on the chart?"</em></li>
        <li>🎯 <strong>Different eras:</strong> <em>"Top songs from the 80s"</em> or <em>"Best of 2000s"</em></li>
        <li>🏆 <strong>Peak performance:</strong> Try any year from 1958-2021!</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div class='footer'>
    Built with ❤️ using Streamlit & FLAN-T5 | Data: Billboard Hot 100
</div>
""", unsafe_allow_html=True)