from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Paragraph, DailyReview
from .forms import ParagraphForm
from django.contrib import messages
from datetime import date, timedelta
import random

def dashboard(request):
    # Streak Logic: Count how many consecutive days in a row the user has reviewed
    # Get all unique dates the user reviewed anything
    reviewed_dates = DailyReview.objects.filter(user=request.user).values_list('date', flat=True).order_by('-date')
    
    streak = 0
    current_date = date.today()
    
    # Check today, then yesterday, then the day before...
    while current_date in reviewed_dates:
        streak += 1
        current_date -= timedelta(days=1)
        
    paragraphs = Paragraph.objects.filter(user=request.user)
    return render(request, 'tracker/dashboard.html', {
        'paragraphs': paragraphs,
        'streak': streak
    })

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
    if request.method == 'POST':
        para_id = request.POST.get('para_id')
        para = get_object_or_404(Paragraph, id=para_id)
        
        # 1. Update paragraph's last_reviewed date
        para.last_reviewed = timezone.now().date()
        para.save()
        
        # 2. Log in DailyReview model
        today = timezone.now().date()
        daily_log, created = DailyReview.objects.get_or_create(user=request.user, date=today)
        daily_log.paragraphs_reviewed.add(para)
        
        messages.success(request, "Recorded! Keep going.")
        return redirect('daily_recall')

    # Get paragraphs NOT reviewed today
    today = timezone.now().date()
    to_review = Paragraph.objects.filter(user=request.user).exclude(last_reviewed=today)
    
    if not to_review.exists():
        return render(request, 'tracker/finished.html')

    # Pick the oldest reviewed one (or random if you prefer)
    challenge = to_review.order_by('last_reviewed').first()
    
    return render(request, 'tracker/recall.html', {'para': challenge})