"""
Weather Service for Agri-Nexus
Fetches weather data for farming locations
"""

import requests
from typing import Dict, Optional
from datetime import datetime


class WeatherService:
    """Weather data service using OpenWeatherMap API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather service
        
        Args:
            api_key: OpenWeatherMap API key (optional for demo mode)
        """
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.demo_mode = api_key is None
    
    def get_weather(self, city: str) -> Dict:
        """
        Get current weather for a city
        
        Args:
            city: City name (e.g., "Mumbai", "Delhi")
            
        Returns:
            Dictionary with weather data
        """
        if self.demo_mode:
            return self._get_demo_weather(city)
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': f"{city},IN",
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'city': city,
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'wind_speed': data['wind']['speed'],
                'pressure': data['main']['pressure'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Weather API error: {str(e)}")
            return self._get_demo_weather(city)
    
    def get_forecast(self, city: str, days: int = 5) -> Dict:
        """
        Get weather forecast for a city
        
        Args:
            city: City name
            days: Number of days (max 5 for free tier)
            
        Returns:
            Dictionary with forecast data
        """
        if self.demo_mode:
            return self._get_demo_forecast(city, days)
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'q': f"{city},IN",
                'appid': self.api_key,
                'units': 'metric',
                'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            forecasts = []
            for item in data['list'][:days * 8:8]:  # One per day
                forecasts.append({
                    'date': item['dt_txt'].split()[0],
                    'temperature': item['main']['temp'],
                    'description': item['weather'][0]['description'],
                    'humidity': item['main']['humidity'],
                    'rain_probability': item.get('pop', 0) * 100
                })
            
            return {
                'city': city,
                'forecasts': forecasts
            }
            
        except Exception as e:
            print(f"Forecast API error: {str(e)}")
            return self._get_demo_forecast(city, days)
    
    def _get_demo_weather(self, city: str) -> Dict:
        """Demo weather data when API key not available"""
        demo_data = {
            'Mumbai': {'temp': 32, 'humidity': 75, 'desc': 'Partly cloudy'},
            'Delhi': {'temp': 28, 'humidity': 60, 'desc': 'Clear sky'},
            'Bangalore': {'temp': 25, 'humidity': 70, 'desc': 'Light rain'},
            'Kolkata': {'temp': 30, 'humidity': 80, 'desc': 'Humid'},
            'Chennai': {'temp': 33, 'humidity': 78, 'desc': 'Hot and humid'},
            'Hyderabad': {'temp': 29, 'humidity': 65, 'desc': 'Sunny'},
            'Pune': {'temp': 27, 'humidity': 68, 'desc': 'Pleasant'},
            'Ahmedabad': {'temp': 35, 'humidity': 55, 'desc': 'Hot'}
        }
        
        data = demo_data.get(city, {'temp': 30, 'humidity': 70, 'desc': 'Moderate'})
        
        return {
            'city': city,
            'temperature': data['temp'],
            'feels_like': data['temp'] + 2,
            'humidity': data['humidity'],
            'description': data['desc'],
            'icon': '01d',
            'wind_speed': 3.5,
            'pressure': 1013,
            'timestamp': datetime.now().isoformat(),
            'demo_mode': True
        }
    
    def _get_demo_forecast(self, city: str, days: int) -> Dict:
        """Demo forecast data"""
        forecasts = []
        base_temp = 30
        
        for i in range(days):
            forecasts.append({
                'date': f"2026-03-{10+i:02d}",
                'temperature': base_temp + (i % 3),
                'description': ['Sunny', 'Partly cloudy', 'Light rain'][i % 3],
                'humidity': 70 + (i * 2),
                'rain_probability': [10, 30, 60][i % 3]
            })
        
        return {
            'city': city,
            'forecasts': forecasts,
            'demo_mode': True
        }


def get_weather_service(api_key: Optional[str] = None) -> WeatherService:
    """Get weather service instance"""
    return WeatherService(api_key)


if __name__ == '__main__':
    # Test weather service
    service = get_weather_service()
    
    print("Testing Weather Service (Demo Mode)")
    print("=" * 50)
    
    weather = service.get_weather("Mumbai")
    print(f"\nCurrent Weather in {weather['city']}:")
    print(f"  Temperature: {weather['temperature']}°C")
    print(f"  Humidity: {weather['humidity']}%")
    print(f"  Conditions: {weather['description']}")
    
    forecast = service.get_forecast("Mumbai", 3)
    print(f"\n3-Day Forecast for {forecast['city']}:")
    for day in forecast['forecasts']:
        print(f"  {day['date']}: {day['temperature']}°C - {day['description']}")
