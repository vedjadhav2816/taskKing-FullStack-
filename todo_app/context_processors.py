from .models import Profile  # Import your Profile model

def user_premium_status(request):
    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()  # Fetch profile
        return {'is_premium': profile.is_premium if profile else False}
    return {'is_premium': False}
