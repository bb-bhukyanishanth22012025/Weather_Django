from django.urls import path
from .views import FetchWeatherData, WeatherDataAPIView, weather_page

urlpatterns = [
    path('weather/fetch', FetchWeatherData.as_view(), name='fetch_weather_data'),
    path('weather/', WeatherDataAPIView.as_view(), name='save_or_get_weather_data'),  
    path('', weather_page, name='weather_ui'),
]
