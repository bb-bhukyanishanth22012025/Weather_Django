from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import WeatherForecast
from datetime import datetime


class FetchWeatherData(APIView):
    def get(self, request):
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not latitude or not longitude or not start_date or not end_date:
            return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)

        weather_api_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m&timezone=auto&start_date={start_date}&end_date={end_date}"

        try:
            response = requests.get(weather_api_url)
            response.raise_for_status()
            weather_data = response.json()
            return Response(weather_data, status=status.HTTP_200_OK)
        except requests.RequestException as e:
            return Response({'error': 'Failed to fetch weather data', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WeatherDataAPIView(APIView):
    def post(self, request):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        if not latitude or not longitude or not start_date or not end_date:
            return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)

        weather_api_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m&timezone=auto&start_date={start_date}&end_date={end_date}"

        try:
            response = requests.get(weather_api_url)
            response.raise_for_status()
            weather_data = response.json()

            times = weather_data["hourly"]["time"]
            temperatures = weather_data["hourly"]["temperature_2m"]

            saved_count = 0
            for time, temperature in zip(times, temperatures):
                forecast_time = datetime.fromisoformat(time)

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
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        forecast_time = request.GET.get('forecast_time')

        queryset = WeatherForecast.objects.all()

        if latitude and longitude:
            queryset = queryset.filter(latitude=latitude, longitude=longitude)
            if forecast_time:
                queryset = queryset.filter(forecast_time=forecast_time)

        data = [
            {
                'latitude': record.latitude,
                'longitude': record.longitude,
                'forecast_time': record.forecast_time,
                'temperature': record.temperature
            }
            for record in queryset
        ]

        return Response(data, status=status.HTTP_200_OK)
