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
from .ml_model.model import predict

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
            google_maps_api_key = settings.GOOGLE_MAPS_API_KEY
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
                        image_url = os.path.join(settings.STATIC_ROOT, 'homePage', 'images', 'photo.jpeg')

                        decision, prediction = predict(image_path)
                        prediction = round(prediction[0] * 100, 2)
                        decision = "No Wildfire" if decision == 0 else "Wildfire"
                        color = "red" if prediction > 50 else "black"
                        print(decision, prediction)

                    else:
                        form.add_error(None, f'Failed to retrieve the map image. Status code: {map_response.status_code}')
                else:
                    return render(request, 'homePage/search.html', {
                        'form': form,
                        'latitude': latitude,
                        'longitude': longitude,
                        'zoom': zoom,
                        'image_url': image_url,
                        'analyzed': False,
                        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
                        'FIREBASE_API_KEY': settings.FIREBASE_API_KEY,
                        'AUTH_DOMAIN': settings.AUTH_DOMAIN,
                        'PROJECT_ID': settings.PROJECT_ID,
                        'STORAGE_BUCKET': settings.STORAGE_BUCKET,
                        'MESSAGING_SENDER_ID': settings.MESSAGING_SENDER_ID,
                        'APP_ID': settings.APP_ID,
                        'MEASUREMENT_ID': settings.MEASUREMENT_ID
                    })

                # Render the template with the form, coordinates, zoom, and image URL
                return render(request, 'homePage/search.html', {
                    'form': form,
                    'latitude': latitude,
                    'longitude': longitude,
                    'zoom': zoom,
                    'image_url': image_url,
                    'analyzed': True,
                    'decision': decision,
                    'prediction': prediction,
                    'color': color,
                    'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
                    'FIREBASE_API_KEY': settings.FIREBASE_API_KEY,
                    'AUTH_DOMAIN': settings.AUTH_DOMAIN,
                    'PROJECT_ID': settings.PROJECT_ID,
                    'STORAGE_BUCKET': settings.STORAGE_BUCKET,
                    'MESSAGING_SENDER_ID': settings.MESSAGING_SENDER_ID,
                    'APP_ID': settings.APP_ID,
                    'MEASUREMENT_ID': settings.MEASUREMENT_ID
                })

            else:
                form.add_error(None, 'Could not retrieve coordinates for the given location.')

    else:
        form = LocationForm()

    return render(request, 'homePage/search.html', {'form': form,
                                                    'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
                                                    'FIREBASE_API_KEY': settings.FIREBASE_API_KEY,
                                                    'AUTH_DOMAIN': settings.AUTH_DOMAIN,
                                                    'PROJECT_ID': settings.PROJECT_ID,
                                                    'STORAGE_BUCKET': settings.STORAGE_BUCKET,
                                                    'MESSAGING_SENDER_ID': settings.MESSAGING_SENDER_ID,
                                                    'APP_ID': settings.APP_ID,
                                                    'MEASUREMENT_ID': settings.MEASUREMENT_ID})


import os
from django.conf import settings
from .models import OverlayImage


def save_overlay_image(image_path):
    # Define the path for the image in the media folder
    media_path = os.path.join(settings.MEDIA_ROOT, 'images', 'overlay.jpg')

    # Ensure the image file exists at the given path
    if os.path.exists(media_path):
        # Create an instance of the OverlayImage model and save the image
        overlay_image = OverlayImage(image=f'images/overlay.jpg')  # Path is relative to MEDIA_ROOT
        overlay_image.save()

        return overlay_image
    else:
        print("Image does not exist at the specified path")
        return None

from django.shortcuts import render
from .models import OverlayImage

def overlay_view(request):
    # Retrieve the most recently saved overlay image
    overlay_image = OverlayImage.objects.last()  # You can modify this query as needed

    return render(request, 'homePage/overlay.html', {'overlay_image': overlay_image})