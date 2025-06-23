from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .utils import (
    get_english_definition,
    get_bangla_definition,
    get_cambridge_definition,
    parse_english_data,
    parse_bangla_data,
    parse_cambridge_data,
    merge_data
)

@api_view(['GET'])
def dictionary_lookup(request):
    word = request.GET.get('word', '').strip().lower()
    if not word.isalpha():
        return Response({"error": "Invalid word. Only alphabets allowed."}, status=status.HTTP_400_BAD_REQUEST)

    english_json = get_english_definition(word)
    bangla_html = get_bangla_definition(word)
    cambridge_html = get_cambridge_definition(word)

    english_data = parse_english_data(english_json) if english_json else {}
    bangla_data = parse_bangla_data(bangla_html) if bangla_html else {}
    cambridge_data = parse_cambridge_data(cambridge_html) if cambridge_html else {}

    merged = merge_data(word, english_data, cambridge_data)

    return Response({
        "word": word,
        "english": merged,
        "bangla": bangla_data
    })
