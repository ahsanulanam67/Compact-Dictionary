import tkinter as tk
from tkinter import ttk, messagebox
import threading
import re
import requests
from bs4 import BeautifulSoup
import textwrap

# -------------------- Helper functions --------------------
def get_english_definition(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None

def get_bangla_definition(word):
    try:
        url = f"https://www.english-bangla.com/dictionary/{word}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception:
        return None

def get_cambridge_definition(word):
    try:
        url = f"https://dictionary.cambridge.org/dictionary/english/{word}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception:
        return None

def parse_english_data(data):
    if not data:
        return {}
    entry = data[0]
    result = {
        'word': entry.get('word', ''),
        'phonetic': entry.get('phonetic', ''),
        'meanings': []
    }
    for meaning in entry.get('meanings', []):
        definitions = []
        for d in meaning.get('definitions', [])[:3]:
            definitions.append({
                'definition': d.get('definition', ''),
                'example': d.get('example', '')
            })
        examples = [d['example'] for d in meaning.get('definitions', []) if 'example' in d][:3]
        result['meanings'].append({
            'partOfSpeech': meaning.get('partOfSpeech', ''),
            'definitions': definitions,
            'synonyms': meaning.get('synonyms', [])[:5],
            'antonyms': meaning.get('antonyms', [])[:5],
            'examples': examples
        })
    return result

def parse_bangla_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    meanings = [span.get_text(strip=True) for span in soup.find_all('span', class_='format1')[:3]]
    pron_span = soup.find('span', class_='prnc')
    pronunciation = pron_span.get_text(strip=True) if pron_span else ''
    return {
        'meanings': meanings,
        'pronunciation': pronunciation
    }

def parse_cambridge_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    result = {
        'definitions': [],
        'examples_by_pos': {}
    }
    entries = soup.find_all('div', class_='entry-body__el')
    for entry in entries[:3]:
        pos = entry.find('span', class_='pos')
        pos_text = pos.get_text(strip=True).lower() if pos else ''
        def_blocks = entry.find_all('div', class_='def-block ddef_block')
        for def_block in def_blocks[:3]:
            definition = def_block.find('div', class_='def ddef_d db')
            if definition:
                def_text = ' '.join(definition.get_text(' ', strip=True).split())
                def_text = re.sub(r'[^\w\s;,:\.\-]', '', def_text)
                def_text = def_text.replace(':', ': ')
                if def_text:
                    result['definitions'].append({
                        'partOfSpeech': pos_text,
                        'definition': def_text
                    })

            # Examples from <span class="eg deg">
            example_spans = def_block.find_all('span', class_='eg deg')

            # Also find <ul class="hul-u hul-u0 ca_b daccord_b lm-0"> inside this def_block (or right after)
            # and get all <li class="eg dexamp hax"> inside it
          
            # Combine examples
            all_examples = example_spans 
            
            for ex in all_examples[:2]:  # limit to 2 examples per def_block
                ex_text = ' '.join(ex.stripped_strings)
                ex_text = ' '.join(ex_text.split())
                if ex_text:
                    result.setdefault('examples_by_pos', {}).setdefault(pos_text, []).append(ex_text)
    return result




# Fonts and colors configuration (same as before)
FONT_TITLE = ("Segoe UI Semibold", 24, "bold")
FONT_SECTION = ("Segoe UI Semilight", 16, "bold")
FONT_LABEL = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_MONO = ("Consolas", 11)
FONT_SUBTITLE = ("Segoe UI Light", 12)

# Light and dark theme colors (same as before)
light_theme = {
    "bg": "#f8f9fa",
    "text_bg": "#ffffff",
    "text_fg": "#212529",
    "title_fg": "#0d6efd",
    "section_fg": "#6c757d",
    "label_fg": "#1a5276",
    "pronunciation_fg": "#1d1d1d",
    "bangla_meaning_fg": "#145a32",
    "definition_fg": "#212f3c",
    "examples_label_fg": "#d35400",
    "examples_fg": "#7f8c8d",
    "synonyms_fg": "#1f618d",
    "antonyms_fg": "#c0392b",
    "info_fg": "#888888",
    "error_fg": "#cc0000",
    "button_bg": "#007acc",
    "button_fg": "white",
    "button_active_bg": "#005f99",
    "button_disabled_bg": "#cccccc",
    "button_disabled_fg": "#666666",
    "entry_bg": "white",
    "entry_fg": "black",
    "entry_highlight": "#007acc"
}

dark_theme = {
    "bg": "#212529",
    "text_bg": "#2c3034",
    "text_fg": "#e9ecef",
    "title_fg": "#4dabf7",
    "section_fg": "#adb5bd",
    "label_fg": "#a1c4d1",
    "pronunciation_fg": "#d6d6d6",
    "bangla_meaning_fg": "#85c894",
    "definition_fg": "#c7d1d9",
    "examples_label_fg": "#f39c12",
    "examples_fg": "#a7b1b9",
    "synonyms_fg": "#74a9d8",
    "antonyms_fg": "#e57373",
    "info_fg": "#bbbbbb",
    "error_fg": "#ff6b6b",
    "button_bg": "#375a7f",
    "button_fg": "white",
    "button_active_bg": "#2a4661",
    "button_disabled_bg": "#4a4a4a",
    "button_disabled_fg": "#999999",
    "entry_bg": "#3b4252",
    "entry_fg": "white",
    "entry_highlight": "#4dabf7"
}

class DictionaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("E2E and E2B Dictionary")
        self.theme = 'light'
        self.colors = dark_theme
        
        # Configure window
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        self.root.configure(bg=self.colors["bg"])
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # Header
        self.header_frame = tk.Frame(root, bg=self.colors["bg"])
        self.header_frame.pack(pady=(20, 5), fill=tk.X)
        
        self.title_lbl = tk.Label(
            self.header_frame, 
            text="E2E and E2B Dictionary", 
            font=FONT_TITLE, 
            fg=self.colors["title_fg"], 
            bg=self.colors["bg"]
        )
        self.title_lbl.pack()
        
        self.subtitle_lbl = tk.Label(
            self.header_frame,
            text="Type an English word and press Enter to explore its full meaning.",
            font=FONT_SUBTITLE,
            fg="#6c757d",
            bg=self.colors["bg"]
        )
        self.subtitle_lbl.pack(pady=(0, 15))
        
        # Search Frame
        self.search_frame = tk.Frame(root, bg=self.colors["bg"])
        self.search_frame.pack(pady=10, fill=tk.X, padx=20)
        
        self.entry_word = tk.Entry(
            self.search_frame,
            font=("Segoe UI", 14),
            width=30,
            bd=0,
            relief=tk.FLAT,
            highlightthickness=2,
            highlightbackground="#cccccc",
            highlightcolor=self.colors["entry_highlight"],
            bg=self.colors["entry_bg"],
            fg=self.colors["entry_fg"]
        )
        self.entry_word.pack(side=tk.LEFT, padx=(0, 10), ipady=8, fill=tk.X, expand=True)
        
        self.btn_search = ttk.Button(
            self.search_frame,
            text="🔍 Search Meaning",
            style='Search.TButton',
            command=self.on_search
        )
        self.btn_search.pack(side=tk.LEFT)
        
        self.entry_word.bind('<Return>', self.on_search)
        
        # Theme Toggle
        self.btn_toggle = ttk.Button(
            root,
            text="☀️ Light Mode",
            style='Toggle.TButton',
            command=self.toggle_theme
        )
        self.btn_toggle.pack(pady=(0, 10))
        
        # Result Frame with Scrollbar
        self.result_container = tk.Frame(root, bg=self.colors["bg"])
        self.result_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.txt_result = tk.Text(
            self.result_container,
            wrap=tk.WORD,
            bd=0,
            bg=self.colors["text_bg"],
            fg=self.colors["text_fg"],
            padx=15,
            pady=15,
            font=FONT_NORMAL
        )
        
        self.scrollbar = ttk.Scrollbar(
            self.result_container,
            orient="vertical",
            command=self.txt_result.yview
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.txt_result.config(yscrollcommand=self.scrollbar.set)
        self.txt_result.pack(fill=tk.BOTH, expand=True)
        
        # Footer
        self.footer_lbl = tk.Label(
            root,
            text="📘 Powered by Cambridege & english-bangla.com | Built by Saboj",
            font=("Segoe UI", 9),
            fg="#888888",
            bg=self.colors["bg"]
        )
        self.footer_lbl.pack(side=tk.BOTTOM, pady=(0, 10))
        
        self.configure_tags()
        
    def configure_styles(self):
        self.style.configure('Search.TButton',
            borderwidth=0,
            relief="flat",
            font=FONT_LABEL,
            padding=10,
            foreground=self.colors["button_fg"],
            background=self.colors["button_bg"]
        )
        self.style.map('Search.TButton',
            background=[
                ('active', self.colors["button_active_bg"]),
                ('disabled', self.colors["button_disabled_bg"])
            ],
            foreground=[
                ('active', self.colors["button_fg"]),
                ('disabled', self.colors["button_disabled_fg"])
            ]
        )
        
        self.style.configure('Toggle.TButton',
            borderwidth=0,
            relief="flat",
            font=FONT_LABEL,
            padding=5,
            foreground=self.colors["button_fg"],
            background=self.colors["button_bg"]
        )
        self.style.map('Toggle.TButton',
            background=[
                ('active', self.colors["button_active_bg"]),
                ('disabled', self.colors["button_disabled_bg"])
            ],
            foreground=[
                ('active', self.colors["button_fg"]),
                ('disabled', self.colors["button_disabled_fg"])
            ]
        )
        
        self.style.configure('Vertical.TScrollbar',
            gripcount=0,
            background="#cccccc",
            troughcolor=self.colors["bg"],
            bordercolor=self.colors["bg"],
            arrowcolor=self.colors["text_fg"],
            arrowsize=15
        )

    def configure_tags(self):
        c = self.colors
        txt = self.txt_result
        txt.tag_configure("title", font=FONT_TITLE, foreground=c["title_fg"], spacing1=10, spacing3=10)
        txt.tag_configure("section", font=FONT_SECTION, foreground=c["section_fg"], spacing1=8, spacing3=4)
        txt.tag_configure("label", font=FONT_LABEL, foreground=c["label_fg"])
        txt.tag_configure("pronunciation", font=FONT_NORMAL, foreground=c["pronunciation_fg"])
        txt.tag_configure("bangla_meaning", font=FONT_NORMAL, foreground=c["bangla_meaning_fg"], lmargin1=20, spacing2=0)
        txt.tag_configure("definition", font=FONT_MONO, foreground=c["definition_fg"], lmargin1=20, spacing2=0)
        txt.tag_configure("examples_label", font=FONT_LABEL, foreground=c["examples_label_fg"], spacing3=2)
        txt.tag_configure("examples", font=FONT_NORMAL, foreground=c["examples_fg"], lmargin1=30, spacing2=2)
        txt.tag_configure("synonyms", font=FONT_NORMAL, foreground=c["synonyms_fg"])
        txt.tag_configure("antonyms", font=FONT_NORMAL, foreground=c["antonyms_fg"])
        txt.tag_configure("info", font=FONT_LABEL, foreground=c["info_fg"], spacing3=8)
        txt.tag_configure("error", font=FONT_LABEL, foreground=c["error_fg"])
        txt.tag_configure("divider", font=("Segoe UI", 1), foreground="#e0e0e0", spacing1=5, spacing3=5)

    def toggle_theme(self):
        if self.theme == 'light':
            self.theme = 'dark'
            self.colors = dark_theme
            self.btn_toggle.config(text="☀️ Light Mode")
        else:
            self.theme = 'light'
            self.colors = light_theme
            self.btn_toggle.config(text="🌙 Dark Mode")

        self.root.configure(bg=self.colors["bg"])
        self.header_frame.config(bg=self.colors["bg"])
        self.search_frame.config(bg=self.colors["bg"])
        self.result_container.config(bg=self.colors["bg"])
        self.title_lbl.config(fg=self.colors["title_fg"], bg=self.colors["bg"])
        self.subtitle_lbl.config(fg="#6c757d", bg=self.colors["bg"])
        self.footer_lbl.config(bg=self.colors["bg"])
        
        self.entry_word.config(
            bg=self.colors["entry_bg"],
            fg=self.colors["entry_fg"],
            highlightcolor=self.colors["entry_highlight"]
        )
        
        self.txt_result.config(
            bg=self.colors["text_bg"],
            fg=self.colors["text_fg"]
        )
        
        self.configure_styles()
        self.configure_tags()

    def clear_text_widget(self):
        self.txt_result.config(state=tk.NORMAL)
        self.txt_result.delete('1.0', tk.END)

    def insert_with_tag(self, text, tag=None):
        if tag:
            self.txt_result.insert(tk.END, text, tag)
        else:
            self.txt_result.insert(tk.END, text)

    def display_result(self, english_data, bangla_data):
        self.clear_text_widget()
        if not english_data and not bangla_data:
            self.insert_with_tag("No definitions found for this word.", "error")
            self.txt_result.config(state=tk.DISABLED)
            return

        word = english_data.get('word', 'Unknown')

        # Title with POS
        pos_list = []
        for meaning in english_data.get('meanings', []):
            if meaning.get('partOfSpeech'):
                pos_list.append(meaning.get('partOfSpeech').capitalize())
        pos_str = ", ".join(sorted(set(pos_list)))
        self.insert_with_tag(f"📖 {word.capitalize()}", "title")
        if pos_str:
            self.insert_with_tag(f" ({pos_str})", "section")
        self.insert_with_tag("\n", "title")
        self.insert_with_tag("━"*60 + "\n\n", "divider")

        # Pronunciations
        pronunciation_section = False
        
        if english_data.get('phonetic'):
            self.insert_with_tag("🔊 English Pronunciation: ", "label")
            self.insert_with_tag(english_data['phonetic'] + "\n", "pronunciation")
            pronunciation_section = True
            
        if bangla_data.get('pronunciation'):
            self.insert_with_tag("🔊 Bangla Pronunciation: ", "label")
            self.insert_with_tag(bangla_data['pronunciation'] + "\n", "pronunciation")
            pronunciation_section = True
            
        if pronunciation_section:
            self.insert_with_tag("\n", "divider")

        # Bangla meanings
        if bangla_data.get('meanings'):
            self.insert_with_tag("🌐 Bangla Meanings:\n", "section")
            for i, meaning in enumerate(bangla_data['meanings'][:3], 1):
                wrapped = textwrap.fill(meaning, width=80, subsequent_indent='    ')
                self.insert_with_tag(f"  {i}. {wrapped}\n", "bangla_meaning")
            self.insert_with_tag("\n", "divider")
        else:
            self.insert_with_tag("🌐 Bangla Meanings: Not found\n\n", "section")

        # English meanings
        self.insert_with_tag("📚 English Definitions:\n", "section")
        for meaning in english_data.get('meanings', []):
            # Part of speech
            if meaning.get('partOfSpeech'):
                self.insert_with_tag(f"  {meaning['partOfSpeech'].capitalize()}\n", "label")
            
            # Definitions (limit to 3)
            for i, d in enumerate(meaning.get('definitions', [])[:3], 1):
                def_wrapped = textwrap.fill(d.get('definition', ''), width=80, subsequent_indent='      ')
                self.insert_with_tag(f"  {i}. {def_wrapped}\n", "definition")
                
                # Show example if it exists for this specific definition
                if d.get('example'):
                    ex_wrapped = textwrap.fill(d['example'], width=75, initial_indent='   • ', subsequent_indent='     ')
                    self.insert_with_tag(f"{ex_wrapped}\n", "examples")

            # Examples (additional examples, limit to 3 total)
            examples = meaning.get('examples', [])[:3]
            if examples:
                self.insert_with_tag("📌 Examples:\n", "examples_label")
                for ex in examples[:3]:
                    ex_wrapped = textwrap.fill(ex, width=75, initial_indent='   • ', subsequent_indent='     ')
                    self.insert_with_tag(f"{ex_wrapped}\n", "examples")
                self.insert_with_tag("\n")

            # Synonyms (limit to 5)
            synonyms = meaning.get('synonyms', [])[:5]
            if synonyms:
                self.insert_with_tag("🔄 Synonyms: ", "label")
                self.insert_with_tag(", ".join(synonyms) + "\n", "synonyms")

            # Antonyms (limit to 5)
            antonyms = meaning.get('antonyms', [])[:5]
            if antonyms:
                self.insert_with_tag("🔄 Antonyms: ", "label")
                self.insert_with_tag(", ".join(antonyms) + "\n", "antonyms")

            self.insert_with_tag("\n", "divider")

        self.txt_result.config(state=tk.DISABLED)

    def lookup_word(self, word):
    # Fetch raw data
        cambridge_html = get_cambridge_definition(word)
        english_json = get_english_definition(word)
        bangla_html = get_bangla_definition(word)

        # Parse data
        cambridge_data = parse_cambridge_data(cambridge_html) if cambridge_html else {}
        english_data = parse_english_data(english_json) if english_json else {}
        bangla_data = parse_bangla_data(bangla_html) if bangla_html else {}

        # Build a new english_data structure starting from Cambridge
        merged_data = {
            'word': word,
            'phonetic': english_data.get('phonetic', ''),
            'meanings': []
        }

        if cambridge_data.get('definitions'):
        # Build from Cambridge data
            pos_group = {}
            for d in cambridge_data['definitions']:
                pos = d.get('partOfSpeech', '').lower()
                if pos not in pos_group:
                    pos_group[pos] = []
                pos_group[pos].append({'definition': d['definition'], 'example': ''})

            for pos, defs in pos_group.items():
                # Try to find matching partOfSpeech from API to get synonyms/antonyms
                api_matching = next((m for m in english_data.get('meanings', []) if m.get('partOfSpeech', '').lower() == pos), {})
                matched_examples = cambridge_data.get('examples_by_pos', {}).get(pos, [])[:3]
                
                merged_data['meanings'].append({
                    'partOfSpeech': pos,
                    'definitions': defs[:3],
                    'examples': matched_examples,
                    'synonyms': api_matching.get('synonyms', [])[:5],
                    'antonyms': api_matching.get('antonyms', [])[:5]
                })


        else:
            # Fallback to API if Cambridge has nothing
            merged_data = english_data

        self.display_result(merged_data, bangla_data)
        
    def merge_data(word, english_data, cambridge_data):
        merged_data = {
            'word': word,
            'phonetic': english_data.get('phonetic', ''),
            'meanings': []
        }
        if cambridge_data.get('definitions'):
            pos_group = {}
            for d in cambridge_data['definitions']:
                pos = d.get('partOfSpeech', '').lower()
                pos_group.setdefault(pos, []).append({'definition': d['definition'], 'example': ''})

            for pos, defs in pos_group.items():
                api_matching = next((m for m in english_data.get('meanings', []) if m.get('partOfSpeech', '').lower() == pos), {})
                matched_examples = cambridge_data.get('examples_by_pos', {}).get(pos, [])[:3]
                merged_data['meanings'].append({
                    'partOfSpeech': pos,
                    'definitions': defs[:3],
                    'examples': matched_examples,
                    'synonyms': api_matching.get('synonyms', [])[:5],
                    'antonyms': api_matching.get('antonyms', [])[:5]
                })
        else:
            merged_data = english_data
        return merged_data

    def on_search(self, event=None):
        word = self.entry_word.get().strip()
        if not re.fullmatch(r"[a-zA-Z]+", word):
            messagebox.showerror("Invalid input", "Please enter a valid English word (letters only).")
            return
            
        self.clear_text_widget()
        self.insert_with_tag("Searching... Please wait\n", "info")
        self.txt_result.config(state=tk.DISABLED)
        
        self.btn_search.state(['disabled'])
        
        def task():
            try:
                self.lookup_word(word)
            finally:
                self.root.after(0, lambda: self.btn_search.state(['!disabled']))
                
        threading.Thread(target=task, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = DictionaryApp(root)
    root.mainloop()