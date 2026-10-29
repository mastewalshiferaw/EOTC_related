import os
from rest_framework.views import APIView
from rest_framework.response import Response
from .services import perform_hybrid_ocr, restore_fidel_ocr_text
from .translation_service import translate_flexible

class OCROnlyView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"text": "No file received"}, status=400)
        
        # Fast local OCR: returns in < 0.5s
        lang = request.data.get('lang', 'amh')
        provider = request.data.get('provider')
        auto_clean = request.data.get('auto_clean', 'true').lower() == 'true'
        
        text = perform_hybrid_ocr(file.read(), lang=lang, provider=provider, auto_clean=auto_clean)
        active_provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        return Response({"text": text, "provider": active_provider})

class CleanOCRView(APIView):
    def post(self, request):
        text = request.data.get('text', '')
        provider = request.data.get('provider')
        cleaned = restore_fidel_ocr_text(text, provider=provider)
        return Response({"text": cleaned})

class TranslateFlexibleView(APIView):
    def post(self, request):
        text = request.data.get('text', '')
        source = request.data.get('source', "Ge'ez")
        target = request.data.get('target', "Amharic")
        provider = request.data.get('provider')
        
        translation = translate_flexible(text, source, target, provider=provider)
        active_provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        return Response({"translation": translation, "provider": active_provider})
