from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GezDocumentSerializer
from .services import extract_geez_from_image
from .translation_service import translate_text # Import the new service

class DocumentUploadView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = GezDocumentSerializer(data=request.data)
        
        if serializer.is_valid():
            # 1. Save the file
            doc = serializer.save()
            
            # 2. Run OCR (Ge'ez Extraction)
            extracted_text = extract_geez_from_image(doc.file.path)
            doc.extracted_geez_text = extracted_text
            
            # 3. Run Translation (to Amharic by default)
            # You can also get 'target_lang' from request.data if you want
            try:
                translated = translate_text(extracted_text, target_lang="amh_Ethi")
                doc.translated_text = translated
            except Exception as e:
                doc.translated_text = f"Translation Error: {str(e)}"
            
            # 4. Save all results
            doc.save()
            
            return Response({
                "id": doc.id,
                "original_geez": doc.extracted_geez_text,
                "translated_text": doc.translated_text
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DirectTranslateView(APIView):
    def post(self, request):
        text = request.data.get('text', '')
        target_lang = request.data.get('target', 'amh_Ethi') # Default to Amharic
        
        if not text:
            return Response({"error": "No text provided"}, status=400)
            
        translated = translate_text(text, target_lang=target_lang)
        return Response({
            "original_geez": text,
            "translated_text": translated
        })