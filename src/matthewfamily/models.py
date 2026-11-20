from django.db import models

class WeeklyService(models.Model):
    DAY_CHOICES = [
        ('WEDNESDAY', 'Wednesday SCC Fellowship'),
        ('THURSDAY', 'Thursday Eucharistic Adoration'),
    ]
    service_day = models.CharField(max_length=20, choices=DAY_CHOICES, unique=True)
    venue = models.CharField(max_length=200)
    time_range = models.CharField(max_length=100)
    animator = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_service_day_display()} - {self.venue}"


class CommunityMember(models.Model):
    STATUS_CHOICES = [('Paid', 'Paid'), ('Pending', 'Pending')]

    full_name = models.CharField(max_length=120)
    year_and_course = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)
    semestral_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    animation_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    attendance_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.full_name