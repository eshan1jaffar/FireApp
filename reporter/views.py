import json
from math import radians, sin, atan2, sqrt, cos

from django.http import JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.shortcuts import render
import requests

from .models import Marker

from django.shortcuts import render
from .models import Marker





def report(request):
    if request.method == 'POST':
        # Check if the request is an AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Handle AJAX request (saving marker from the map)
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            urgency = data.get('urgency')

            # Ensure the latitude and longitude are floats before saving
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid latitude or longitude'})

            if urgency in ['low', 'moderate', 'high', 'critical']:
                # Save the marker data to the database
                Marker.objects.create(latitude=latitude, longitude=longitude, urgency=urgency)
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid urgency level'})

        else:
            # Handle regular form submission (if needed)
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            urgency = request.POST.get('urgency')

            if latitude and longitude and urgency:
                try:
                    # Convert latitude and longitude to floats
                    latitude = float(latitude)
                    longitude = float(longitude)
                except ValueError:
                    return render(request, 'reporter/reporter.html', {'error': 'Invalid latitude or longitude'})

                Marker.objects.create(latitude=latitude, longitude=longitude, urgency=urgency)
                return redirect('dashboard')  # Redirect to the dashboard after saving the marker
            else:
                return render(request, 'reporter/reporter.html', {'error': 'Please select a valid location and urgency.'})

    return render(request, 'reporter/reporter.html')


def dashboard(request):
    # Get all markers
    markers = Marker.objects.all()

    # Sort markers by urgency level
    urgency_order = {
        'critical': 1,
        'high': 2,
        'moderate': 3,
        'low': 4
    }

    # Sort the markers based on urgency
    markers = sorted(markers, key=lambda x: urgency_order.get(x.urgency, 5))

    return render(request, 'reporter/dashboard.html', {'markers': markers})
