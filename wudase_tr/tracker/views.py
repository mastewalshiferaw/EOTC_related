from django.shortcuts import render, redirect
from .models import Paragraph
import random

def upload_paragraph(request):
    if request.method == 'POST':
        # Logic to save the uploaded image
        # User selects Day, Order Index, and uploads file
        new_p = Paragraph.objects.create(
            user=request.user,
            image=request.FILES['para_image'],
            day_name=request.POST['day'],
            order_index=request.POST['order']
        )
        return redirect('dashboard')
    return render(request, 'upload.html')

def daily_challenge(request):
    # Get all paragraphs the user has uploaded
    user_paragraphs = Paragraph.objects.filter(user=request.user)
    
    if not user_paragraphs.exists():
        return redirect('upload_paragraph')

    # Randomly pick one for recall
    challenge = random.choice(user_paragraphs)
    return render(request, 'challenge.html', {'para': challenge})