from django.db import models
from django.contrib.auth.models import User

class Paragraph(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='wudase_paragraphs/')
    day_name = models.CharField(max_length=20) # e.g., "Monday"
    order_index = models.IntegerField() # 1, 2, 3...
    is_mastered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.day_name} - Part {self.order_index}"

class DailyReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    paragraphs_reviewed = models.ManyToManyField(Paragraph)