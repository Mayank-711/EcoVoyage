from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import Feedback
from authapp.models import UserProfile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import StoreForm
from .models import Store
from django.shortcuts import get_object_or_404

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

from django.shortcuts import redirect

def view_feedback(request):
    # Check if the admin is logged in via the session
    if not request.session.get('admin_logged_in'):
        return redirect('adminlogin')  # Redirect to the admin login page if not logged in

    # If the admin is logged in, proceed with fetching feedback
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

def add_store(request):
    if request.method == 'POST':
        form = StoreForm(request.POST, request.FILES)
        if form.is_valid():
            store = form.save()
            messages.success(request, f'Store "{store.store_name}" added successfully with ID {store.store_id}.')
            return redirect('addstore')  # Redirect to the add store page after successful submission
    else:
        form = StoreForm()

    return render(request, 'adminapp/addstore.html', {'form': form})

def manage_stores(request):
    stores = Store.objects.all()
    return render(request, 'adminapp/manage_stores.html', {'stores': stores})

def edit_store(request, store_id):
    # Fetch the store using store_id
    store = get_object_or_404(Store, store_id=store_id)

    if request.method == 'POST':
        # Update store information from the form data
        store.store_name = request.POST.get('store_name')
        store.location = request.POST.get('location')
        store.description = request.POST.get('description')
        if request.FILES.get('logo'):
            store.logo = request.FILES.get('logo')
        store.save()
        return redirect('manage_stores')  # Redirect after saving

    return render(request, 'adminapp/edit_store.html', {'store': store})

def delete_store(request, store_id):
    # Fetch the store using store_id
    store = get_object_or_404(Store, store_id=store_id)

    if request.method == 'POST':
        store.delete()  # Delete the store instance
        return redirect('manage_stores')  # Redirect to manage stores page

    return render(request, 'adminapp/delete_store.html', {'store': store})