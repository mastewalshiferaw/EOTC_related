from rest_framework.views import APIView
from rest_framework.response import Response
from .services import perform_top_tier_ocr
from .translation_service import translate_flexible

class OCROnlyView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided"}, status=400)
        
        # Read the file bytes and send to OCR
        text = perform_top_tier_ocr(file.read())
        return Response({"text": text})

class TranslateFlexibleView(APIView):
    def post(self, request):
        text = request.data.get('text', '')
        source = request.data.get('source', "Ge'ez")
        target = request.data.get('target', "Amharic")
        
        if not text:
            return Response({"error": "No text provided"}, status=400)
            
        translation = translate_flexible(text, source, target)
        return Response({"translation": translation})