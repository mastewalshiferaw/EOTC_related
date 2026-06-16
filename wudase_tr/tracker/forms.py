from django import forms
from .models import Paragraph

class ParagraphForm(forms.ModelForm):
    class Meta:
        model = Paragraph
        fields = ['day_name', 'order_index', 'image']
        widgets = {
            'day_name': forms.Select(choices=[('Yezewetir Tselot', 'ጸሎተ ዘዘወትር'),('Monday', 'ሰኞ'), ('Tuesday', 'ማክሰኞ'), 
                                              ('Wednesday', 'ረቡዕ'), 
                                              ('Thursday', 'ሐሙስ'), ('Friday', 'ዓርብ'), ('Saturday', 'ቅዳሜ'), ('Sunday', 'እሁድ'), 
                                              ('Anktse berhan', 'አንቀጽ ብርሀን'),('Melka Mariam', 'መልክዐ ማርያም' ),('Melka iyesus', 'መልክዐ እየሱስ')]),
            'order_index': forms.NumberInput(attrs={'placeholder': 'Paragraph Number'}),
        }