from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .models import Paragraph, DailyReview, ReviewLog
from .forms import ParagraphForm

@login_required
def dashboard(request):
    reviewed_dates = DailyReview.objects.filter(user=request.user).values_list('date', flat=True).order_by('-date')
    
    streak = 0
    check_date = date.today()
    # Check if we should count today or start from yesterday if not reviewed yet
    if check_date not in reviewed_dates:
        check_date -= timedelta(days=1)
        
    while check_date in reviewed_dates:
        streak += 1
        check_date -= timedelta(days=1)
        
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
        rating = request.POST.get('rating', '1') # Default to 1 if missing
        para = get_object_or_404(Paragraph, id=para_id, user=request.user)
        
        # 1. Log the difficulty rating
        ReviewLog.objects.create(user=request.user, paragraph=para, rating=rating)
        
        # 2. Update paragraph
        para.last_reviewed = today
        para.save()
        
        # 3. Log in DailyReview
        daily_log, created = DailyReview.objects.get_or_create(user=request.user, date=today)
        daily_log.paragraphs_reviewed.add(para)
        
        return redirect('daily_recall')

    to_review = Paragraph.objects.filter(user=request.user).exclude(last_reviewed=today)
    
    if not to_review.exists():
        return render(request, 'tracker/finished.html')

    total_paragraphs = Paragraph.objects.filter(user=request.user).count()
    remaining = to_review.count()
    challenge = to_review.order_by('last_reviewed').first()
    
    return render(request, 'tracker/recall.html', {
        'para': challenge,
        'remaining': remaining,
        'total': total_paragraphs
    })