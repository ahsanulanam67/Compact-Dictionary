# utils.py
import requests
from bs4 import BeautifulSoup
import re

word = "Exaggerate"

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
    if not html:
        return {}
    soup = BeautifulSoup(html, 'html.parser')
    meanings = [span.get_text(strip=True) for span in soup.find_all('span', class_='format1')[:3]]
    pron_span = soup.find('span', class_='prnc')
    pronunciation = pron_span.get_text(strip=True) if pron_span else ''
    return {
        'meanings': meanings,
        'pronunciation': pronunciation
    }

def parse_cambridge_data(html):
    if not html:
        return {}
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
            example_spans = def_block.find_all('span', class_='eg deg')
            for ex in example_spans[:2]:
                ex_text = ' '.join(ex.stripped_strings)
                ex_text = ' '.join(ex_text.split())
                if ex_text:
                    result.setdefault('examples_by_pos', {}).setdefault(pos_text, []).append(ex_text)
    return result

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

