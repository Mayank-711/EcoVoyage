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

logger = logging.getLogger(__name__)

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
                    'api_key': 'upIsbo0X7RjH2SfHjy2eYpm8TWdynT6vFDCpA85y'
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
                    return redirect('mappage')
                else:
                    return render(request, 'mainapp/mappage.html', {'error': 'Error fetching data from API'})
            except Exception as e:
                return render(request, 'mainapp/mappage.html', {'error': str(e)})
            

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

    # Prepare data for pie charts
    modes_of_transport = [item['mode_of_transport'] for item in data]
    total_distances = [item['total_distance'] for item in data]
    total_carbon_footprints = [item['total_carbon_footprint'] for item in data]

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
        showlegend=False
    )])
    distance_pie.update_layout(
        title={
            'text': "Distance (km)",
            'x': 0.5,  # Center the title horizontally
            'xanchor': 'center',  # Center the title horizontally
            'y': 1.0,  # Position the title at the top
            'yanchor': 'top',  # Align the title to the top
            'font': {
                'size': 16,  # Adjust title font size as needed
                'color': '#00563B'  # Dark green color
            }
        },
        margin=dict(t=40, b=0, l=0, r=0),  # Adjust margins to fit the title
        height=400,  # Set height to ensure the title fits
        width=400  # Set width as needed
    )

    # Create the carbon footprint pie chart
    carbon_footprint_pie = go.Figure(data=[go.Pie(
        labels=modes_of_transport,
        values=total_carbon_footprints,
        marker=dict(colors=colors),
        showlegend=False
    )])
    carbon_footprint_pie.update_layout(
        title={
            'text': "Distance (km)",
            'x': 0.5,  # Center the title horizontally
            'xanchor': 'center',  # Center the title horizontally
            'y': 1.0,  # Position the title at the top
            'yanchor': 'top',  # Align the title to the top
            'font': {
                'size': 16,  # Adjust title font size as needed
                'color': '#00563B'  # Dark green color
            }
        },
        margin=dict(t=40, b=0, l=0, r=0),  # Adjust margins to fit the title
        height=400,  # Set height to ensure the title fits
        width=400  # Set width as needed
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

        this_week_avg = (this_week_total_carbon_footprint ) / this_week_total_distance if this_week_total_distance != 0 else 0
        last_week_avg = (last_week_total_carbon_footprint ) / last_week_total_distance if last_week_total_distance != 0 else 0
        week_before_avg = (week_before_last_total_carbon_footprint ) / week_before_last_total_distance if week_before_last_total_distance != 0 else 0
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
        text=[f"{avg:.2f}" for avg in averages],
        textposition='auto'
    )])

    avg_plot.update_layout(
        height=450,
        width=400,
        margin=dict(t=50, b=50, l=0, r=0),
        title_text="Average CO2 per Meter of Travel (g/km)",
        title_x=0.5,  # Center the title
        paper_bgcolor='#E5F6DF',  # Light green background
        plot_bgcolor='#E5F6DF',   # Light green background inside the plot
        font=dict(
            family="Arial, sans-serif",
            color='#00563B',      # Dark green text
            size=14
        ),
        title_font=dict(
            family="Arial, sans-serif",
            color='#00563B',      # Dark green title text
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
        'w1total_co2': this_week_total_carbon_footprint
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

        # If the vehicle is electric, adjust the mode of transport
        if is_electric == "yes":
            mode_of_transport = "e" + mode_of_transport

        # Define API parameters
        params = {
            'origin': f'{source_lat},{source_lon}',
            'destination': f'{destination_lat},{destination_lon}',
            'mode': 'driving',
            'alternatives': 'false',
            'steps': 'true',
            'overview': 'full',
            'language': 'en',
            'traffic_metadata': 'true',
            'api_key': 'upIsbo0X7RjH2SfHjy2eYpm8TWdynT6vFDCpA85y'
        }

        # Make the API request
        try:
            response = requests.post('https://api.olamaps.io/routing/v1/directions', params=params)
            if response.status_code == 200:
                data = response.json()
                legs = data['routes'][0]['legs']

                # Calculate total distance and duration
                total_distance = sum(leg['distance'] for leg in legs) / 1000  # Convert to km
                total_duration_fetched = sum(leg['duration'] for leg in legs) / 60  # Convert to minutes
                
                total_distance = round(total_distance, 2)
                total_duration_fetched = round(total_duration_fetched, 2)

                # Calculate carbon footprint
                list_of_transport = {
                    "bus": 50,
                    "ebus": 15,
                    "train": 41,
                    "etrain": 14,
                    "car": 128,
                    "ecar": 66.67,
                    "metro": 5,
                    "bicycle": 0,
                    "walk": 0,
                    "bike": 74,
                    "ebike": 22,
                    "rickshaw": 51.67,
                    "erickshaw": 24.33,
                    "scooter": 55,
                    "escooter": 22
                }

                if mode_of_transport not in list_of_transport:
                    messages.error(request, 'Invalid mode of transport selected.')
                    return redirect('logtrip')

                carbonfootprint = list_of_transport[mode_of_transport] * total_distance
                print(mode_of_transport, carbonfootprint, sep="\n")

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

                messages.success(request, 'Trip logged successfully!')
            else:
                messages.error(request, 'Error fetching data from API')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

        # Redirect to the logtrip page or another page
        return redirect('logtrip')

    travellog = TravelLog.objects.filter(user=user).order_by('-date','-log_time')

    # Send data to the frontend
    context = {
        'travellog': travellog
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
        entry['efficiency'] = round(entry['efficiency'], 2)

    return {
        'leaderboard': leaderboard,
        'current_datetime': now,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week
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

@login_required(login_url='/login/')
def redeem(request):
    return render(request,'mainapp/redeem.html')