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



class TranslationCache(models.Model):
    # We store the hash of the text to make lookups very fast
    source_text = models.TextField()
    source_lang = models.CharField(max_length=50)
    target_lang = models.CharField(max_length=50)
    translated_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent duplicate entries for the same translation
        unique_together = ('source_text', 'source_lang', 'target_lang')

    def __str__(self):
        return f"{self.source_lang} -> {self.target_lang}: {self.source_text[:20]}..."