from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from .forms import UserForm, UserProfileForm
import re
import uuid
from .utils import send_email_to_client
from .models import Friendship
def landingpage(request):
    return render(request, 'authapp/home.html')

def loginpage(request):
    try:    
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            if not User.objects.filter(username=username).exists():
                messages.error(request, 'Invalid Username')
                return redirect("login")

            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("mappage")
            else:
                messages.error(request, "Invalid Credentials")
                return redirect("login")
    except Exception as e:
        print(e)
    return render(request, 'authapp/login.html')

def signuppage(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            try:
                if User.objects.filter(username=username).exists():
                    messages.info(request, "User with the same username already exists.")
                    return redirect("signup")
                user = User.objects.filter(email=email)
                if user.exists():
                    messages.info(request, "Email already exists.")
                    return redirect("signup")
                if len(password) < 8:
                    messages.error(request, "Password must be at least 8 characters long.")
                    return redirect("signup")
                if not re.search(r'[A-Za-z]', password):
                    messages.error(request, "Password must contain at least one letter.")
                    return redirect("signup")
                if not re.search(r'[0-9]', password):
                    messages.error(request, "Password must contain at least one number.")
                    return redirect("signup")
                else:
                    my_user = User.objects.create_user(username, email, password)
                    my_user.save()
                    messages.info(request, "Account created successfully. Please login to continue.")
                return redirect('login')
            except Exception as e:
                print(e)  
    except Exception as e:
        print(e)
    return render(request, 'authapp/signup.html')


def user_logout(request):
    logout(request)
    return redirect('login')

def ForgotPassword(request):
    try:
        if request.method == "POST":
            username = request.POST.get("username")
            user_obj = User.objects.filter(username=username).first()
            if not user_obj:
                messages.error(request, "No Username Found with this Username")
                return redirect("forgotpassword")

            # Generate a token and update the user's profile
            token = str(uuid.uuid4())
            profile_obj, created = UserProfile.objects.get_or_create(user=user_obj)
            profile_obj.forgot_password_token = token
            profile_obj.save()

            # Send email to user
            send_email_to_client(user_obj.email, token)
            messages.success(request, "Email has been sent")
            return redirect("forgotpassword")
    except Exception as e:
        print(e)
        messages.error(request, "An error occurred. Please try again.")
    return render(request, "authapp/forgotpassword.html")


def ChangePassword(request, token):
    context = {}
    try:
        profile_obj = UserProfile.objects.filter(forgot_password_token=token).first()
        if not profile_obj:
            messages.error(request, "Invalid or expired token.")
            return redirect("forgotpassword")

        if request.method == "POST":
            new_password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")
            
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect(f"/ChangePassword/{token}/")

            if len(new_password) < 8:
                messages.error(request, "Password should be at least 8 characters long.")
                return redirect(f"/ChangePassword/{token}/")
            
            user_obj = profile_obj.user
            user_obj.set_password(new_password)
            user_obj.save()
            messages.success(request, "Password changed successfully. Please log in with your new password.")
            return redirect("login")

    except Exception as e:
        print(e)
        messages.error(request, "An error occurred. Please try again.")
    
    return render(request, "authapp/changepassword.html", context)


@login_required(login_url='login')
def view_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Fetch received friend requests
    received_requests = Friendship.objects.filter(to_user=request.user, accepted=False)
    
    # Fetch friends of the logged-in user
    friends_from_user = Friendship.objects.filter(from_user=request.user, accepted=True).values_list('to_user', flat=True)
    friends_to_user = Friendship.objects.filter(to_user=request.user, accepted=True).values_list('from_user', flat=True)
    
    # Combine both lists to get all friends
    friends_ids = set(friends_from_user) | set(friends_to_user)
    
    # Fetch friend profiles
    friends = User.objects.filter(id__in=friends_ids).select_related('userprofile')
    
    context = {
        'user': user,
        'profile': profile,
        'received_requests': received_requests,
        'friends': friends,
    }
    
    return render(request, 'authapp/view_profile.html', context)

@login_required(login_url='login')
def edit_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('view_profile', user_id=user.id)
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'authapp/edit_profile.html', context)

@login_required(login_url='login')
def avatar_selection(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        avatar_id = request.POST.get('avatar')
        if avatar_id:
            profile.avatar = avatar_id
            profile.save()
            return redirect('view_profile', user_id=request.user.id)
    
    return render(request, 'authapp/avatar_selection.html', {'profile': profile})


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

@login_required(login_url='login')
@csrf_protect
def update_avatar(request):
    if request.method == 'POST':
        avatar_id = request.POST.get('avatar')

        if avatar_id:
            try:
                # Get the UserProfile associated with the current user
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                profile.avatar = avatar_id  # Update the avatar field
                profile.save()
                return JsonResponse({'success': True, 'message': 'Avatar updated successfully.'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
        else:
            return JsonResponse({'success': False, 'message': 'No avatar ID provided.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required(login_url='login')
def add_friend(request, user_id):
    user_to_add = get_object_or_404(User, id=user_id)
    if user_to_add == request.user:
        messages.error(request, "You cannot send a friend request to yourself.")
        return redirect('friends_list')
    
    friendship, created = Friendship.objects.get_or_create(from_user=request.user, to_user=user_to_add)
    if created:
        messages.success(request, f'Friend request sent to {user_to_add.username}.')
    else:
        messages.info(request, f'You have already sent a friend request to {user_to_add.username}.')
    
    return redirect('friends_list')

@login_required(login_url='login')
def accept_request(request, request_id):
    friendship = get_object_or_404(Friendship, id=request_id)
    if friendship.to_user == request.user:
        friendship.accepted = True
        friendship.save()
        messages.success(request, f'You are now friends with {friendship.from_user.username}.')
    else:
        messages.error(request, 'You are not authorized to accept this friend request.')
    return redirect('view_profile', user_id=request.user.id)

@login_required(login_url='login')
def decline_request(request, request_id):
    friendship = get_object_or_404(Friendship, id=request_id)
    if friendship.to_user == request.user:
        friendship.delete()
        messages.success(request, f'You have declined the friend request from {friendship.from_user.username}.')
    else:
        messages.error(request, 'You are not authorized to decline this friend request.')
    return redirect('view_profile', user_id=request.user.id)


@login_required(login_url='login')
def friends_list(request):
    # Exclude the current user
    users = User.objects.exclude(id=request.user.id)
    
    # Get users who have a sent friend request
    sent_requests = Friendship.objects.filter(from_user=request.user).values_list('to_user', flat=True)
    
    # Get the list of friends (both directions)
    friends_from_user = Friendship.objects.filter(from_user=request.user, accepted=True).values_list('to_user', flat=True)
    friends_to_user = Friendship.objects.filter(to_user=request.user, accepted=True).values_list('from_user', flat=True)
    
    # Combine both lists to get all friends
    friends = set(friends_from_user) | set(friends_to_user)
    
    # Exclude friends from the user list
    users = users.exclude(id__in=friends)
    
    return render(request, 'authapp/friends_list.html', {
        'users': users,
        'sent_requests': sent_requests
    })

@login_required(login_url='login')
def search_users(request):
    query = request.GET.get('q')
    if query:
        users = User.objects.filter(username__icontains=query)
    else:
        users = User.objects.none()
    
    context = {
        'users': users,
        'query': query,
    }
    return render(request, 'authapp/search_results.html', context)