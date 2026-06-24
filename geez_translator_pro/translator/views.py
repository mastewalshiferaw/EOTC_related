from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GezDocumentSerializer
from .services import extract_geez_from_image

class DocumentUploadView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = GezDocumentSerializer(data=request.data)
        
        if serializer.is_valid():
            # 1. Save the file to the database
            doc = serializer.save()
            
            # 2. Get the absolute path of the uploaded file
            image_path = doc.file.path
            
            # 3. Run OCR (Ge'ez Extraction)
            extracted_text = extract_geez_from_image(image_path)
            
            # 4. Update the record with the text
            doc.extracted_geez_text = extracted_text
            doc.save()
            
            return Response({
                "message": "File processed successfully",
                "geez_text": extracted_text,
                "document_id": doc.id
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)