from rest_framework.views import APIView
from rest_framework.response import Response
from .services import perform_hybrid_ocr
from .translation_service import translate_flexible

class OCROnlyView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"text": "No file received"}, status=400)
        
        # Read desired language from form data (defaulting to Ge'ez / Amharic)
        lang = request.data.get('lang', 'amh')
        text = perform_hybrid_ocr(file.read(), lang=lang)
        return Response({"text": text})

class TranslateFlexibleView(APIView):
    def post(self, request):
        text = request.data.get('text', '')
        source = request.data.get('source', "Ge'ez")
        target = request.data.get('target', "Amharic")
        
        translation = translate_flexible(text, source, target)
        return Response({"translation": translation})
