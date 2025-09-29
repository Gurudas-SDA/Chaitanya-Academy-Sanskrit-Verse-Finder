# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import re
import unicodedata
import os
from rapidfuzz import fuzz
from difflib import SequenceMatcher

st.set_page_config(page_title="Sanskrit Verse Finder", layout="wide")

# === Ceļš uz datubāzi (Excel blakus app.py) ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_FILE = os.path.join(SCRIPT_DIR, "250928Versebase_app.xlsx")

# === CSS ===
st.markdown("""
<style>
/* pamatteksts */
p { margin: 0; line-height: 1.2; }

/* Virsraksts + mazāks (N verses) */
.sv-title { font-size: 2rem; font-weight: 700; margin: 0.5rem 0 0.75rem 0; }
.sv-title .verses { font-size: 50%; font-weight: 500; }

/* Avotu saraksts: ciešs divkolonnu režģis ar šauru atstarpi */
.sources-grid {
  display: grid;
  grid-template-columns: 1fr 12px 1fr;  /* 12px – ļoti šaura atstarpe */
  column-gap: 8px;
  align-items: start;
}
.sources-grid .gap { width: 12px; }
.source-item { margin-bottom: 0.35rem; font-size: 0.95rem; }

/* ATSTARPES KONTROLE */
:root{
  --verse-line-gap: 0.15rem; /* starp panta rindiņām (tikpat kā starp avotu ierakstiem) */
  --verse-block-gap: 0.6rem; /* starp pēdējo panta rindu un avotiem */
}
.verse-line { margin: 0 0 var(--verse-line-gap) 0; line-height: 1.2; }
.verse-gap  { height: var(--verse-block-gap); }

/* Sarkans highlight meklētajam fragmentam */
.highlight { color: #dc2626; font-weight: 600; }

.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# === Palīgfunkcijas ===
def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('-', '').replace(' ', '').replace('\n', '')
    text = re.sub(r'[^\w]', '', text)
    return text.lower().strip()

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

def count_words_with_matches(search_text: str, full_verse: str) -> int:
    """Skaita cik dažādos vārdos ir sakritošie burti"""
    normalized_search = normalize_text(search_text)
    normalized_full = normalize_text(full_verse)
    
    if not normalized_search or not normalized_full:
        return 999
    
    # Atrod fragmenta pozīciju
    pos = normalized_full.find(normalized_search)
    if pos < 0:
        best_pos = -1
        best_score = 0
        for i in range(len(normalized_full) - len(normalized_search) + 1):
            window = normalized_full[i:i+len(normalized_search)]
            score = fuzz.ratio(normalized_search, window)
            if score > best_score:
                best_score = score
                best_pos = i
        if best_score < 60:
            return 999
        pos = best_pos
    
    # Ņem fragmentu
    fragment_length = len(normalized_search)
    margin = int(fragment_length * 0.2)
    start_pos = max(0, pos - margin)
    end_pos = min(len(normalized_full), pos + fragment_length + margin)
    fragment = normalized_full[start_pos:end_pos]
    
    # Atrod sakritības
    matcher = SequenceMatcher(None, normalized_search, fragment)
    matching_positions = set()
    for _, b_start, size in matcher.get_matching_blocks():
        for i in range(size):
            matching_positions.add(start_pos + b_start + i)
    
    if not matching_positions:
        return 999
    
    # Izveido mapping uz vārdiem oriģinālajā tekstā
    words = full_verse.split()
    norm_pos_to_word = {}
    current_norm_pos = 0
    
    for word_idx, word in enumerate(words):
        normalized_word = normalize_text(word)
        for _ in normalized_word:
            norm_pos_to_word[current_norm_pos] = word_idx
            current_norm_pos += 1
    
    # Skaita cik dažādos vārdos ir sakritības
    words_with_matches = set()
    for norm_pos in matching_positions:
        if norm_pos in norm_pos_to_word:
            words_with_matches.add(norm_pos_to_word[norm_pos])
    
    return len(words_with_matches)

def highlight_verse_lines(lines: list, search_text: str, full_verse: str) -> list:
    """Iekrāso tikai tos burtus kas sakrīt meklētā fragmenta ietvaros"""
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
    
    # Pārvērš relatīvās pozīcijas fragmentā uz absolūtām pozīcijām
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
    df = pd.read_excel(file_path, sheet_name=0)
    database = []
    for _, row in df.iterrows():
        if pd.notna(row.get('IAST Verse')) and str(row.get('IAST Verse')).strip():
            database.append({
                'iast_verse': str(row.get('IAST Verse', '')).strip(),
                'original_source': str(row.get('Original Source', '')).strip(),
                'author': str(row.get('Author', '')).strip(),
                'context': str(row.get('Context', '')).strip(),
                'english_translation': str(row.get('English Translation', '')).strip(),
                'cited_in': str(row.get('Cited In', '')).strip()
            })
    return database, len(database)

@st.cache_data
def load_database(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            import csv
            content = uploaded_file.read().decode('utf-8-sig')
            lines = content.splitlines()
            delimiter = ',' if content.count(',') >= content.count(';') else ';'
            reader = csv.DictReader(lines, delimiter=delimiter)
            database = []
            for row in reader:
                if row.get('IAST Verse') and row.get('IAST Verse').strip():
                    database.append({
                        'iast_verse': str(row.get('IAST Verse', '')).strip(),
                        'original_source': str(row.get('Original Source', '')).strip(),
                        'author': str(row.get('Author', '')).strip(),
                        'context': str(row.get('Context', '')).strip(),
                        'english_translation': str(row.get('English Translation', '')).strip(),
                        'cited_in': str(row.get('Cited In', '')).strip()
                    })
        else:
            df = pd.read_excel(uploaded_file, sheet_name=0)
            database = []
            for _, row in df.iterrows():
                if pd.notna(row.get('IAST Verse')) and str(row.get('IAST Verse')).strip():
                    database.append({
                        'iast_verse': str(row.get('IAST Verse', '')).strip(),
                        'original_source': str(row.get('Original Source', '')).strip(),
                        'author': str(row.get('Author', '')).strip(),
                        'context': str(row.get('Context', '')).strip(),
                        'english_translation': str(row.get('English Translation', '')).strip(),
                        'cited_in': str(row.get('Cited In', '')).strip()
                    })
        return database, len(database)
    except Exception as e:
        return None, str(e)

def search_verses(search_text: str, database, max_results=20, min_confidence=0.3):
    results = []
    
    # Skaita cik vārdi ir meklējamajā frāzē
    search_words_count = len(search_text.split())
    
    for verse_data in database:
        score, position, prefix_len = calculate_fragment_match(search_text, verse_data['iast_verse'])
        
        if score < min_confidence:
            continue
        
        # Pārbauda cik vārdos ir sakritības
        words_with_matches = count_words_with_matches(search_text, verse_data['iast_verse'])
        
        # Ja sakritības ir vairāk vārdos nekā meklējamajā frāzē - izmet
        if words_with_matches > search_words_count:
            continue
        
        results.append({
            'verse_data': verse_data, 
            'confidence': score, 
            'score_percent': score * 100,
            'position': position,
            'prefix_length': prefix_len
        })
    
    # Kārtojums: 
    # 1. confidence (dilstošā) 
    # 2. prefix_length (dilstošā) - jo vairāk secīgo, jo labāk
    # 3. pozīcija (augošā) - jo agrāk, jo labāk
    results.sort(key=lambda x: (-x['confidence'], -x['prefix_length'], x['position']))
    return results[:max_results]

def clean_author(author: str) -> str:
    if not author: return ""
    return re.sub(r'^\s*by\s+', '', str(author), flags=re.I).strip()

def format_source_and_author(source, author) -> str:
    a = clean_author(author)
    if source and a: return f"{source} (by {a})"
    if source: return source
    if a: return f"(by {a})"
    return "NOT AVAILABLE"

# ——— "by" formatēšana Source sarakstam: **Title** by Author, viss slīprakstā
_by_regex = re.compile(r"\s+by\s+", re.IGNORECASE)
def render_cited_item(text: str) -> str:
    parts = _by_regex.split(text, maxsplit=1)
    if len(parts) == 2:
        title, author = parts[0].strip(), parts[1].strip()
        return f"<em><strong>{title}</strong> by {author}</em>"
    return f"<em>{text}</em>"

# ——— Panta rindas pēc Excel šūnas struktūras
def verse_lines_from_cell(cell: str):
    if not cell: return []
    raw_lines = [ln.strip() for ln in str(cell).split("\n") if ln.strip()]
    starred = [ln[1:-1].strip() for ln in raw_lines if ln.startswith("*") and ln.endswith("*") and len(ln) >= 2]
    return starred if starred else raw_lines

# === App ===
def main():
    st.markdown("<h1>Sanskrit Verse Finder</h1>", unsafe_allow_html=True)

    # Automātiska ielāde no blakus esošā Excel
    if 'database' not in st.session_state and os.path.exists(DEFAULT_DB_FILE):
        data, cnt = load_database_from_file(DEFAULT_DB_FILE)
        if data:
            st.session_state['database'] = data
            st.session_state['db_source'] = os.path.basename(DEFAULT_DB_FILE)
            st.session_state['db_count'] = cnt

    # Sānjosla
    with st.sidebar:
        st.markdown("### Datu bāze")
        st.text("=== DEBUG ===")
        st.text(f"Fails eksistē: {os.path.exists(DEFAULT_DB_FILE)}")
        st.text(f"DB ielādēta: {'database' in st.session_state}")
        st.code(DEFAULT_DB_FILE, language=None)

        uploaded_file = st.file_uploader("Augšupielādēt (rezerves variants)", type=['xlsx', 'xls', 'csv'])
        if uploaded_file:
            data, cnt_or_err = load_database(uploaded_file)
            if data:
                st.session_state['database'] = data
                st.session_state['db_source'] = uploaded_file.name
                st.session_state['db_count'] = cnt_or_err
                st.rerun()
            else:
                st.error(f"Kļūda: {cnt_or_err}")

        max_results = st.slider("Max rezultāti", 5, 50, 20)
        min_confidence = st.slider("Min %", 10, 80, 30) / 100
        st.checkbox("Debug režīms", value=False)

    if 'database' in st.session_state:
        total = st.session_state.get('db_count', len(st.session_state['database']))

        # Virsraksts: Sources (N verses) – N uz pusi mazāks
        st.markdown(f"<div class='sv-title'>Sources <span class='verses'>({total} verses)</span></div>", unsafe_allow_html=True)

        # Avotu saraksts (divas kolonnas ar šauru atstarpi)
        cited_list = sorted(set(d['cited_in'] for d in st.session_state['database'] if d['cited_in']))
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
        search_input = st.text_area("", height=80, placeholder="sarva-dharmān parityajya")
        if st.button("Find the verse", type="primary"):
            if not search_input.strip():
                st.warning("Ierakstiet tekstu!")
                return

            results = search_verses(search_input, st.session_state['database'], max_results, min_confidence)
            if not results:
                st.markdown("<p>Nav rezultātu</p>", unsafe_allow_html=True)
                return

            st.markdown(f"<p><b>REZULTĀTI:</b> '{search_input}' | Atrasti: {len(results)}</p>", unsafe_allow_html=True)
            st.markdown("---")

            for result in results:
                verse_data = result['verse_data']
                score = result['score_percent']
                st.markdown(f"<p><b>{score:.0f}%</b></p>", unsafe_allow_html=True)

                # Pantus drukājam pa rindiņām ar vienādu nelielu atstarpi UN iekrāsojam fragmentu
                lines = verse_lines_from_cell(verse_data['iast_verse'])
                if lines:
                    highlighted_lines = highlight_verse_lines(lines, search_input, verse_data['iast_verse'])
                    for ln in highlighted_lines:
                        st.markdown(f"<p class='verse-line'>{ln}</p>", unsafe_allow_html=True)
                else:
                    # Fallback ja nav rindu
                    st.markdown(f"<p class='verse-line'>{verse_data['iast_verse']}</p>", unsafe_allow_html=True)

                # Lielāka atstarpe starp pantu un avotiem
                st.markdown("<div class='verse-gap'></div>", unsafe_allow_html=True)

                # Primārais avots
                st.markdown(f"<p>{format_source_and_author(verse_data['original_source'], verse_data['author'])}</p>",
                            unsafe_allow_html=True)
                # Sekundārais avots (slīpraksts, nosaukums treknrakstā)
                if verse_data['cited_in']:
                    st.markdown(f"<p>{render_cited_item(verse_data['cited_in'])}</p>", unsafe_allow_html=True)

                st.markdown("---")

if __name__ == "__main__":
    main()
