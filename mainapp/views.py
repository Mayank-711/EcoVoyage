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
from django.db.models import Sum
from django.utils.safestring import mark_safe

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
                        "Bus": 20.55,
                        "E-bus": 2.65,
                        "Train": 41,
                        "E-Train": 14,
                        "Car": 128,
                        "E-car": 66.67,
                        "Metro": 5,
                        "Bicycle": 0,
                        "Walk": 0,
                        "Bike": 74,
                        "Ebike": 22,
                        "Rickshaw": 25.67,
                        "Erickshaw": 13.33,
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
    start_of_week = today - timedelta(days=today.weekday())
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

    print(this_week_avg,last_week_avg,week_before_avg,sep="\n")
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
        'w1total_distance':this_week_total_distance,
        'w1total_co2':this_week_total_carbon_footprint
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
                    "bus": 20.55,
                    "ebus": 2.65,
                    "train": 41,
                    "etrain": 14,
                    "car": 128,
                    "ecar": 66.67,
                    "metro": 5,
                    "bicycle": 0,
                    "walk": 0,
                    "bike": 74,
                    "ebike": 22,
                    "rickshaw": 25.67,
                    "erickshaw": 13.33,
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

@login_required(login_url='/login/')
def leaderboards(request):
    
    return render(request,'mainapp/leaderboards.html')

@login_required(login_url='/login/')
def redeem(request):
    return render(request,'mainapp/redeem.html')