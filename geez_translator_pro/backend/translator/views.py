from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import GezDocument
from .serializers import GezDocumentSerializer
from .services import extract_text_from_any_file
from .translation_service import translate_text

class DocumentUploadView(APIView):
    def post(self, request):
        serializer = GezDocumentSerializer(data=request.data)
        if serializer.is_valid():
            doc = serializer.save()
            
            # 1. OCR Step
            geez_text = extract_text_from_any_file(doc.file.path)
            doc.extracted_geez_text = geez_text
            
            # 2. Translation Step (Gemini)
            target = request.data.get('target', 'amh_Ethi')
            translation = translate_text(geez_text, target_lang=target)
            doc.translated_text = translation
            
            doc.save()
            
            return Response({
                "original_geez": geez_text,
                "translated_text": translation
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DirectTranslateView(APIView):
    def post(self, request):
        text = request.data.get('text', '')
        target = request.data.get('target', 'amh_Ethi')
        
        if not text:
            return Response({"error": "No text provided"}, status=400)
            
        translation = translate_text(text, target_lang=target)
        return Response({
            "original_geez": text,
            "translated_text": translation
        })