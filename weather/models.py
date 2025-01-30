from django.db import models

class WeatherForecast(models.Model):
    latitude = models.DecimalField(max_digits=6, decimal_places=4)
    longitude = models.DecimalField(max_digits=6, decimal_places=4)
    forecast_time = models.DateTimeField()  
    temperature = models.DecimalField(max_digits=4, decimal_places=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['latitude', 'longitude', 'forecast_time'], name='unique_weather_record')
        ]

    def __str__(self):
        return f"{self.forecast_time} - ({self.latitude}, {self.longitude}): {self.temperature}°C"
