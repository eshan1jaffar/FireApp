from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
import requests

def report(request):
    # Get user’s current location (latitude and longitude).
    # You can use a front-end script to request the user's location from their browser.
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')

    context = {
        'user_lat': user_lat,
        'user_lng': user_lng,
    }
    return render(request, 'reporter/reporter.html', context)
