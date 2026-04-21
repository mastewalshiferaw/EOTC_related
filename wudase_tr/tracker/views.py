from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .models import Paragraph, DailyReview, ReviewLog # Ensure you have ReviewLog if you use it
from .forms import ParagraphForm

@login_required
def dashboard(request):
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

@login_required
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

@login_required
def daily_recall(request):
    today = timezone.now().date()
    
    if request.method == 'POST':
        para_id = request.POST.get('para_id')
        para = get_object_or_404(Paragraph, id=para_id, user=request.user)
        
        # 1. Update paragraph's last_reviewed date
        para.last_reviewed = today
        para.save()
        
        # 2. Log in DailyReview model
        daily_log, created = DailyReview.objects.get_or_create(user=request.user, date=today)
        daily_log.paragraphs_reviewed.add(para)
        
        messages.success(request, "Recorded! Keep going.")
        return redirect('daily_recall')

    # Get paragraphs NOT reviewed today
    to_review = Paragraph.objects.filter(user=request.user).exclude(last_reviewed=today)
    
    if not to_review.exists():
        return render(request, 'tracker/finished.html')

    # Get the count for your progress bar logic
    total_paragraphs = Paragraph.objects.filter(user=request.user).count()
    remaining_count = to_review.count()

    # Sort by last_reviewed so the oldest ones come first
    challenge = to_review.order_by('last_reviewed').first()
    
    return render(request, 'tracker/recall.html', {
        'para': challenge,
        'remaining': remaining_count,
        'total': total_paragraphs
    })