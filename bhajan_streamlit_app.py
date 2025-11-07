import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Import data loader
from data_loader import load_bhajan_data_from_excel

# Page configuration
st.set_page_config(
    page_title="🕉️ Bhajan Search",
    page_icon="🕉️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* Main container styling */
    .main {
        padding: 1rem;
        font-family: 'Poppins', sans-serif;
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Header styling */
    .header {
        background: linear-gradient(135deg, #ea580c 0%, #fb923c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(234, 88, 12, 0.3);
    }
    
    .header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
    }
    
    .header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
    }
    
    /* Bhajan item styling */
    .bhajan-item {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.2s ease;
    }
    
    .bhajan-item:hover {
        background: #fff7ed;
        border-color: #ea580c;
    }
    
    .bhajan-title {
        color: #1f2937;
        font-weight: 600;
        margin-bottom: 0.3rem;
        font-size: 1.1rem;
    }
    
    .bhajan-author {
        color: #6b7280;
        font-size: 0.9rem;
    }
    
    /* Verse styling */
    .verse-container {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .verse-original {
        font-family: 'Times New Roman', serif;
        line-height: 1.4;
        font-size: 1.1rem;
        color: #1f2937;
        white-space: pre-line;
    }
    
    .verse-english {
        line-height: 1.5;
        font-size: 1rem;
        color: #1f2937;
        white-space: pre-line;
    }
    
    /* Menu styling */
    .menu-section {
        margin: 1.5rem 0;
    }
    
    .category-section {
        background: #f8fafc;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        background: white;
        color: #374151;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #fff7ed;
        border-color: #ea580c;
        color: #ea580c;
    }
    
    /* Stats container */
    .stats-container {
        background: #f8fafc;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
        
        .header h1 {
            font-size: 1.5rem;
        }
        
        .verse-container {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'selected_bhajan' not in st.session_state:
    st.session_state.selected_bhajan = None
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None
if 'selected_author' not in st.session_state:
    st.session_state.selected_author = None
if 'show_english' not in st.session_state:
    st.session_state.show_english = False

def go_home():
    st.session_state.page = 'home'
    st.session_state.selected_bhajan = None
    st.session_state.selected_category = None
    st.session_state.selected_author = None
    st.session_state.show_english = False

def show_titles():
    st.session_state.page = 'titles'

def show_categories():
    st.session_state.page = 'categories'

def show_authors():
    st.session_state.page = 'authors'

def show_category_bhajans(category):
    st.session_state.page = 'category_bhajans'
    st.session_state.selected_category = category

def show_author_bhajans(author):
    st.session_state.page = 'author_bhajans'
    st.session_state.selected_author = author

def show_bhajan(bhajan):
    st.session_state.page = 'bhajan'
    st.session_state.selected_bhajan = bhajan

# Load bhajan data from fixed Excel file
@st.cache_data
def load_data():
    # Try to load from the fixed Excel file
    excel_file_path = "Bhajans.xlsx"
    if os.path.exists(excel_file_path):
        return load_bhajan_data_from_excel(excel_file_path)
    else:
        # If file doesn't exist, use default data
        return load_bhajan_data_from_excel()

# Header
st.markdown("""
<div class="header">
    <h1>🕉️ Bhajan Search</h1>
    <p>Discover and explore sacred bhajans</p>
</div>
""", unsafe_allow_html=True)

# Load data
bhajan_data = load_data()

# Safety check - ensure bhajan_data is not empty and has valid data
if not bhajan_data:
    st.error("⚠️ No bhajan data found! Please check your Excel file format.")
    st.stop()

# Get unique categories and authors with safety checks
try:
    categories = sorted(list(set(bhajan['category'] for bhajan in bhajan_data if bhajan.get('category'))))
    authors = sorted(list(set(bhajan['author'] for bhajan in bhajan_data if bhajan.get('author'))))
    sorted_titles = sorted(bhajan_data, key=lambda x: x['title'])
except Exception as e:
    st.error(f"⚠️ Error processing bhajan data: {e}")
    st.error("Please check that your Excel file has the correct format with columns: Category, Bhajan_Title, Author, Verse_Number, Original, English")
    st.stop()

# Navigation
if st.session_state.page != 'home':
    if st.button("🏠 Back to Home", key="home_btn", help="Return to main menu"):
        go_home()
        st.rerun()

# Page content
if st.session_state.page == 'home':
    # Home page
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📚\nBy Title: A-Z", key="titles_btn", help="Browse all bhajans alphabetically", use_container_width=True):
            show_titles()
            st.rerun()
    
    with col2:
        if st.button("📁\nBy Category", key="categories_btn", help="Explore by devotional themes", use_container_width=True):
            show_categories()
            st.rerun()
    
    with col3:
        if st.button("👤\nBy Author", key="authors_btn", help="Find bhajans by their composers", use_container_width=True):
            show_authors()
            st.rerun()
    
    # Show stats
    st.markdown("---")
    st.markdown("""
    <div class="stats-container">
        <h4 style="text-align: center; margin: 0 0 1rem 0; color: #374151;">📊 Collection Statistics</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Bhajans", len(bhajan_data))
    with col2:
        st.metric("Categories", len(categories))
    with col3:
        st.metric("Authors", len(authors))

elif st.session_state.page == 'titles':
    # All titles page
    st.markdown("## 📚 All Bhajans (A-Z)")
    
    for bhajan in sorted_titles:
        # Create clickable title only - no boxes, no author links
        title_clicked = st.button(bhajan['title'], key=f"title_{bhajan['title']}", use_container_width=True)
        if title_clicked:
            show_bhajan(bhajan)
            st.rerun()

elif st.session_state.page == 'categories':
    # Categories page
    st.markdown("## 📁 Categories")
    
    for category in categories:
        count = len([b for b in bhajan_data if b['category'] == category])
        # Create clickable category
        category_clicked = st.button(f"{category} ({count} bhajan{'s' if count != 1 else ''})", 
                                   key=f"cat_{category}", 
                                   use_container_width=True)
        if category_clicked:
            show_category_bhajans(category)
            st.rerun()

elif st.session_state.page == 'authors':
    # Authors page
    st.markdown("## 👤 Authors")
    
    for author in authors:
        count = len([b for b in bhajan_data if b['author'] == author])
        # Create clickable author
        author_clicked = st.button(f"{author} ({count} bhajan{'s' if count != 1 else ''})", 
                                 key=f"auth_{author}", 
                                 use_container_width=True)
        if author_clicked:
            show_author_bhajans(author)
            st.rerun()

elif st.session_state.page == 'category_bhajans':
    # Category bhajans page
    if st.button("← Back to Categories", key="back_to_cats"):
        show_categories()
        st.rerun()
    
    st.markdown(f"## 📁 {st.session_state.selected_category}")
    
    category_bhajans = [b for b in bhajan_data if b['category'] == st.session_state.selected_category]
    category_bhajans.sort(key=lambda x: x['title'])
    
    for bhajan in category_bhajans:
        # Create clickable title
        title_clicked = st.button(bhajan['title'], key=f"cat_title_{bhajan['title']}", use_container_width=True)
        if title_clicked:
            show_bhajan(bhajan)
            st.rerun()
        
        # Create clickable author link
        author_clicked = st.button(f"👤 {bhajan['author']}", key=f"cat_author_{bhajan['title']}", use_container_width=True, type="secondary")
        if author_clicked:
            show_author_bhajans(bhajan['author'])
            st.rerun()
        
        st.markdown("---")

elif st.session_state.page == 'author_bhajans':
    # Author bhajans page
    if st.button("← Back to Authors", key="back_to_auths"):
        show_authors()
        st.rerun()
    
    st.markdown(f"## 👤 {st.session_state.selected_author}")
    
    author_bhajans = [b for b in bhajan_data if b['author'] == st.session_state.selected_author]
    author_bhajans.sort(key=lambda x: x['title'])
    
    for bhajan in author_bhajans:
        # Create clickable title
        title_clicked = st.button(bhajan['title'], key=f"auth_title_{bhajan['title']}", use_container_width=True)
        if title_clicked:
            show_bhajan(bhajan)
            st.rerun()
        
        # Add spacing between bhajans (like in other pages)
        st.markdown("")

elif st.session_state.page == 'bhajan':
    # Bhajan display page
    bhajan = st.session_state.selected_bhajan
    
    if bhajan:
        # Title and author
        st.markdown(f"# {bhajan['title']}")
        st.markdown(f"**{bhajan['author']}**")
        st.markdown(f"*Category: {bhajan['category']}*")
        st.markdown("---")
        
        # Language toggle
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📜 Original", 
                        key="original_btn",
                        help="Show original text",
                        type="primary" if not st.session_state.show_english else "secondary",
                        use_container_width=True):
                st.session_state.show_english = False
                st.rerun()
        
        with col2:
            if st.button("🇬🇧 English", 
                        key="english_btn",
                        help="Show English translation",
                        type="primary" if st.session_state.show_english else "secondary",
                        use_container_width=True):
                st.session_state.show_english = True
                st.rerun()
        
        st.markdown("---")
        
        # Display verses
        for i, verse in enumerate(bhajan['verses']):
            text_class = "verse-english" if st.session_state.show_english else "verse-original"
            text_content = verse['english'] if st.session_state.show_english else verse['original']
            
            st.markdown(f"""
            <div class="verse-container">
                <div class="{text_class}">{text_content}</div>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 0.9rem; padding: 1rem;">
    🕉️ Bhajan Search App • Made with ❤️ for devotional service
</div>
""", unsafe_allow_html=True)
