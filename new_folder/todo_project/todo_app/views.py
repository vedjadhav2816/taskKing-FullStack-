from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse
from django.utils.timezone import now
from django.conf import settings
from .models import Profile, Task, Payment
from django.core.mail import send_mail
from django.utils.timezone import now, timedelta
import razorpay
import random
import string
import json  # Added for JSON parsing in verify_payment

# ✅ Razorpay API Keys (Set in settings.py)
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))


# ✅ Generate Referral Code
def generate_referral_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


# ✅ Home View
def home(request):
    if request.user.is_authenticated:
        # Logged-in users see the dashboard
        profile = Profile.objects.get(user=request.user)
        context = {"is_premium": profile.is_premium}
        return render(request, "dashboard.html", context)
    else:
        # Logged-out users see the base.html homepage
        return render(request, "base.html")
# ✅ About Page View

def about(request):
    return render(request, "about.html")


# ✅ Contact Page View
def contact(request):
    
    if request.method == 'POST':
        # Handle contact form submission (logic can be added later)
        pass
    return render(request, 'contact.html')


def signup(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not all([first_name, last_name, email, username, password]):
            messages.error(request, "All fields are required.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered!")
            return redirect("signup")

        # ✅ Create user with additional fields
        user = User.objects.create_user(
            username=username, password=password, email=email,
            first_name=first_name, last_name=last_name
        )
        login(request, user)

        # ✅ Create Profile for user
        Profile.objects.get_or_create(
            user=user, defaults={"is_premium": False, "referral_code": generate_referral_code(), "theme": "light"}
        )

        messages.success(request, "Signup successful! Welcome to TaskKing.")
        return redirect("dashboard")

    return render(request, "signup.html")

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")  # If already logged in, go to dashboard

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")  # Show login page only if needed


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("home")  # Redirect to base.html after logout




# ✅ Dashboard View

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from datetime import timedelta
from .models import Task, Profile, Payment

@login_required(login_url='/')
def dashboard(request):
    today = now().date()

    # ✅ Remove overdue tasks
    Task.objects.filter(
        user=request.user,
        due_date__lt=today,
        completed=False
    ).delete()

    # ✅ Fetch user tasks
    tasks = Task.objects.filter(user=request.user)
    completed_tasks = tasks.filter(completed=True).count()
    pending_tasks = tasks.filter(completed=False).count()

    # ✅ Check user profile
    profile, created = Profile.objects.get_or_create(user=request.user)

    # ✅ Check if the user's premium subscription has expired
    last_payment = Payment.objects.filter(user=request.user, status=True).order_by('-created_at').first()
    
    if last_payment and last_payment.created_at + timedelta(days=30) >= now():
        profile.is_premium = True
        profile.subscription_end = last_payment.created_at + timedelta(days=30)  # Set expiry date
    else:
        profile.is_premium = False

    profile.save()

    # ✅ Show "Manage Subscription" only for premium users
    show_manage_subscription = profile.is_premium

    context = {
        "tasks": tasks,
        "completed": completed_tasks,
        "pending": pending_tasks,
        "is_premium": profile.is_premium,  # ✅ Pass to template
        "show_manage_subscription": show_manage_subscription,  # ✅ Pass to template
        "subscription_end": profile.subscription_end.strftime('%d %b, %Y') if profile.is_premium else None,  # Format date for UI
        "today": today,
    }

    return render(request, "dashboard.html", context)



@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = True
    task.save()
    messages.success(request, f"Task '{task.title}' marked as completed!")
    return redirect("dashboard")  

# ✅ Add Task View
@login_required
def add_task(request):
    if request.method == "POST":
        title = request.POST.get("title")
        priority = request.POST.get("priority")  # Get priority from form
        due_date = request.POST.get("due_date")

        # Create the task with priority field
        Task.objects.create(user=request.user, title=title, priority=priority, due_date=due_date)

        return redirect("dashboard")

    return render(request, "add_task.html")


# ✅ Complete Task View
@login_required
def complete_task(request, task_id):
    task = Task.objects.get(id=task_id, user=request.user)
    if task and not task.completed:
        task.completed = True
        task.save()

        # Get updated task counts
        total_tasks = Task.objects.filter(user=request.user).count()
        completed_count = Task.objects.filter(user=request.user, completed=True).count()
        pending_count = total_tasks - completed_count

        return JsonResponse({
            "success": True,
            "completed_count": completed_count,
            "pending_count": pending_count,
            "total_tasks": total_tasks
        })
    
    return JsonResponse({"success": False})
# ✅ Delete Task View
@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect("dashboard")


# ✅ Razorpay Payment Page View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Payment
import razorpay

@login_required
def create_payment(request):
    amount = 19900  # ₹499.00 in paise

    # Get or create the user's profile
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Check if the user already has an active subscription
    if profile.is_premium and profile.subscription_end >= now():
        return redirect("dashboard")  # Prevent duplicate payments if already active

    # Check if a pending payment already exists
    payment, created = Payment.objects.get_or_create(
        user=request.user,
        status=False,  # Only consider unpaid transactions
        defaults={
            "transaction_id": "",  # Temporary placeholder, will be updated
            "amount": 199.00,
            "status": False
        }
    )

    # If an unpaid payment exists, reset and reuse it
    if not created:
        payment.transaction_id = ""  # Reset transaction ID
        payment.save()

    # Create a new Razorpay Order
    razorpay_order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1"
    })

    # Update the transaction ID in the database
    payment.transaction_id = razorpay_order["id"]
    payment.save()

    context = {
        "key": settings.RAZORPAY_KEY_ID,  # Razorpay Key for frontend
        "order_id": razorpay_order["id"],  # Order ID for verification
    }

    return render(request, "payment.html", context)




# ✅ Payment Success View (Handles Razorpay Callback)
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from datetime import timedelta
import razorpay

@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        try:
            data = request.POST
            razorpay_payment_id = data.get("razorpay_payment_id")
            razorpay_order_id = data.get("razorpay_order_id")
            razorpay_signature = data.get("razorpay_signature")

            # Verify Razorpay payment signature
            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            }
            razorpay_client.utility.verify_payment_signature(params_dict)

            # Fetch the payment record
            payment = Payment.objects.get(transaction_id=razorpay_order_id)

            # Ensure the payment is not already processed
            if payment.status:
                return JsonResponse({"message": "Payment already processed."})

            # Mark payment as successful
            payment.status = True
            payment.save()

            # Upgrade user to premium
            profile, created = Profile.objects.get_or_create(user=payment.user)
            profile.is_premium = True

            # Extend subscription if already premium
            if profile.subscription_end and profile.subscription_end >= now():
                profile.subscription_end += timedelta(days=30)
            else:
                profile.subscription_end = now() + timedelta(days=30)

            profile.save()

            return JsonResponse({"message": "Payment successful! Premium activated."})

        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"error": "Payment verification failed. Contact support."}, status=400)
        except Payment.DoesNotExist:
            return JsonResponse({"error": "Payment record not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)




# ✅ Verify Payment (AJAX call for frontend)
@csrf_exempt
@login_required
def verify_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            payment_id = data.get("razorpay_payment_id")
            order_id = data.get("razorpay_order_id")
            signature = data.get("razorpay_signature")

            # Verify payment with Razorpay
            params_dict = {
                "razorpay_payment_id": payment_id,
                "razorpay_order_id": order_id,
                "razorpay_signature": signature
            }

            razorpay_client.utility.verify_payment_signature(params_dict)

            # Mark user as premium after successful verification
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.is_premium = True
            profile.save()

            return JsonResponse({"success": True})

        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"success": False, "error": "Invalid payment signature."})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


# ✅ Premium Upgrade View
@login_required
def upgrade_to_premium(request):
    user_profile = request.user.profile
    user_profile.is_premium = True  # Upgrade user
    user_profile.save()
    messages.success(request, "Congratulations! You are now a Premium Member. 🎉")
    return redirect('dashboard') 


@login_required
def view_profile(request):
    return render(request, 'profile.html')



@login_required
def edit_profile(request):
    if not request.user.profile.is_premium:
        return redirect('view_profile')  # Redirect free users to the profile page

    if request.method == "POST":
        request.user.username = request.POST.get("username")
        request.user.email = request.POST.get("email")
        request.user.profile.theme = request.POST.get("theme")
        request.user.save()
        request.user.profile.save()
        return redirect('view_profile')

    return render(request, 'edit_profile.html')

@login_required
def change_theme(request):
    if request.method == 'POST':
        theme = request.POST.get('theme')
        if theme in ['dark', 'light', 'fun']:
            request.user.profile.theme = theme
            request.user.profile.save()
        return redirect('dashboard')  # Adjust to your dashboard URL
    return render(request, 'change_theme.html')

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user.username = username
        user.email = email

        if password:  # If password is entered, update it
            user.set_password(password)
            user.save()

            # Re-authenticate the user after password change
            updated_user = authenticate(username=username, password=password)
            if updated_user:
                login(request, updated_user)

        else:
            user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard')  # Redirect to Dashboard after update ✅

    return render(request, 'edit_profile.html')

@login_required
def advanced_analytics(request):
    # Ensure only premium users can access
    if not request.user.profile.is_premium:  # Fix here
        return redirect('dashboard')

    # Fetch user’s task data
    tasks = Task.objects.filter(user=request.user)
    completed_tasks = tasks.filter(completed=True).count()
    total_tasks = tasks.count()
    pending_tasks = total_tasks - completed_tasks
    overdue_tasks = tasks.filter(due_date__lt=request.user.date_joined, completed=False).count()

    # Priority Breakdown
    high_priority = tasks.filter(priority='high').count()
    medium_priority = tasks.filter(priority='medium').count()
    low_priority = tasks.filter(priority='low').count()

    # Prepare data for charts
    analytics_data = {
        "completed_tasks": completed_tasks,
        "total_tasks": total_tasks,
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue_tasks,
        "high_priority": high_priority,
        "medium_priority": medium_priority,
        "low_priority": low_priority,
    }

    return render(request, 'advanced_analysis.html', {"analytics_data": analytics_data})


def support(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Send email to support (configure settings.py for email)
        send_mail(
            subject=f'TaskKing Support Request from {name}',
            message=f'From: {email}\n\n{message}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['support@taskking.com'],
            fail_silently=False,
        )
        return render(request, 'support.html', {'success': 'Message sent successfully!'})
    return render(request, 'support.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from datetime import timedelta
import razorpay

from .models import Payment, Profile
from django.conf import settings

# Initialize Razorpay client


@login_required
def payment_view(request):
    """Check if the user has already paid, then show the correct payment page."""
    has_paid = False  # Default: user has not paid

    if request.user.is_authenticated:
        # Check if the user is a premium member with an active subscription
        has_paid = Profile.objects.filter(
            user=request.user, is_premium=True, subscription_end__gt=now()
        ).exists()

        if has_paid:
            return redirect("dashboard")  # Redirect premium users to the dashboard

    # Create a new Razorpay Order if payment is needed
    amount = 19900  # ₹499.00 in paise
    razorpay_order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1"
    })

    # Save the order ID in the database for tracking
    Payment.objects.create(
        user=request.user,
        transaction_id=razorpay_order["id"],
        amount=199.00,
        status=False
    )

    return render(request, "payment.html", {
        "key": settings.RAZORPAY_KEY_ID,
        "order_id": razorpay_order["id"],  # Pass the actual generated order ID
        "has_paid": has_paid  # Pass the correct value to template
    })


@csrf_exempt
def payment_success(request):
    """Handles Razorpay payment verification and upgrades user."""
    if request.method == "POST":
        try:
            data = request.POST
            razorpay_payment_id = data.get("razorpay_payment_id")
            razorpay_order_id = data.get("razorpay_order_id")
            razorpay_signature = data.get("razorpay_signature")

            # Verify Razorpay payment
            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            }
            razorpay_client.utility.verify_payment_signature(params_dict)

            # Update payment status
            payment = Payment.objects.get(transaction_id=razorpay_order_id)
            payment.status = True
            payment.save()

            # Upgrade user to premium for 1 month
            profile, created = Profile.objects.get_or_create(user=payment.user)
            profile.is_premium = True
            profile.subscription_end = now() + timedelta(days=30)  # Set expiry after 30 days
            profile.save()

            return JsonResponse({"message": "Payment successful!"})

        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"error": "Payment verification failed. Contact support."}, status=400)
        except Payment.DoesNotExist:
            return JsonResponse({"error": "Payment record not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def manage_subscription(request):
    profile = Profile.objects.get(user=request.user)

    # Get the last successful payment
    last_payment = Payment.objects.filter(user=request.user, status=True).order_by('-created_at').first()

    # Determine subscription validity
    if profile.is_premium and profile.subscription_end and profile.subscription_end >= now():
        subscription_end = profile.subscription_end
        show_manage_subscription = True  # Show "Manage Subscription"
    else:
        subscription_end = None
        show_manage_subscription = False  # Hide "Manage Subscription" if expired

    context = {
        "is_premium": profile.is_premium,
        "subscription_end": subscription_end.strftime('%d %B %Y') if subscription_end else None,
        "show_manage_subscription": show_manage_subscription,
    }

    return render(request, "manage_subscription.html", context)


import google.generativeai as genai
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import os

# Load API key from environment (secure)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

@login_required
def suggest_tasks(request):
    task_list = []
    error = None

    if request.method == "POST":
        user_input = request.POST.get("goal", "").strip()

        if not user_input:
            error = "⚠️ Please enter a valid goal."
        else:
            try:
                model = genai.GenerativeModel("gemini-1.5-pro")  
                response = model.generate_content(
                    f"Suggest 12 tasks related to {user_input} in a clean numbered list. "
                    "Only provide the tasks, no explanations, no extra formatting, no *** symbols."
                )

                # Ensure response is clean and properly formatted
                suggested_tasks = response.text.strip()
                task_list = [task.strip() for task in suggested_tasks.split("\n") if task.strip().isdigit() is False]

            except Exception as e:
                error = f"⚠️ AI Error: {str(e)}"

    return render(request, "suggest_tasks.html", {"task_list": task_list, "error": error})
