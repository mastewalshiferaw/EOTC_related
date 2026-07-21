from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import perform_top_tier_ocr
from .translation_service import translate_flexible

class OCROnlyView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"text": "System Error: No file received"}, status=400)
        
        # Read file bytes and send to Google Vision
        extracted_text = perform_top_tier_ocr(file.read())
        return Response({"text": extracted_text})

class TranslateFlexibleView(APIView):
    def post(self, request):
        text = request.data.get('text', '')
        source = request.data.get('source', "Ge'ez")
        target = request.data.get('target', "Amharic")
        
        if not text:
            return Response({"translation": "No text provided"}, status=400)
            
        result = translate_flexible(text, source, target)
        return Response({"translation": result})