# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import re
import unicodedata
import os
from rapidfuzz import fuzz
from difflib import SequenceMatcher

st.set_page_config(page_title="Gauḍīya Vaiṣṇava Verse Finder", layout="wide")

# === Ceļš uz datubāzi (Excel blakus app.py) ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_FILE = os.path.join(SCRIPT_DIR, "250928Versebase_app.xlsx")

# === CSS - Rītausmas Gaisma palete ===
st.markdown("""
<style>
/* Rītausmas Gaisma krāsu palete */
:root {
  --bg-morning: #F8F8FA;
  --text-indigo: #282B4F;
  --text-soft: #4a4e73;
  --accent-violet: #A075A4;
  --accent-coral: #E58B8B;
  --accent-light-violet: #c9b3cb;
  --accent-light-coral: #f5c4c4;
  --border-subtle: #e8e8f0;
  --white: #ffffff;
}

/* Fons */
.main { background-color: var(--bg-morning); }
.block-container { 
  padding-top: 1rem; 
  background-color: var(--bg-morning);
}

/* Pamatteksts */
p { 
  margin: 0; 
  line-height: 1.4; 
  color: var(--text-indigo);
}

/* Galvenais virsraksts */
h1 {
  color: var(--text-indigo) !important;
  letter-spacing: -0.02em;
  font-weight: 700 !important;
}

/* Sources virsraksts + (N verses) */
.sv-title { 
  font-size: 2rem; 
  font-weight: 700; 
  margin: 0.5rem 0 0.75rem 0;
  color: var(--text-indigo);
  letter-spacing: -0.02em;
}
.sv-title .verses { 
  font-size: 50%; 
  font-weight: 500;
  color: var(--text-soft);
}

/* Avotu saraksts kartīte */
.sources-grid {
  display: grid;
  grid-template-columns: 1fr 12px 1fr;
  column-gap: 8px;
  align-items: start;
  background-color: var(--white);
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(40, 43, 79, 0.08);
  border: 1px solid var(--border-subtle);
}
.sources-grid .gap { width: 12px; }
.source-item { 
  margin-bottom: 0.4rem; 
  font-size: 0.95rem;
  color: var(--text-soft);
  line-height: 1.5;
}

/* ATSTARPES KONTROLE */
:root{
  --verse-line-gap: 0.2rem;
  --verse-block-gap: 0.7rem;
}

/* Panta rindas */
.verse-line { 
  margin: 0 0 var(--verse-line-gap) 0; 
  line-height: 1.5;
  color: var(--text-indigo);
  font-size: 1.05rem;
}
.verse-gap { height: var(--verse-block-gap); }

/* Highlight meklējamam fragmentam - koraļļu roze */
.highlight { 
  color: var(--accent-coral); 
  font-weight: 600;
  background-color: var(--accent-light-coral);
  padding: 0 3px;
  border-radius: 3px;
}

/* Procentu rādītājs - violets akcents */
.result-score {
  color: var(--accent-violet) !important;
  font-weight: 700 !important;
  font-size: 1.15rem !important;
}

/* Translation virsraksts */
.translation-header { 
  font-weight: 700; 
  margin-bottom: 0.5rem;
  color: var(--accent-violet);
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.translation-text { 
  line-height: 1.6; 
  color: var(--text-soft);
  font-size: 0.95rem;
  font-style: italic;
}

/* Rezultātu header */
.results-header {
  background: linear-gradient(135deg, var(--accent-violet), var(--accent-coral));
  color: white !important;
  padding: 0.85rem 1.25rem;
  border-radius: 12px;
  font-weight: 600;
  margin: 1rem 0;
  box-shadow: 0 4px 12px rgba(160, 117, 164, 0.25);
}

/* Avotu informācija */
.source-info {
  color: var(--text-soft);
  font-size: 0.9rem;
  line-height: 1.6;
}

/* Strong/Bold elementi */
strong, b {
  color: var(--text-indigo);
  font-weight: 600;
}

/* Italic elementi */
em {
  color: var(--text-soft);
}

/* Horizontal rule */
hr {
  border-color: var(--border-subtle) !important;
  margin: 1.5rem 0 !important;
  opacity: 0.6;
}

/* Streamlit button - violets ar gradient */
.stButton button {
  background: linear-gradient(135deg, var(--accent-violet), var(--accent-coral)) !important;
  color: white !important;
  border: none !important;
  font-weight: 600 !important;
  letter-spacing: 0.025em !important;
  padding: 0.6rem 1.5rem !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 4px 12px rgba(160, 117, 164, 0.3) !important;
}

.stButton button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(160, 117, 164, 0.4) !important;
}

/* Textarea styling */
.stTextArea textarea {
  border-color: var(--border-subtle) !important;
  border-radius: 12px !important;
  font-size: 0.95rem !important;
  background-color: var(--white) !important;
  color: var(--text-indigo) !important;
  border-width: 2px !important;
}

.stTextArea textarea:focus {
  border-color: var(--accent-violet) !important;
  box-shadow: 0 0 0 3px rgba(160, 117, 164, 0.1) !important;
}

.stTextArea textarea::placeholder {
  color: var(--text-soft) !important;
  opacity: 0.6;
}

/* Sidebar styling */
.css-1d391kg, [data-testid="stSidebar"] {
  background-color: var(--white) !important;
}

/* Warning messages */
.stWarning {
  background-color: var(--accent-light-coral) !important;
  color: var(--text-indigo) !important;
  border-left: 4px solid var(--accent-coral) !important;
}
</style>
""", unsafe_allow_html=True)

# === Palīgfunkcijas ===
def normalize_text(text: str) -> str:
    """Normalizē tekstu meklēšanai - noņem visas atstarpes, diakritiku utt."""
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('-', '').replace(' ', '').replace('\n', '')
    text = re.sub(r'[^\w]', '', text)
    return text.lower().strip()

def normalize_for_sorting(text: str) -> str:
    """Normalizē tekstu alfabētiskai šķirošanai, noņemot diakritiskās zīmes"""
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower().strip()

def clean_verse_text(text: str) -> str:
    """Notīra Excel encoding artefaktus un citus nevēlamus simbolus"""
    if not text:
        return ""
    # Noņem Excel encoding simbolus
    text = text.replace('_x000D_', '').replace('_x000A_', '')
    # Noņem ciparus iekavās rindas beigās, piemēram (1), (2)
    text = re.sub(r'\s*\(\d+\)\s*$', '', text)
    return text.strip()

def find_fragment_position(search_text: str, verse_text: str) -> int:
    """Atrod, kurā pozīcijā normalizētajā tekstā ir fragments"""
    ns, nv = normalize_text(search_text), normalize_text(verse_text)
    if not ns or not nv:
        return 999999
    
    pos = nv.find(ns)
    if pos >= 0:
        return pos
    
    # Ja nav precīzas sakritības, mēģinām atrast ar fuzzy match
    best_pos = 999999
    best_score = 0
    window_size = len(ns)
    
    for i in range(len(nv) - window_size + 1):
        window = nv[i:i+window_size]
        score = fuzz.ratio(ns, window)
        if score > best_score:
            best_score = score
            best_pos = i
    
    return best_pos if best_score > 70 else 999999

def calculate_fragment_match(search_text: str, verse_text: str) -> tuple:
    """Izmanto RapidFuzz līdzības salīdzināšanai un atgriež arī pozīciju un prefix garumu"""
    ns, nv = normalize_text(search_text), normalize_text(verse_text)
    if not ns or not nv: 
        return 0.0, 999999, 0
    
    # Salīdzina pilnus tekstus
    score = fuzz.ratio(ns, nv) / 100.0
    
    # Ja meklētais teksts ir īsāks, pārbauda arī daļēju sakritību
    if len(ns) < len(nv):
        partial_score = fuzz.partial_ratio(ns, nv) / 100.0
        score = max(score, partial_score)
    
    # Atrod pozīciju
    position = find_fragment_position(search_text, verse_text)
    
    # Skaita secīgos sakritošos burtus no sākuma
    prefix_length = 0
    for i in range(min(len(ns), len(nv))):
        if ns[i] == nv[i]:
            prefix_length += 1
        else:
            break
    
    return score, position, prefix_length

def highlight_verse_lines(lines: list, search_text: str, full_verse: str) -> list:
    """Iekrāso tikai tos burtus kas sakriet meklētā fragmenta ietvaros"""
    if not lines or not search_text:
        return lines
    
    normalized_search = normalize_text(search_text)
    normalized_full = normalize_text(full_verse)
    
    if not normalized_search or not normalized_full:
        return lines
    
    # Atrod fragmenta sākuma pozīciju
    pos = normalized_full.find(normalized_search)
    
    if pos < 0:
        # Ja nav precīzas sakritības, meklē ar fuzzy match
        best_pos = -1
        best_score = 0
        window_size = len(normalized_search)
        
        for i in range(len(normalized_full) - window_size + 1):
            window = normalized_full[i:i+window_size]
            score = fuzz.ratio(normalized_search, window)
            if score > best_score:
                best_score = score
                best_pos = i
        
        if best_score < 60:
            return lines
        pos = best_pos
    
    # Ņem tikai fragmentu (ar nelielu rezervi)
    fragment_length = len(normalized_search)
    margin = int(fragment_length * 0.2)
    start_pos = max(0, pos - margin)
    end_pos = min(len(normalized_full), pos + fragment_length + margin)
    fragment = normalized_full[start_pos:end_pos]
    
    # Izmanto SequenceMatcher tikai šim fragmentam
    matcher = SequenceMatcher(None, normalized_search, fragment)
    matching_blocks = matcher.get_matching_blocks()
    
    # Pārveršas relatīvās pozīcijas fragmentā uz absolūtām pozīcijām
    matching_positions = set()
    for _, b_start, size in matching_blocks:
        for i in range(size):
            abs_pos = start_pos + b_start + i
            matching_positions.add(abs_pos)
    
    if not matching_positions:
        return lines
    
    # Izveido mapping: normalizētā pozīcija → (rindas_nr, simbola_pozīcija_rindā)
    norm_to_line_char = []
    
    for i, line in enumerate(lines):
        for char_pos, char in enumerate(line):
            normalized_char = normalize_text(char)
            if normalized_char:
                for _ in normalized_char:
                    norm_to_line_char.append((i, char_pos))
    
    # Noteikt, kuri oriģinālie simboli jāiekrāso
    chars_to_highlight = {}
    
    for norm_pos in matching_positions:
        if norm_pos < len(norm_to_line_char):
            line_idx, char_pos = norm_to_line_char[norm_pos]
            chars_to_highlight[(line_idx, char_pos)] = True
    
    # Iekrāso
    result_lines = []
    for line_idx, line in enumerate(lines):
        if not any((line_idx, pos) in chars_to_highlight for pos in range(len(line))):
            result_lines.append(line)
            continue
        
        highlighted = []
        i = 0
        while i < len(line):
            if (line_idx, i) in chars_to_highlight:
                start = i
                while i < len(line) and (line_idx, i) in chars_to_highlight:
                    i += 1
                highlighted.append(f'<span class="highlight">{line[start:i]}</span>')
            else:
                start = i
                while i < len(line) and (line_idx, i) not in chars_to_highlight:
                    i += 1
                highlighted.append(line[start:i])
        
        result_lines.append(''.join(highlighted))
    
    return result_lines

@st.cache_data
def load_database_from_file(file_path: str):
    """Ielādē datubāzi no Excel faila"""
    df = pd.read_excel(file_path, sheet_name=0)
    database = []
    for _, row in df.iterrows():
        if pd.notna(row.get('IAST Verse')) and str(row.get('IAST Verse')).strip():
            database.append({
                'iast_verse': clean_verse_text(str(row.get('IAST Verse', '')).strip()),
                'original_source': str(row.get('Original Source', '')).strip() if pd.notna(row.get('Original Source')) else '',
                'author': str(row.get('Author', '')).strip() if pd.notna(row.get('Author')) else '',
                'context': str(row.get('Context', '')).strip() if pd.notna(row.get('Context')) else '',
                'english_translation': str(row.get('Translation', '')).strip() if pd.notna(row.get('Translation')) else '',
                'cited_in': str(row.get('Cited In', '')).strip() if pd.notna(row.get('Cited In')) else ''
            })
    return database, len(database)

def search_verses(search_text: str, database, max_results=20, min_confidence=0.3):
    """Meklē pantus datubāzē"""
    results = []
    
    for verse_data in database:
        score, position, prefix_len = calculate_fragment_match(search_text, verse_data['iast_verse'])
        
        if score < min_confidence:
            continue
        
        results.append({
            'verse_data': verse_data, 
            'confidence': score, 
            'score_percent': score * 100,
            'position': position,
            'prefix_length': prefix_len
        })
    
    # Kārtojums: confidence → prefix_length → pozīcija
    results.sort(key=lambda x: (-x['confidence'], -x['prefix_length'], x['position']))
    return results[:max_results]

def clean_author(author: str) -> str:
    """Attīra autora vārdu no 'by' un nederīgām vērtībām"""
    if not author: 
        return ""
    author_str = str(author).strip()
    if author_str.lower() in ['nan', 'none', 'null', '']:
        return ""
    return re.sub(r'^\s*by\s+', '', author_str, flags=re.I).strip()

def format_source_and_author(source, author) -> str:
    """Formatē avota un autora informāciju"""
    a = clean_author(author)
    if source and a: return f"{source} (by {a})"
    if source: return source
    if a: return f"(by {a})"
    return "NOT AVAILABLE"

_by_regex = re.compile(r"\s+by\s+", re.IGNORECASE)
def render_cited_item(text: str) -> str:
    """Formatē citēto avotu ar HTML - treknrakstā līdz 'by' un līdz '_'"""
    if not text or str(text).strip().lower() in ['nan', 'none', 'null', '']:
        return ""
    parts = _by_regex.split(text, maxsplit=1)
    if len(parts) == 2:
        title, author = parts[0].strip(), parts[1].strip()
        # Pārbauda vai title satur apakšsvītru
        if '_' in title:
            # Sadala pie pirmās apakšsvītras
            underscore_parts = title.split('_', 1)
            bold_part = underscore_parts[0].strip()
            rest_part = underscore_parts[1].strip()
            return f"<em><strong>{bold_part}</strong>_{rest_part} by {author}</em>"
        else:
            return f"<em><strong>{title}</strong> by {author}</em>"
    else:
        # Ja nav 'by', pārbauda vai ir apakšsvītra
        if '_' in text:
            underscore_parts = text.split('_', 1)
            bold_part = underscore_parts[0].strip()
            rest_part = underscore_parts[1].strip()
            return f"<em><strong>{bold_part}</strong>_{rest_part}</em>"
        else:
            return f"<em>{text}</em>"

def verse_lines_from_cell(cell: str):
    """Iegūst panta rindas no Excel šūnas"""
    if not cell: return []
    # Vispirms notīra encoding artefaktus
    cell = clean_verse_text(cell)
    raw_lines = [clean_verse_text(ln) for ln in str(cell).split("\n") if ln.strip()]
    starred = [ln[1:-1].strip() for ln in raw_lines if ln.startswith("*") and ln.endswith("*") and len(ln) >= 2]
    return starred if starred else raw_lines

# === App ===
def main():
    st.markdown("<h1>Gauḍīya Vaiṣṇava Verse Finder</h1>", unsafe_allow_html=True)

    # Automātiska ielāde
    if 'database' not in st.session_state and os.path.exists(DEFAULT_DB_FILE):
        with st.spinner('Ielādē datu bāzi...'):
            data, cnt = load_database_from_file(DEFAULT_DB_FILE)
            if data:
                st.session_state['database'] = data
                st.session_state['db_source'] = os.path.basename(DEFAULT_DB_FILE)
                st.session_state['db_count'] = cnt

    # Sānjosla
    with st.sidebar:
        if 'database' not in st.session_state:
            st.error("Datu bāze nav pieejama")
            st.stop()
        
        max_results = st.slider("Max results", 5, 50, 20)
        min_confidence = st.slider("Min %", 10, 80, 30) / 100

    if 'database' not in st.session_state:
        st.error("Datu bāze nav ielādēta. Lūdzu sazinieties ar administratoru.")
        return

    total = st.session_state.get('db_count', len(st.session_state['database']))

    # Virsraksts: Sources (N verses)
    st.markdown(f"<div class='sv-title'>Sources <span class='verses'>({total} verses)</span></div>", unsafe_allow_html=True)

    # Avotu saraksts (divas kolonnas ar šauru atstarpi)
    cited_set = set(d['cited_in'] for d in st.session_state['database'] if d['cited_in'])
    cited_list = sorted(cited_set, key=normalize_for_sorting)
    if cited_list:
        half = (len(cited_list) + 1) // 2
        left = cited_list[:half]; right = cited_list[half:]
        left_html  = "".join(f"<p class='source-item'>{render_cited_item(c)}</p>" for c in left)
        right_html = "".join(f"<p class='source-item'>{render_cited_item(c)}</p>" for c in right)
        html = f"""
        <div class="sources-grid">
          <div>{left_html}</div>
          <div class="gap"></div>
          <div>{right_html}</div>
        </div>"""
        st.markdown(html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Meklēšana
    search_input = st.text_area("", height=80, placeholder="Enter a verse fragment to search... / Введите фрагмент стиха для поиска...")
    if st.button("Find the verse", type="primary"):
        if not search_input.strip():
            st.warning("⚠️ Lūdzu ievadiet meklējamo tekstu!")
            return

        with st.spinner('Finding...'):
            results = search_verses(search_input, st.session_state['database'], max_results, min_confidence)
        
        if not results:
            st.markdown("<p>Nav rezultātu</p>", unsafe_allow_html=True)
            return

        st.markdown(f"<div class='results-header'>REZULTĀTI: '{search_input}' | Atrasti: {len(results)}</div>", unsafe_allow_html=True)

        for result in results:
            verse_data = result['verse_data']
            score = result['score_percent']
            
            # Izveido divas kolonnas: kreisā pantam, labā tulkojumam
            col1, col2 = st.columns([1.2, 1])
            
            with col1:
                st.markdown(f"<p class='result-score'>{score:.0f}%</p>", unsafe_allow_html=True)

                # Pantus drukājam pa rindām ar vienādu nelielu atstarpi UN iekrāsojam fragmentu
                lines = verse_lines_from_cell(verse_data['iast_verse'])
                if lines:
                    highlighted_lines = highlight_verse_lines(lines, search_input, verse_data['iast_verse'])
                    for ln in highlighted_lines:
                        st.markdown(f"<p class='verse-line'>{ln}</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p class='verse-line'>{verse_data['iast_verse']}</p>", unsafe_allow_html=True)

                # Lielāka atstarpe starp pantu un avotiem
                st.markdown("<div class='verse-gap'></div>", unsafe_allow_html=True)

                # Primārais avots
                st.markdown(f"<p class='source-info'>{format_source_and_author(verse_data['original_source'], verse_data['author'])}</p>",
                            unsafe_allow_html=True)
                # Sekundārais avots
                if verse_data['cited_in']:
                    cited_html = render_cited_item(verse_data['cited_in'])
                    if cited_html:
                        st.markdown(f"<p class='source-info'>{cited_html}</p>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<p class='translation-header'>Translation</p>", unsafe_allow_html=True)
                if verse_data['english_translation']:
                    st.markdown(f"<p class='translation-text'>{verse_data['english_translation']}</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p class='translation-text' style='color: #9ca3af;'>No translation available</p>", unsafe_allow_html=True)

            st.markdown("---")

if __name__ == "__main__":
    main()