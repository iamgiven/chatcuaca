import re
from datetime import datetime, timedelta
import requests
import streamlit as st

def extract_city_and_date(user_input):
    """Extract city name and target date from natural language input"""
    # Convert input to lowercase for easier matching
    user_input = user_input.lower()
    
    # Initialize variables
    city = None
    target_date = None
    
    # Common date patterns
    today_patterns = ["hari ini", "sekarang"]
    tomorrow_patterns = ["besok", "tomorrow"]
    
    # Check for weather-related questions
    weather_patterns = ["cuaca", "weather", "forecast", "prakiraan", "bagaimana cuaca", "seperti apa cuaca"]
    is_weather_question = any(pattern in user_input for pattern in weather_patterns)
    
    if not is_weather_question:
        return None, None
    
    # Extract city name (looking for words after "di" or "in")
    city_match = re.search(r'(?:di|in)\s+([a-zA-Z\s]+?)(?:\s+(?:pada|hari|besok|tomorrow|today|ini)|$)', user_input)
    if city_match:
        city = city_match.group(1).strip()
    
    # Determine target date
    if any(pattern in user_input for pattern in tomorrow_patterns):
        target_date = (datetime.now() + timedelta(days=1)).date()
    elif any(pattern in user_input for pattern in today_patterns) or "pada hari ini" in user_input:
        target_date = datetime.now().date()
    else:
        target_date = datetime.now().date()  # Default to today if no date specified
    
    return city, target_date

def get_weather_data(city, target_date=None):
    """Fetch weather forecast data from OpenWeatherMap API"""
    if not city:
        return None
        
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={st.secrets['OPENWEATHER_API_KEY']}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if target_date:
            # Filter forecast data for target date
            target_date_str = target_date.strftime('%Y-%m-%d')
            forecasts = [item for item in data['list'] if item['dt_txt'].startswith(target_date_str)]
            
            if forecasts:
                # Aggregate forecasts for the day
                temps = [f['main']['temp'] for f in forecasts]
                feels_like = [f['main']['feels_like'] for f in forecasts]
                conditions = [f['weather'][0]['description'] for f in forecasts]
                
                return {
                    'name': data['city']['name'],
                    'target_date': target_date_str,
                    'main': {
                        'temp': sum(temps) / len(temps),
                        'feels_like': sum(feels_like) / len(feels_like),
                        'humidity': forecasts[0]['main']['humidity']
                    },
                    'wind': {'speed': forecasts[0]['wind']['speed']},
                    'weather': [{'description': max(set(conditions), key=conditions.count)}],
                    'forecast_details': forecasts
                }
        
        # If no target date or no forecast found, return current weather
        return {
            'name': data['city']['name'],
            'main': data['list'][0]['main'],
            'wind': data['list'][0]['wind'],
            'weather': data['list'][0]['weather']
        }
    except requests.exceptions.RequestException:
        return None

def format_weather_data(weather_data):
    """Format weather data into a structured prompt"""
    if not weather_data:
        return "Weather data unavailable"
    
    date_str = weather_data.get('target_date', 'today')
    basic_info = f"""
Weather forecast for {weather_data['name']} on {date_str}:
Temperature: {weather_data['main']['temp']:.1f}°C
Feels like: {weather_data['main']['feels_like']:.1f}°C
Humidity: {weather_data['main']['humidity']}%
Wind Speed: {weather_data['wind']['speed']} km/h
Conditions: {weather_data['weather'][0]['description']}
"""
    
    # Add detailed forecast if available
    if 'forecast_details' in weather_data:
        basic_info += "\nDetailed forecast:\n"
        for forecast in weather_data['forecast_details']:
            time = forecast['dt_txt'].split()[1][:5]
            basic_info += f"{time}: {forecast['main']['temp']:.1f}°C, {forecast['weather'][0]['description']}\n"
    
    return basic_info

def handle_general_chat(user_input):
    """Handle general chat inputs"""
    user_input = user_input.lower().strip()
    
    # Greetings patterns
    greetings = ["halo", "hi", "hello", "hai", "hei"]
    
    # Check for exact matches or starts with
    if user_input in greetings or any(user_input.startswith(g) for g in greetings):
        return """Halo! Saya adalah chatbot cuaca yang bisa membantu Anda mendapatkan informasi cuaca untuk kota mana saja.

Anda dapat menanyakan:
• Cuaca saat ini: "Bagaimana cuaca di Jakarta hari ini?"
• Prakiraan cuaca: "Seperti apa cuaca di Tokyo besok?"

Silakan tanyakan tentang cuaca di kota yang Anda inginkan!"""
    
    return None