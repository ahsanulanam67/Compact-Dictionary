import requests
from bs4 import BeautifulSoup
import re
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import time

# Create a session for connection pooling
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept-Language': 'en-US,en;q=0.9'
})

# Cache results with timeout
@lru_cache(maxsize=1000)
def cached_request(url, timeout=5):
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    except Exception:
        return None

def get_english_definition(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    response = cached_request(url)
    return response.json() if response else None

def get_bangla_definition(word):
    url = f"https://www.english-bangla.com/dictionary/{word}"
    response = cached_request(url)
    return response.text if response else None

def get_cambridge_definition(word):
    url = f"https://dictionary.cambridge.org/dictionary/english/{word}"
    response = cached_request(url)
    return response.text if response else None

def parallel_fetch(word):
    with ThreadPoolExecutor() as executor:
        english_future = executor.submit(get_english_definition, word)
        bangla_future = executor.submit(get_bangla_definition, word)
        cambridge_future = executor.submit(get_cambridge_definition, word)
        
        english_data = english_future.result()
        bangla_data = bangla_future.result()
        cambridge_data = cambridge_future.result()
        
    return english_data, bangla_data, cambridge_data

def parse_english_data(data):
    if not data:
        return {}
    
    entry = data[0] if isinstance(data, list) else data
    result = {
        'word': entry.get('word', ''),
        'phonetic': entry.get('phonetic', ''),
        'meanings': []
    }
    
    for meaning in entry.get('meanings', [])[:3]:  # Limit to 3 meanings
        definitions = []
        examples = []
        
        for d in meaning.get('definitions', [])[:3]:  # Limit to 3 definitions
            definition = d.get('definition', '').strip()
            example = d.get('example', '').strip()
            
            if definition:
                definitions.append({
                    'definition': definition,
                    'example': example
                })
            if example:
                examples.append(example)
        
        result['meanings'].append({
            'partOfSpeech': meaning.get('partOfSpeech', '').lower(),
            'definitions': definitions,
            'synonyms': meaning.get('synonyms', [])[:5],
            'antonyms': meaning.get('antonyms', [])[:5],
            'examples': examples[:3]  # Limit to 3 examples
        })
    
    return result

def parse_bangla_data(html):
    if not html:
        return {}
    
    soup = BeautifulSoup(html, 'html.parser')
    meanings = []
    pronunciation = ''
    
    # Extract meanings (limit to 3)
    meaning_spans = soup.find_all('span', class_='format1')[:3]
    for span in meaning_spans:
        text = span.get_text(' ', strip=True)
        if text:
            meanings.append(text)
    
    # Extract pronunciation
    pron_span = soup.find('span', class_='prnc')
    if pron_span:
        pronunciation = pron_span.get_text(strip=True)
    
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
    
    # Process only first 3 entries
    entries = soup.find_all('div', class_='entry-body__el')[:3]
    for entry in entries:
        pos = entry.find('span', class_='pos')
        pos_text = pos.get_text(strip=True).lower() if pos else ''
        
        # Process only first 3 definition blocks
        def_blocks = entry.find_all('div', class_='def-block ddef_block')[:3]
        for def_block in def_blocks:
            definition = def_block.find('div', class_='def ddef_d db')
            if definition:
                def_text = ' '.join(definition.get_text(' ', strip=True).split())
                def_text = re.sub(r'[^\w\s;,:\.\-]', '', def_text)
                def_text = def_text.replace(':', ': ').strip()
                
                if def_text:
                    result['definitions'].append({
                        'partOfSpeech': pos_text,
                        'definition': def_text
                    })
            
            # Limit to 2 examples per definition
            example_spans = def_block.find_all('span', class_='eg deg')[:2]
            for ex in example_spans:
                ex_text = ' '.join(ex.stripped_strings)
                ex_text = ' '.join(ex_text.split()).strip()
                if ex_text:
                    result['examples_by_pos'].setdefault(pos_text, []).append(ex_text)
    
    return result

def merge_data(word, english_data, cambridge_data):
    if not english_data and not cambridge_data:
        return {}
    
    merged = {
        'word': word,
        'phonetic': english_data.get('phonetic', ''),
        'meanings': []
    }
    
    # Group Cambridge definitions by part of speech
    cambridge_pos = {}
    for d in cambridge_data.get('definitions', []):
        pos = d.get('partOfSpeech', '')
        cambridge_pos.setdefault(pos, []).append({
            'definition': d.get('definition', ''),
            'example': ''
        })
    
    # Merge with English data
    for meaning in english_data.get('meanings', []):
        pos = meaning.get('partOfSpeech', '').lower()
        merged_definitions = meaning.get('definitions', [])
        
        # Add Cambridge definitions for this POS
        if pos in cambridge_pos:
            merged_definitions.extend(cambridge_pos[pos][:3])  # Limit to 3
        
        merged['meanings'].append({
            'partOfSpeech': pos,
            'definitions': merged_definitions[:3],  # Limit to 5 definitions total
            'examples': meaning.get('examples', []) + 
                       cambridge_data.get('examples_by_pos', {}).get(pos, [])[:3],
            'synonyms': meaning.get('synonyms', [])[:5],
            'antonyms': meaning.get('antonyms', [])[:5]
        })
    
    # Add any Cambridge meanings not in English data
    for pos, definitions in cambridge_pos.items():
        if pos not in [m['partOfSpeech'] for m in merged['meanings']]:
            merged['meanings'].append({
                'partOfSpeech': pos,
                'definitions': definitions[:3],
                'examples': cambridge_data.get('examples_by_pos', {}).get(pos, [])[:3],
                'synonyms': [],
                'antonyms': []
            })
    
    return merged