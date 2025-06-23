from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from .utils import parallel_fetch, parse_english_data, parse_bangla_data, parse_cambridge_data, merge_data
import logging
import time  # Add this import

logger = logging.getLogger(__name__)

@api_view(['GET'])
def dictionary_lookup(request):
    word = request.GET.get('word', '').strip().lower()
    
    # Validate input
    if not word or not word.isalpha():
        return Response(
            {"error": "Invalid word. Only alphabetic characters allowed."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check cache first
    cache_key = f"dict_{word}"
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Serving from cache: {word}")
        return Response(cached_result)
    
    logger.info(f"Processing new request: {word}")
    start_time = time.time()
    
    try:
        # Parallel fetch from all sources
        english_json, bangla_html, cambridge_html = parallel_fetch(word)
        
        # Parse data
        english_data = parse_english_data(english_json) if english_json else {}
        bangla_data = parse_bangla_data(bangla_html) if bangla_html else {}
        cambridge_data = parse_cambridge_data(cambridge_html) if cambridge_html else {}
        
        # Merge results
        merged = merge_data(word, english_data, cambridge_data)
        response_data = {
            "word": word,
            "english": merged,
            "bangla": bangla_data
        }
        
        # Cache successful response for 24 hours
        cache.set(cache_key, response_data, timeout=60*60*24)
        
        logger.info(f"Request completed in {time.time() - start_time:.2f}s")
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error processing {word}: {str(e)}")
        return Response(
            {"error": "Failed to fetch dictionary data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )