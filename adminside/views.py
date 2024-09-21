from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import Feedback

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




def view_feedback(request):
    feedbacks = Feedback.objects.all().order_by('-submitted_at')[:30]
    return render(request, 'adminapp/feedback.html', {'feedbacks': feedbacks})

def add_store(request):
    return render(request,'adminapp/addstore.html')

def admin_logout(request):
    request.session.flush()  # Clear the session data
    return redirect('adminlogin')  # Redirect to the admin login page