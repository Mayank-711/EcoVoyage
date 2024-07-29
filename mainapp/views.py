from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages
from .models import TravelLog
from django.utils.dateparse import parse_duration

@csrf_exempt
def mappage(request):
    user = request.user 
    username = user.username
    if request.method == 'POST':
        data = json.loads(request.body)
        source_add = data.get('source')
        dest_add = data.get('destination')
        source_lat = data.get('source_lat')
        source_lon = data.get('source_lon')
        destination_lat = data.get('destination_lat')
        destination_lon = data.get('destination_lon')
        distance = data.get("distance")
        date = data.get('date')
        time_taken = data.get('time_taken')
        is_electric = data.get('is_electric')
        mode_of_transport = data.get('mode_of_transport')
        if is_electric:
            mode_of_transport = "e" + mode_of_transport
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
            "erickshaw": 3.33,
            "scooter": 55,
            "escooter": 22
        }

        carbonfootprint = 0.00
        for a in list_of_transport:
            if mode_of_transport == a:
                carbonfootprint = list_of_transport[a] * float(distance)
        travel_log = TravelLog.objects.create(
            user=user,
            source_address=source_add,
            destination_address=dest_add,
            source_latitude=source_lat,
            source_longitude=source_lon,
            destination_latitude=destination_lat,
            destination_longitude=destination_lon,
            distance=distance,
            date=date,
            time_taken=time_taken,
            is_electric=is_electric,
            mode_of_transport=mode_of_transport,
            carbon_footprint=carbonfootprint
        )
        
        print(source_add, source_lat, source_lon, dest_add, destination_lon, destination_lat, distance,
            date, time_taken, is_electric, mode_of_transport, carbonfootprint, username, sep="\n")
        
        messages.success(request, f"You have traveled {distance} km and generated {carbonfootprint} gms of carbon footprint.")
        return redirect('mappage') 

    return render(request, 'mainapp/mappage.html')
