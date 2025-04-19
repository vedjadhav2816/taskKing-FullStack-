from django.urls import path
from . import views  # ✅ Importing views correctly

urlpatterns = [
    # General pages
    path("", views.home, name="home"),  # Show base.html # Logout user
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Authentication
    path('signup/', views.signup, name='signup'),
    path("login/", views.login_view, name="login"),  # Show login page
    path("logout/", views.logout_view, name="logout"),   # ✅ Corrected `logout_view`
    
    # Dashboard and Task Management
    path('dashboard/', views.dashboard, name='dashboard'),  # Dashboard view
    path('add-task/', views.add_task, name='add_task'),  # Add new task
    path('complete-task/<int:task_id>/', views.complete_task, name='complete_task'), # Complete task
    path("task/delete/<int:task_id>/", views.delete_task, name="delete_task"),  # Delete task (matches your original)
    
    # Payment and Premium Upgrade
    path('pay/', views.create_payment, name='create_payment'),  # Initiate payment
    path('payment-success/', views.payment_success, name='payment_success'),  # Payment success callback
    path("verify_payment/", views.verify_payment, name="verify_payment"),  # Verify payment
    path('upgrade/', views.upgrade_to_premium, name='payment'),  # Updated to match dashboard.html's 'payment' URL

    path('profile/', views.view_profile, name="view_profile"),
    path('profile/edit/', views.edit_profile, name="edit_profile"),
    path('profile/theme/', views.change_theme, name="change_theme"),
    path('update-profile/', views.update_profile, name='update_profile'),

    path('advanced-analytics/', views.advanced_analytics, name='advanced_analytics'),

       path('support/', views.support, name='support'),
       path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
        path('manage-subscription/', views.manage_subscription, name='manage_subscription'),

        path("suggest-tasks/", views.suggest_tasks, name="suggest_tasks"),
]