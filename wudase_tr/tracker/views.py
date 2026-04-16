from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Paragraph, DailyReview
from .forms import ParagraphForm
import random

def dashboard(request):
    # Calculate streak (simple version)
    streak = DailyReview.objects.filter(user=request.user).count()
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
        
        # 1. Mark paragraph as reviewed
        para.last_reviewed = timezone.now().date()
        para.save()
        
        # 2. Log in DailyReview model
        today = timezone.now().date()
        daily_log, created = DailyReview.objects.get_or_create(user=request.user, date=today)
        daily_log.paragraphs_reviewed.add(para)
        
        return redirect('daily_recall')

    # Get paragraphs NOT reviewed today
    to_review = Paragraph.objects.filter(user=request.user).exclude(
        last_reviewed=timezone.now().date()
    ).order_by('last_reviewed')

    if not to_review.exists():
        return render(request, 'tracker/finished.html')

    challenge = to_review.first()
    return render(request, 'tracker/recall.html', {'para': challenge})