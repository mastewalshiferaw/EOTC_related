from django import forms
from .models import Paragraph

class ParagraphForm(forms.ModelForm):
    class Meta:
        model = Paragraph
        fields = ['day_name', 'order_index', 'image']
        widgets = {
            'day_name': forms.Select(choices=[('Monday', 'ሰኞ'), ('Tuesday', 'ማክሰኞ'), ('Wednesday', 'ረቡዕ'), 
                                              ('Thursday', 'ሐሙስ'), ('Friday', 'ዓርብ'), ('Saturday', 'ቅዳሜ'), ('Sunday', 'እሁድ')]),
            'order_index': forms.NumberInput(attrs={'placeholder': 'Paragraph Number'}),
        }