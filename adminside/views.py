from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import Feedback
from authapp.models import UserProfile
from django.contrib.auth.decorators import login_required

ADMIN_CREDENTIALS = {'admin': 'admin123'}  # Change this to match the username you're checking


def adminlogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if the username exists and the password matches
        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
            # Set session variable
            request.session['admin_logged_in'] = True  # Optional: Track admin login status
            return redirect('view_feedback')  # Redirect to admin dashboard
        else:
            return redirect('adminlogin')  # Redirect back if credentials are incorrect

    return render(request, 'adminapp/alogin.html')

@login_required(login_url='adminlogin')
def view_feedback(request):
    feedbacks = Feedback.objects.all().order_by('-submitted_at')

    names = feedbacks.values_list('name', flat=True).distinct()

    profiles = UserProfile.objects.filter(user__username__in=names).values('user__username', 'avatar')

    avatar_dict = {profile['user__username']: profile['avatar'] for profile in profiles}

    for feedback in feedbacks:
        feedback.avatar = avatar_dict.get(feedback.name, 'default.jpg')  # Use 'default.jpg' if no avatar found
    feedbacks = feedbacks[:30]
    return render(request, 'adminapp/feedback.html', {'feedbacks': feedbacks})



def add_store(request):
    return render(request,'adminapp/addstore.html')

def admin_logout(request):
    request.session.flush()  # Clear the session data
    return redirect('adminlogin')  # Redirect to the admin login page