from django.db import models

class AttendanceLog(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Completed', 'Completed'),
    )

    identifier = models.CharField(max_length=100)
    student_name = models.CharField(max_length=150, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    timestamp_in = models.DateTimeField(auto_now_add=True)
    timestamp_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    def __str__(self):
        return f"{self.identifier} - {self.status}"

class LibrarySystemState(models.Model):
    is_open = models.BooleanField(default=False)

    def __str__(self):
        return "Open" if self.is_open else "Closed"

    @classmethod
    def get_state(cls):
        state, created = cls.objects.get_or_create(id=1)
        return state
