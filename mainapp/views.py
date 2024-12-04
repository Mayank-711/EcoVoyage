from datetime import date, datetime,timedelta
import logging
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import TravelLog,Chat
from django.utils.dateparse import parse_duration
import requests
from django.contrib.auth.decorators import login_required
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from django.db.models import Sum,F
from django.utils.safestring import mark_safe
from authapp.models import UserProfile,Friendship,User
import google.generativeai as genai
import os
from django.http import JsonResponse
from django.conf import settings
from adminside.forms import FeedbackForm
from adminside.models import Feedback
from django.utils import timezone
from datetime import datetime
from django.utils.timezone import now
from adminside.models import Store

logger = logging.getLogger(__name__)

API_KEY_GEMINI =settings.GEMINI
OLAMAPS_API = settings.OLAMAPS



@csrf_exempt
@login_required(login_url='/login/')
def process_form(request):
    if request.method == 'POST':
        user = request.user
        search_date = date.today()
        search_time = datetime.now().strftime('%H:%M:%S')

        source_lat = request.POST.get('source_lat')
        source_lng = request.POST.get('source_lng')
        dest_lat = request.POST.get('dest_lat')
        dest_lng = request.POST.get('dest_lng')
        source_add = request.POST.get('source-add')
        dest_add = request.POST.get('destination-add')

        if source_lat and source_lng and dest_lat and dest_lng:
            try:
                params = {
                    'origin': f'{source_lat},{source_lng}',
                    'destination': f'{dest_lat},{dest_lng}',
                    'mode': 'driving',
                    'alternatives': 'false',
                    'steps': 'true',
                    'overview': 'full',
                    'language': 'en',
                    'traffic_metadata': 'true',
                    'api_key': OLAMAPS_API
                }
                response = requests.post('https://api.olamaps.io/routing/v1/directions', params=params)

                if response.status_code == 200:
                    data = response.json()
                    legs = data['routes'][0]['legs']
                    total_distance = sum(leg['distance'] for leg in legs) / 1000  # Convert to km
                    total_duration = sum(leg['duration'] for leg in legs) / 60  # Convert to minutes
                    total_distance = round(total_distance, 2)
                    total_duration = round(total_duration, 2)
                    list_of_transport = {
                        "Bus": 50,
                        "E-bus": 15,
                        "Train (if Applicable)": 41,
                        "E-Train(if Applicable)": 14,
                        "Car": 128,
                        "E-car": 66.67,
                        "Metro(if Applicable)": 5,
                        "Bicycle": 0,
                        "Walk": 0,
                        "Bike": 74,
                        "Ebike": 22,
                        "Rickshaw": 51.67,
                        "Erickshaw": 24.33,
                        "Scooter": 55,
                        "E-scooter": 22
                    }

                    # Calculate carbon footprint and round to 2 decimal places
                    carbon_footprint_perkm = {mode: round(value * total_distance, 2) for mode, value in list_of_transport.items()}
                    
                    # Save the trip data to the database
                    Chat.objects.create(
                        user=user,
                        source_lat=source_lat,
                        source_lng=source_lng,
                        dest_lat=dest_lat,
                        dest_lng=dest_lng,
                        source_address=source_add,
                        destination_address=dest_add,
                        search_date=search_date,
                        search_time=search_time,
                        distance=total_distance,
                        duration=total_duration,
                        carbon_footprint=carbon_footprint_perkm
                    )
            except Exception as e:
                # Log the exception (optional)
                print(f"Error occurred: {e}")
            
        # After success or failure, always redirect to 'mappage'
        return redirect('mappage')

@login_required(login_url='/login/')
def mappage(request):
    user = request.user
    # Fetch the latest 5 chats
    chats = Chat.objects.filter(user=user).order_by('-search_date', '-search_time')[:5]

    today = datetime.now().date()

    # Adjust week start and end dates for a week starting on Sunday and ending on Saturday
    start_of_week = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
    end_of_week = start_of_week + timedelta(days=6)

    # Query to get the total distance and carbon footprint for each mode of transport this week
    data = TravelLog.objects.filter(user=user, date__range=[start_of_week, end_of_week]) \
        .values('mode_of_transport') \
        .annotate(total_distance=Sum('distance'), total_carbon_footprint=Sum('carbon_footprint'))

    # Check if there is any data
    if not data:
        message = "No data available for this week. Please log your trips to see graphs."
        return render(request, 'mainapp/mappage.html', {'chats': chats, 'message': message})

    # Calculate the overall total distance and total carbon footprint
    total_distance = sum(item['total_distance'] for item in data)
    total_carbon_footprint = sum(item['total_carbon_footprint'] for item in data)

    # Round the total values to two decimal places
    total_distance = round(total_distance, 2)
    total_carbon_footprint = round(total_carbon_footprint, 2)

    # Prepare data for pie charts
    modes_of_transport = [item['mode_of_transport'] for item in data]
    total_distances = [round(item['total_distance'], 2) for item in data]
    total_carbon_footprints = [round(item['total_carbon_footprint'], 2) for item in data]

    # Set colors for each mode of transport to ensure consistency between the two charts
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5'
    ]

    # Create the distance pie chart
    distance_pie = go.Figure(data=[go.Pie(
        labels=modes_of_transport,
        values=total_distances,
        marker=dict(colors=colors),
        textinfo='label+percent',  # Show labels and percentages
        showlegend=True
    )])
    distance_pie.update_layout(
        title={
            'text': "Distance (km)",
            'x': 0.5,
            'xanchor': 'center',
            'y': 1.0,
            'yanchor': 'top',
            'font': {
                'size': 16,
                'color': '#00563B'
            }
        },
        margin=dict(t=40, b=0, l=0, r=0),
        height=400,
        width=400
    )

    # Create the carbon footprint pie chart
    carbon_footprint_pie = go.Figure(data=[go.Pie(
        labels=modes_of_transport,
        values=total_carbon_footprints,
        marker=dict(colors=colors),
        textinfo='label+percent',  # Show labels and percentages
        showlegend=True
    )])
    carbon_footprint_pie.update_layout(
        title={
            'text': "Carbon Footprint (kg CO2)",
            'x': 0.5,
            'xanchor': 'center',
            'y': 1.0,
            'yanchor': 'top',
            'font': {
                'size': 16,
                'color': '#00563B'
            }
        },
        margin=dict(t=40, b=0, l=0, r=0),
        height=400,
        width=400
    )

    # Create the bar chart for average carbon footprint per meter
    start_of_last_week = start_of_week - timedelta(weeks=1)
    end_of_last_week = start_of_last_week + timedelta(days=6)

    start_of_week_before_last = start_of_last_week - timedelta(weeks=1)
    end_of_week_before_last = start_of_week_before_last + timedelta(days=6)

    this_week_data = TravelLog.objects.filter(user=user, date__range=[start_of_week, end_of_week]) \
        .values('mode_of_transport') \
        .annotate(total_distance=Sum('distance'), total_carbon_footprint=Sum('carbon_footprint'))

    last_week_data = TravelLog.objects.filter(user=user, date__range=[start_of_last_week, end_of_last_week]) \
        .values('mode_of_transport') \
        .annotate(total_distance=Sum('distance'), total_carbon_footprint=Sum('carbon_footprint'))

    week_before_last_data = TravelLog.objects.filter(user=user, date__range=[start_of_week_before_last, end_of_week_before_last]) \
        .values('mode_of_transport') \
        .annotate(total_distance=Sum('distance'), total_carbon_footprint=Sum('carbon_footprint'))

    def calculate_totals(data):
        total_distance = sum(item['total_distance'] for item in data)
        total_carbon_footprint = sum(item['total_carbon_footprint'] for item in data)
        return total_distance, total_carbon_footprint

    try:
        this_week_total_distance, this_week_total_carbon_footprint = calculate_totals(this_week_data)
        last_week_total_distance, last_week_total_carbon_footprint = calculate_totals(last_week_data)
        week_before_last_total_distance, week_before_last_total_carbon_footprint = calculate_totals(week_before_last_data)

        # Round the totals to two decimal places
        this_week_total_distance = round(this_week_total_distance, 2)
        this_week_total_carbon_footprint = round(this_week_total_carbon_footprint, 2)
        last_week_total_distance = round(last_week_total_distance, 2)
        last_week_total_carbon_footprint = round(last_week_total_carbon_footprint, 2)
        week_before_last_total_distance = round(week_before_last_total_distance, 2)
        week_before_last_total_carbon_footprint = round(week_before_last_total_carbon_footprint, 2)

        this_week_avg = round((this_week_total_carbon_footprint) / this_week_total_distance, 2) if this_week_total_distance != 0 else 0
        last_week_avg = round((last_week_total_carbon_footprint) / last_week_total_distance, 2) if last_week_total_distance != 0 else 0
        week_before_avg = round((week_before_last_total_carbon_footprint) / week_before_last_total_distance, 2) if week_before_last_total_distance != 0 else 0
    except ZeroDivisionError:
        this_week_avg = last_week_avg = week_before_avg = 0

    # Prepare data for bar chart
    weeks = ['This Week', 'Last Week', 'Week Before Last']
    averages = [this_week_avg, last_week_avg, week_before_avg]

    # Create a simple bar chart
    avg_plot = go.Figure(data=[go.Bar(
        x=weeks,
        y=averages,
        marker_color='#1f77b4',
        text=[f"{avg:.2f}" for avg in averages],  # Display average values on bars
        textposition='auto'
    )])

    avg_plot.update_layout(
        height=450,
        width=400,
        margin=dict(t=50, b=50, l=0, r=0),
        title_text="Average CO2 per Meter of Travel (g/km)",
        title_x=0.5,
        paper_bgcolor='#E5F6DF',
        plot_bgcolor='#E5F6DF',
        font=dict(
            family="Arial, sans-serif",
            color='#00563B',
            size=14
        ),
        title_font=dict(
            family="Arial, sans-serif",
            color='#00563B',
            size=16
        )
    )

    # Convert the figures to HTML
    distance_pie_html = distance_pie.to_html(full_html=False, include_plotlyjs='cdn')
    carbon_footprint_pie_html = carbon_footprint_pie.to_html(full_html=False, include_plotlyjs='cdn')
    avg_plot_html = avg_plot.to_html(full_html=False, include_plotlyjs='cdn')

    return render(request, 'mainapp/mappage.html', {
        'chats': chats, 
        'distance_pie': mark_safe(distance_pie_html),
        'carbon_footprint_pie': mark_safe(carbon_footprint_pie_html), 
        'avg_graph': mark_safe(avg_plot_html),
        'w1total_distance': this_week_total_distance,
        'w1total_co2': this_week_total_carbon_footprint,
        'OLAMAPS_API':OLAMAPS_API,
    })


@login_required(login_url='/login/')
def logtrip(request):
    user = request.user

    if request.method == 'POST':
        # Retrieve form data
        source_add = request.POST.get('source')
        dest_add = request.POST.get('destination')
        source_lat = request.POST.get('source_lat')
        source_lon = request.POST.get('source_lng')
        destination_lat = request.POST.get('dest_lat')
        destination_lon = request.POST.get('dest_lng')
        is_electric = request.POST.get('is_electric')
        mode_of_transport = request.POST.get('mode_of_transport')
        time_taken = request.POST.get('time_taken')
        date = request.POST.get('date')
        log_time = datetime.now().strftime('%H:%M:%S')

        # Debugging form input
        print(f"[DEBUG] Log Trip Form Data: Source={source_add}, Destination={dest_add}, Mode={mode_of_transport}")

        # If the vehicle is electric, adjust the mode of transport
        if is_electric == "yes":
            mode_of_transport = "e" + mode_of_transport

        # API request setup
        params = {
            'origin': f'{source_lat},{source_lon}',
            'destination': f'{destination_lat},{destination_lon}',
            'mode': 'driving',
            'alternatives': 'false',
            'steps': 'true',
            'overview': 'full',
            'language': 'en',
            'traffic_metadata': 'true',
            'api_key': OLAMAPS_API
        }

        # Make the API request
        try:
            response = requests.post('https://api.olamaps.io/routing/v1/directions', params=params)

            # Check if the API request was successful
            if response.status_code == 200:
                data = response.json()

                # Ensure the 'routes' key exists and has valid data
                if 'routes' in data and len(data['routes']) > 0:
                    legs = data['routes'][0]['legs']

                    total_distance = sum(leg['distance'] for leg in legs) / 1000  # Convert to km
                    total_duration_fetched = sum(leg['duration'] for leg in legs) / 60  # Convert to minutes

                    total_distance = round(total_distance, 2)
                    total_duration_fetched = round(total_duration_fetched, 2)

                    # Calculate carbon footprint
                    list_of_transport = {
                        "bus": 50, "ebus": 15, "train": 41, "etrain": 14, 
                        "car": 128, "ecar": 66.67, "metro": 5, "bicycle": 0, 
                        "walk": 0, "bike": 74, "ebike": 22, "rickshaw": 51.67, 
                        "erickshaw": 24.33, "scooter": 55, "escooter": 22
                    }

                    if mode_of_transport not in list_of_transport:
                        messages.error(request, 'Invalid mode of transport selected.')
                        return redirect('logtrip')

                    carbonfootprint = list_of_transport[mode_of_transport] * total_distance
                    if total_duration_fetched < float(time_taken):
                        extra_time = float(time_taken) - total_duration_fetched
                        carbonfootprint_per_min = carbonfootprint / total_duration_fetched
                        extra_co2 = extra_time * carbonfootprint_per_min
                        carbonfootprint += extra_co2

                    carbonfootprint = round(carbonfootprint, 2)

                    # Save the trip data to the database
                    TravelLog.objects.create(
                        user=user,
                        source_address=source_add,
                        destination_address=dest_add,
                        source_latitude=source_lat,
                        source_longitude=source_lon,
                        destination_latitude=destination_lat,
                        destination_longitude=destination_lon,
                        distance=total_distance,
                        date=date,
                        time_taken=time_taken,
                        time_duration_fetched=str(total_duration_fetched),  # Save fetched duration
                        is_electric=is_electric == "yes",
                        mode_of_transport=mode_of_transport,
                        carbon_footprint=carbonfootprint,
                        log_time=log_time
                    )

                    # Check if this is the first trip of the day
                    today = timezone.now().date() 
                    print(f"[DEBUG] Today's Date: {today}")

                    existing_trips = TravelLog.objects.filter(user=user, date=today)
                    print(f"[DEBUG] Existing trips for today: {[trip.id for trip in existing_trips]}")
                    if existing_trips.count() == 1:
                        print("[DEBUG] No previous trips found for today, awarding coins.")
                        try:
                            user_profile = UserProfile.objects.get(user=user)
                            print(f"[DEBUG] Current Coins: {user_profile.coins}")
                            user_profile.coins += 50 
                            user_profile.save()
                            print(f"[DEBUG] New Coins after Award: {user_profile.coins}")
                            messages.success(request, 'You earned 50 coins for your first trip today!')
                        except UserProfile.DoesNotExist:
                            messages.error(request, 'User profile not found. Contact support.')
                            return redirect('logtrip')
                    else:
                        print("[DEBUG] Trip already logged for today.")
                        messages.success(request, 'Trip logged successfully!')

                else:
                    messages.error(request, 'Invalid data received from API.')
                    print(f"[DEBUG] API response error: {data}")

            else:
                messages.error(request, 'Error fetching data from API')
                print(f"[DEBUG] API Request failed with status code: {response.status_code}")

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            print(f"[DEBUG] Error during API request: {str(e)}")

        return redirect('logtrip')

    travellog = TravelLog.objects.filter(user=user).order_by('-date', '-log_time')

    context = {
        'travellog': travellog,
        'OLAMAPS_API': OLAMAPS_API
    }
    return render(request, 'mainapp/LogTrip.html', context)



def get_weekly_leaderboard():
    today = datetime.now().date()
    now = datetime.now()

    # Adjust week start and end dates for a week starting on Sunday and ending on Saturday
    start_of_week = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
    end_of_week = start_of_week + timedelta(days=6)

    # Filter logs from the start of the current week (Sunday) to the end of the week (Saturday)
    weekly_logs = TravelLog.objects.filter(date__gte=start_of_week, date__lte=end_of_week)
    # Aggregate total distance and carbon footprint by user
    leaderboard = weekly_logs.values('user__id', 'user__username').annotate(
        total_distance=Sum('distance'),
        total_carbon=Sum('carbon_footprint')
    ).annotate(
        efficiency=F('total_carbon') / F('total_distance')
    ).order_by('efficiency')  # Order by efficiency (ascending for better efficiency)

    # Get all user profiles with avatars
    profiles = UserProfile.objects.values('user__id', 'avatar')

    # Create a dictionary for quick lookup of avatars by user id
    avatar_dict = {profile['user__id']: profile['avatar'] for profile in profiles}

    # Add avatar information and round efficiency to the leaderboard entries
    for entry in leaderboard:
        user_id = entry['user__id']
        entry['avatar'] = avatar_dict.get(user_id, 'default.jpg')  # Use default if no avatar found
        # Round efficiency to 2 decimal places
        entry['total_distance']= round(entry['total_distance'],2)
        entry['total_carbon']= round(entry['total_carbon'],2)
        entry['efficiency'] = round(entry['efficiency'], 2)

    return {
        'leaderboard': leaderboard,
        'current_datetime': now,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
    }

def friend_leaderboards(user):
    today = datetime.now().date()

    # Adjust week start and end dates for a week starting on Sunday and ending on Saturday
    start_of_week = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
    end_of_week = start_of_week + timedelta(days=6)

    # Get friends' IDs
    friends_from_user = Friendship.objects.filter(from_user=user, accepted=True).values_list('to_user', flat=True)
    friends_to_user = Friendship.objects.filter(to_user=user, accepted=True).values_list('from_user', flat=True)
    
    # Combine both lists to get all friends and include the user themselves
    friends_ids = set(friends_from_user) | set(friends_to_user)
    friends_ids.add(user.id)  # Include the logged-in user

    # Filter logs for friends and the logged-in user
    weekly_logs = TravelLog.objects.filter(user__id__in=friends_ids, date__gte=start_of_week, date__lte=end_of_week)

    # Aggregate total distance and carbon footprint by friend
    friend_leaderboard = weekly_logs.values('user__id', 'user__username').annotate(
        total_distance=Sum('distance'),
        total_carbon=Sum('carbon_footprint')
    ).annotate(
        efficiency=F('total_carbon') / F('total_distance')
    ).order_by('efficiency')  # Order by efficiency (ascending for better efficiency)

    # Get friend profiles with avatars
    profiles = UserProfile.objects.filter(user__id__in=friends_ids).values('user__id', 'avatar')

    # Create a dictionary for quick lookup of avatars by user id
    avatar_dict = {profile['user__id']: profile['avatar'] for profile in profiles}

    # Add avatar information and round efficiency to the friend leaderboard entries
    for entry in friend_leaderboard:
        user_id = entry['user__id']
        entry['avatar'] = avatar_dict.get(user_id, 'default.jpg')  # Use default if no avatar found
        # Round efficiency to 2 decimal places
        entry['total_distance']= round(entry['total_distance'],2)
        entry['total_carbon']= round(entry['total_carbon'],2)
        entry['efficiency'] = round(entry['efficiency'], 2)

    return friend_leaderboard

@login_required(login_url='/login/')
def leaderboards(request):
    now = datetime.now()
    user = request.user

    # Get the weekly leaderboard data
    leaderboard_data = get_weekly_leaderboard()

    # Get friend leaderboards data
    friends_lboard_data = friend_leaderboards(user)

    context = {
        'leaderboard': leaderboard_data['leaderboard'],
        'current_datetime': leaderboard_data['current_datetime'],
        'start_of_week': leaderboard_data['start_of_week'],
        'end_of_week': leaderboard_data['end_of_week'],
        'friends_leaderboard': friends_lboard_data  # Add friends leaderboard to context
    }
    return render(request, 'mainapp/leaderboards.html', context)


# Example Usage

# Set the API key as an environment variable
os.environ["API_KEY"] = API_KEY_GEMINI
genai.configure(api_key=os.environ["API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")


def analyze_travel_logs(travel_logs):
    short_distance_trips = []
    long_distance_trips = []

    for log in travel_logs:
        distance = log['distance']  # Access distance from the dictionary
        if distance < 2:  # Assuming distance is in kilometers
            short_distance_trips.append(log)
        else:
            long_distance_trips.append(log)
    print('Short Distance',short_distance_trips)
    print('Long Distance',long_distance_trips)
    return short_distance_trips, long_distance_trips

def generate_eco_friendly_suggestions(short_distance_trips, long_distance_trips):
    recommendations = []

    # Recommendation for short-distance trips
    if short_distance_trips:
        prompt_short = ("It seems like you frequently use scooters, bikes, or cars for short distances. "
                        "For trips less than 2 km, consider using more eco-friendly options such as walking or cycling. "
                        "Here are the trips where walking or cycling would be a better choice: ")
        prompt_short += ", ".join([f"{log['source_address']} to {log['destination_address']} ({log['distance']} km)" for log in short_distance_trips])
        
        recommendations.append(prompt_short)
    
    # Recommendation for long-distance trips
    if long_distance_trips:
        prompt_long = ("For longer distances, using public transport can significantly reduce your carbon footprint.Distance is in KM  "
                       "If you are currently using scooters, bikes, or cars for long trips, consider switching to buses, trains, or carpooling. "
                       "Here are the trips where public transport would be a more eco-friendly choice: ")
        prompt_long += ", ".join([f"{log['source_address']} to {log['destination_address']} ({log['distance']} km)" for log in long_distance_trips])
        
        recommendations.append(prompt_long)
    
    return recommendations

def get_eco_friendly_recommendations(travel_logs):
    short_distance_trips, long_distance_trips = analyze_travel_logs(travel_logs)
    
    raw_recommendations = generate_eco_friendly_suggestions(short_distance_trips, long_distance_trips)
    
    # Use LLM to generate polished content
    final_recommendations = []
    for rec in raw_recommendations:
        response = model.generate_content(f"Provide detailed eco-friendly travel advice and i want to show this in html so make it in that structure using bold,br: {rec}")
        final_recommendations.append(response.text)
    
    return final_recommendations



def get_personalized_recommendations(request):
    user = request.user
    today = datetime.now().date()
    
    start_of_week = today - timedelta(days=today.weekday() + 1) if today.weekday() != 6 else today
    end_of_week = start_of_week + timedelta(days=6)

    travel_logs = TravelLog.objects.filter(
        date__gte=start_of_week, 
        date__lte=end_of_week, 
        user=user
    ).values('source_address', 'destination_address', 'distance', 'date', 'mode_of_transport')

    # Convert QuerySet to list of dicts for compatibility
    travel_logs_list = list(travel_logs)

    # Process travel logs
    recommendations = get_eco_friendly_recommendations(travel_logs_list)
    
    
    return JsonResponse({'recommendations': recommendations})

def tips(request):
    return render(request,'mainapp/tips.html')



@login_required(login_url='/login/')
def redeem(request):
    user = request.user
    coin_balance = 0  
    try:
        user_profile = UserProfile.objects.get(user=user)
        coin_balance = user_profile.coins  # Fetch user's coin balance
        print(f"[DEBUG] Retrieved coin balance: {coin_balance} for user: {user.username}")
    except UserProfile.DoesNotExist:
        coin_balance = 0  # If user profile does not exist, set to 0
        print(f"[DEBUG] UserProfile does not exist for user: {user.username}")

    stores = Store.objects.all()  
    return render(request, 'mainapp/redeem.html', {'coin_balance': coin_balance,'stores': stores})


def submit_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.name = request.user  # Assuming the Feedback model has a ForeignKey to User
            feedback.submitted_at = timezone.now()  # Save current UTC time
            feedback.save()
            return redirect('redeem')  # Redirect to the redeem page
    else:
        form = FeedbackForm()

    return render(request, 'mainapp/redeem.html', {'form': form})