from django.conf import settings
from django.db import models


class RndProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rnd_profile"
    )
    prc_license_number = models.CharField(max_length=50, unique=True)
    prc_expiry_date = models.DateField(null=True, blank=True)
    specialization = models.CharField(max_length=255, null=True, blank=True)
    language_codes = models.JSONField(null=True, blank=True, help_text="Array of language codes")
    bio = models.TextField(null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    available_for_new_clients = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rnd_profiles"

    def __str__(self):
        return f"RND Profile: {self.user.full_name}"


class RndLanguage(models.Model):
    rnd = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="languages"
    )
    language_code = models.CharField(max_length=10)
    language_name = models.CharField(max_length=50)

    class Meta:
        db_table = "rnd_languages"

    def __str__(self):
        return f"{self.rnd.full_name} — {self.language_name}"


class RndAvailabilitySchedule(models.Model):
    class DayOfWeek(models.IntegerChoices):
        SUNDAY = 0, "Sunday"
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"

    rnd = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="availability_schedules"
    )
    day_of_week = models.SmallIntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rnd_availability_schedules"

    def __str__(self):
        return f"{self.rnd.full_name} — {self.get_day_of_week_display()}"


class ClientProfile(models.Model):
    class Sex(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_profile"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, choices=Sex.choices, null=True, blank=True)
    language_code = models.CharField(max_length=10, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    emergency_contact = models.CharField(max_length=255, null=True, blank=True)
    emergency_phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "client_profiles"

    def __str__(self):
        return f"Client Profile: {self.user.full_name}"


class ClientHealthProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="health_profile"
    )
    medical_conditions = models.JSONField(null=True, blank=True)
    allergies = models.JSONField(null=True, blank=True)
    dietary_restrictions = models.JSONField(null=True, blank=True)
    health_goals = models.JSONField(null=True, blank=True)
    religion = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "client_health_profiles"

    def __str__(self):
        return f"Health Profile: {self.user.full_name}"
