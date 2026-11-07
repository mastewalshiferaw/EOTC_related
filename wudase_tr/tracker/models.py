from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Paragraph(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='wudase_paragraphs/')
    day_name = models.CharField(max_length=20) # e.g., "Monday"
    order_index = models.IntegerField() # 1, 2, 3...
    is_mastered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_reviewed = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.day_name} - Part {self.order_index}"

class DailyReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Not auto_now_add: that stores the *server's* local date while views query
    # with timezone.localdate(), so the two disagree whenever the box's timezone
    # differs from TIME_ZONE and get_or_create inserts a fresh row every review.
    date = models.DateField(default=timezone.localdate)
    paragraphs_reviewed = models.ManyToManyField(Paragraph)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'date'], name='unique_daily_review_per_user'
            )
        ]

class ReviewLog(models.Model):
    # 1=Forgot, 2=Hard, 3=Easy
    FORGOT = 1
    HARD = 2
    EASY = 3

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    paragraph = models.ForeignKey(Paragraph, on_delete=models.CASCADE)
    reviewed_at = models.DateField(default=timezone.localdate)
    rating = models.IntegerField(default=FORGOT)

    def __str__(self):
        return f"{self.user.username} reviewed {self.paragraph.day_name} on {self.reviewed_at}"