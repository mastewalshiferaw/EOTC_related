from rest_framework.views import APIView
from rest_framework.response import Response
from .services import perform_top_tier_ocr
from .translation_service import translate_dual

class OCROnlyView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file"}, status=400)
        
        text = perform_top_tier_ocr(file.read())
        return Response({"text": text})

class TranslateDualView(APIView):
    def post(self, request):
        text = request.data.get('text', '')
        translations = translate_dual(text)
        return Response(translations)