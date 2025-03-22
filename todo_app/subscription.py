from django.core.management.base import BaseCommand
from django.utils.timezone import now
from myapp.models import Profile

class Command(BaseCommand):
    help = "Expire premium subscriptions after one month"

    def handle(self, *args, **kwargs):
        expired_profiles = Profile.objects.filter(is_premium=True, subscription_end__lt=now())
        
        for profile in expired_profiles:
            profile.is_premium = False
            profile.save()
            self.stdout.write(self.style.SUCCESS(f"Expired subscription for: {profile.user.username}"))

        self.stdout.write(self.style.SUCCESS("Subscription check completed."))
from django.core.mail import send_mail

# Send renewal email before expiration
for profile in Profile.objects.filter(is_premium=True, subscription_end__lt=now() + timedelta(days=3)):
    send_mail(
        "Subscription Expiry Reminder",
        "Your premium subscription will expire in 3 days. Renew now to continue enjoying premium features.",
        "support@yourdomain.com",
        [profile.user.email],
        fail_silently=False,
    )
