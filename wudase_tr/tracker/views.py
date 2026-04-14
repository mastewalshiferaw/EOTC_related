from django.shortcuts import render, redirect
from .models import Paragraph
from .forms import ParagraphForm
import random

def dashboard(request):
    # This shows your progress
    paragraphs = Paragraph.objects.filter(user=request.user)
    return render(request, 'tracker/dashboard.html', {'paragraphs': paragraphs})

def upload_view(request):
    if request.method == 'POST':
        form = ParagraphForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save(commit=False)
            p.user = request.user
            p.save()
            return redirect('dashboard')
    else:
        form = ParagraphForm()
    return render(request, 'tracker/upload.html', {'form': form})

def daily_recall(request):
    # Randomly get one paragraph to revise
    paragraphs = Paragraph.objects.filter(user=request.user)
    if not paragraphs.exists():
        return redirect('upload_view')
    
    challenge = random.choice(paragraphs)
    return render(request, 'tracker/recall.html', {'para': challenge})

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