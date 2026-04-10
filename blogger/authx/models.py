from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    country_code = models.CharField(max_length=5, blank=True, null=True)
    mobile_number = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[1-9]\d*$',
                message='Mobile number must not start with 0 and must contain only digits.'
            )
        ]
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(mobile_number__regex=r'^[1-9]\d*$'),
                name='mobile_number_valid_format_and_no_leading_zero'
            )
        ]

    def __str__(self):
        return f"{self.user.username}'s Profile"
