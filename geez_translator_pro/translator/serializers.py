from rest_framework import serializers
from .models import GezDocument

class GezDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GezDocument
        fields = ['id', 'file', 'uploaded_at', 'extracted_geez_text', 'translated_text']
        read_only_fields = ['extracted_geez_text', 'translated_text']
        