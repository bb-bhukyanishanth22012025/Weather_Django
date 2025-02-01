from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import WeatherForecast
from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date

def is_valid_latitude(value):
    """Check if latitude is valid (-90 to 90)."""
    try:
        lat = float(value)
        return -90 <= lat <= 90
    except ValueError:
        return False

def is_valid_longitude(value):
    """Check if longitude is valid (-180 to 180)."""
    try:
        lon = float(value)
        return -180 <= lon <= 180
    except ValueError:
        return False

def validate_date(date_str):
    """Validate if the date is in YYYY-MM-DD format and parse it."""
    parsed_date = parse_date(date_str)
    if parsed_date is None:
        return None
    return parsed_date

class FetchWeatherData(APIView):
    """Fetches weather data from an external API without saving it to the database."""

    def get(self, request):
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Input Validation
        if not latitude or not longitude or not start_date or not end_date:
            return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)

        if not is_valid_latitude(latitude) or not is_valid_longitude(longitude):
            return Response({'error': 'Invalid latitude or longitude'}, status=status.HTTP_400_BAD_REQUEST)

        parsed_start_date = validate_date(start_date)
        parsed_end_date = validate_date(end_date)

        if not parsed_start_date or not parsed_end_date:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        if parsed_start_date > parsed_end_date:
            return Response({'error': 'start_date cannot be after end_date'}, status=status.HTTP_400_BAD_REQUEST)

        weather_api_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}&hourly=temperature_2m&"
            f"timezone=auto&start_date={start_date}&end_date={end_date}"
        )

        try:
            response = requests.get(weather_api_url)
            response.raise_for_status()
            weather_data = response.json()
            return Response(weather_data, status=status.HTTP_200_OK)
        except requests.RequestException as e:
            return Response({'error': 'Failed to fetch weather data', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WeatherDataAPIView(APIView):
    """Fetches weather data, stores it in the database, and allows retrieval."""

    def post(self, request):
        """Fetch weather data from API and save it to the database."""
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        # Input Validation
        if not latitude or not longitude or not start_date or not end_date:
            return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)

        if not is_valid_latitude(latitude) or not is_valid_longitude(longitude):
            return Response({'error': 'Invalid latitude or longitude'}, status=status.HTTP_400_BAD_REQUEST)

        parsed_start_date = validate_date(start_date)
        parsed_end_date = validate_date(end_date)

        if not parsed_start_date or not parsed_end_date:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        if parsed_start_date > parsed_end_date:
            return Response({'error': 'start_date cannot be after end_date'}, status=status.HTTP_400_BAD_REQUEST)

        weather_api_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}&hourly=temperature_2m&"
            f"timezone=auto&start_date={start_date}&end_date={end_date}"
        )

        try:
            response = requests.get(weather_api_url)
            response.raise_for_status()
            weather_data = response.json()

            times = weather_data.get("hourly", {}).get("time", [])
            temperatures = weather_data.get("hourly", {}).get("temperature_2m", [])

            if not times or not temperatures:
                return Response({'error': 'No weather data available'}, status=status.HTTP_204_NO_CONTENT)

            saved_count = 0
            for time, temperature in zip(times, temperatures):
                forecast_time = datetime.fromisoformat(time)

                # Avoid duplicate records
                if not WeatherForecast.objects.filter(latitude=latitude, longitude=longitude, forecast_time=forecast_time).exists():
                    WeatherForecast.objects.create(
                        latitude=latitude,
                        longitude=longitude,
                        forecast_time=forecast_time,
                        temperature=temperature
                    )
                    saved_count += 1

            return Response({'message': f'{saved_count} new weather records added to the database.'}, status=status.HTTP_201_CREATED)

        except requests.RequestException as e:
            return Response({'error': 'Failed to fetch weather data', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """Retrieve weather records from the database."""
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        forecast_time = request.GET.get('forecast_time')

        # Input Validation
        if (latitude and not is_valid_latitude(latitude)) or (longitude and not is_valid_longitude(longitude)):
            return Response({'error': 'Invalid latitude or longitude'}, status=status.HTTP_400_BAD_REQUEST)

        if forecast_time:
            try:
                forecast_time = datetime.fromisoformat(forecast_time)
            except ValueError:
                return Response({'error': 'Invalid forecast_time format. Use ISO 8601 format.'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = WeatherForecast.objects.all()

        if latitude and longitude:
            queryset = queryset.filter(latitude=latitude, longitude=longitude)
        if forecast_time:
            queryset = queryset.filter(forecast_time=forecast_time)

        if not queryset.exists():
            return Response({'error': 'No matching weather data found'}, status=status.HTTP_404_NOT_FOUND)

        data = [
            {
                'latitude': record.latitude,
                'longitude': record.longitude,
                'forecast_time': record.forecast_time.isoformat(),
                'temperature': record.temperature
            }
            for record in queryset
        ]

        return Response(data, status=status.HTTP_200_OK)


def weather_page(request):
    """Render a simple weather page."""
    return render(request, 'weather.html')
