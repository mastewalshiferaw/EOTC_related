from django.db import models

class GezDocument(models.Model):
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # This will hold the text we extract via OCR
    extracted_geez_text = models.TextField(blank=True)
    
    # This will hold the final translation
    translated_text = models.TextField(blank=True)

    def __str__(self):
        return f"Doc {self.id} - {self.uploaded_at}"