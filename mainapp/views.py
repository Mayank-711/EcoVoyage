from datetime import date, datetime
import logging
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages
from .models import TravelLog,Chat
from django.utils.dateparse import parse_duration
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
from django.contrib.auth.decorators import login_required
logger = logging.getLogger(__name__)


@csrf_exempt
@login_required(login_url='login')
def mappage(request):
    user = request.user
    
    if request.method == 'POST':
        search_date = date.today()
        search_time = datetime.now().strftime('%H:%M:%S')

        source_lat = request.POST.get('source_lat')
        source_lng = request.POST.get('source_lng')
        dest_lat = request.POST.get('dest_lat')
        dest_lng = request.POST.get('dest_lng')
        source_add = request.POST.get('source-add')
        dest_add = request.POST.get('destination-add')
        print(source_lat,source_lng,dest_lat,dest_lng,source_add,dest_add,sep="\n")
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
                        "Rickshaw": 25.
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
    
    # GET request or after processing the trip
    chats = Chat.objects.filter(user=user).order_by('-search_date', '-search_time')[:5]
    return render(request, 'mainapp/mappage.html', {'chats': chats})

@login_required(login_url='login')
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
                print(source_add,dest_add,source_lat,destination_lat,source_lon,destination_lon,mode_of_transport,time_taken,date,log_time,sep = "\n")
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

@login_required(login_url='login')
def leaderboards(request):
    return render(request,'mainapp/leaderboards.html')

@login_required(login_url='login')
def redeem(request):
    return render(request,'mainapp/redeem.html')