import requests
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.

from django.shortcuts import render

from FireApp import settings
from homePage.forms import LocationForm


def home(request):
    return render(request, 'homePage/home.html')


import os
import requests
from urllib.parse import urlencode
from django.conf import settings
from django.shortcuts import render
from .forms import LocationForm

def search(request):
    image_url = None  # Initialize image_url to None in case it's not created yet
    latitude, longitude = None, None
    zoom = 13  # Default zoom level in case no radio button is selected

    if request.method == 'POST':
        print(request.POST)  # Log POST data for debugging
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.cleaned_data['location']
            # URL encode the address
            encoded_location = urlencode({'address': location})

            # Google Maps Geocoding API request URL
            google_maps_api_key = 'AIzaSyAAEzkGoGPmo780TKHqvycfR12p1wHzHxA'
            geocode_url = f'https://maps.googleapis.com/maps/api/geocode/json?{encoded_location}&key={google_maps_api_key}'

            # Make the API request
            response = requests.get(geocode_url)
            data = response.json()

            # Check if the response status is OK
            if data.get('status') == 'OK' and data.get('results'):
                # Get latitude and longitude from the first result
                location_info = data['results'][0]['geometry']['location']
                latitude = location_info['lat']
                longitude = location_info['lng']

                # Get the zoom level from the hidden input field (default to 13 if not provided)
                zoom_str = request.POST.get('zoom')
                if zoom_str:
                    try:
                        zoom = int(zoom_str)
                    except ValueError:
                        zoom = 13  # Fallback to default zoom if invalid value is provided
                else:
                    zoom = 13  # Fallback to default zoom if no zoom is provided

                # If "Analyze" button was clicked
                if 'analyze' in request.POST:
                    print("Analyze button clicked")  # Debugging output
                    # Construct the URL for the Google Maps Static API
                    static_map_url = f'https://maps.googleapis.com/maps/api/staticmap?center={latitude},{longitude}&zoom={zoom}&size=256x256&maptype=satellite&key={google_maps_api_key}'

                    # Fetch the image from the Google Maps Static API
                    map_response = requests.get(static_map_url)

                    if map_response.status_code == 200:
                        # Ensure the 'images' directory exists
                        images_folder = os.path.join(settings.MEDIA_ROOT, 'images')
                        if not os.path.exists(images_folder):
                            os.makedirs(images_folder)  # Make sure the folder exists

                        # Wipe the entire images folder (delete all existing files)
                        for filename in os.listdir(images_folder):
                            file_path = os.path.join(images_folder, filename)
                            if os.path.isfile(file_path):
                                os.remove(file_path)

                        # Save the new image to the media folder
                        image_name = 'location_image.jpg'
                        image_path = os.path.join(images_folder, image_name)

                        # Write the image content to the file
                        with open(image_path, 'wb') as img_file:
                            img_file.write(map_response.content)

                        # Set image_url to the saved image path
                        image_url = os.path.join(settings.MEDIA_URL, 'images', image_name)

                    else:
                        form.add_error(None, f'Failed to retrieve the map image. Status code: {map_response.status_code}')
                else:
                    form.add_error(None, 'Analyze button not clicked.')

                # Render the template with the form, coordinates, zoom, and image URL
                return render(request, 'homePage/search.html', {
                    'form': form,
                    'latitude': latitude,
                    'longitude': longitude,
                    'zoom': zoom,
                    'image_url': image_url
                })

            else:
                form.add_error(None, 'Could not retrieve coordinates for the given location.')

    else:
        form = LocationForm()

    return render(request, 'homePage/search.html', {'form': form})


