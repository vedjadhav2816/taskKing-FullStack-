from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_premium = models.BooleanField(default=False)  # Tracks payment status
    referral_code = models.CharField(max_length=10, blank=True, null=True)
    theme = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')
    subscription_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=[("Pending", "Pending"), ("Success", "Success"), ("Failed", "Failed")], 
        default="Pending"  # Add default value here
    )

    def __str__(self):
        return self.user.username


    def check_subscription_status(self):
        """Check if subscription is expired and update is_premium status."""
        if self.subscription_end and now() > self.subscription_end:
            self.is_premium = False
            self.save()


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")  # ✅ Added related_name for reverse lookup
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)  # ✅ Added index for faster queries
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.BooleanField(default=False)  # ✅ True = Paid, False = Pending
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ Fixes missing column issue
    updated_at = models.DateTimeField(auto_now=True)  # ✅ Added for tracking changes

    class Meta:
        ordering = ["-created_at"]  # ✅ Newest payments first
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.user.username} - ₹{self.amount}"


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    def __str__(self):
        return f"{self.title} - {self.priority}"
 # <-- Check if this line exists
