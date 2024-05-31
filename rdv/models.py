from django.contrib.auth.models import AbstractUser
from django.db import models


class Disponibility(models.Model):
    WEEKDAYS_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    day = models.CharField(max_length=10, choices=WEEKDAYS_CHOICES)
    start_hour = models.CharField(null=True, blank=True)
    start_minute = models.CharField(null=True, blank=True)
    end_hour = models.CharField(null=True, blank=True)
    end_minute = models.CharField(null=True, blank=True)
    is_allday = models.BooleanField(default=False)

    def __str__(self):
        if self.is_allday:
            return f"{self.get_day_display()} - All day"
        else:
           return f"{self.get_day_display()} - {self.start_hour}:{self.start_minute} to {self.end_hour}:{self.end_minute}"

class City(models.Model):
    designation = models.CharField(max_length=100)

    def __str__(self):
        return self.designation

class Specialty(models.Model):
    designation = models.CharField(max_length=100)

    def __str__(self):
        return self.designation

class CUser(AbstractUser):
    USER_TYPES = [
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
        ('patient', 'Patient'),
    ]

    name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    active = models.BooleanField(default=True)

    class Meta:
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):
        return self.email

class Doctor(models.Model):
    user = models.OneToOneField(CUser, on_delete=models.CASCADE, related_name='doctor')
    address = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, default=1)
    disponibilities = models.ManyToManyField(Disponibility, blank=True)
    is_allweek = models.BooleanField(default=False)
    is_all_weeknoweekend = models.BooleanField(default=False)

    def liked_by(self):
        return self.like_set.all()

    def booked(self):
        return self.rdv_set.all()

    def __str__(self):
        return self.user.username

class Admin(models.Model):
    user = models.OneToOneField(CUser, on_delete=models.CASCADE, related_name='admin')
    # Add admin-specific fields here

    def __str__(self):
        return self.user.username

class Patient(models.Model):
    user = models.OneToOneField(CUser, on_delete=models.CASCADE, related_name='patient')

    def likes(self):
        return self.like_set.all()

    def __str__(self):
        return self.user.username

class Like(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)

    def __str__(self):
        return self.patient.user.username + ' likes ' + self.doctor.user.username

class Rdv(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    
    time = models.DateTimeField()
    state = models.CharField(max_length=10, choices=STATUS_CHOICES)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)

    def __str__(self):
        return self.patient.user.username + ' & ' + self.doctor.user.username + ' at ' + str(self.time) + '(' + self.state + ')'
