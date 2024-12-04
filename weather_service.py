import requests
import streamlit as st
from datetime import datetime
from config import WEATHER_API_URL

class WeatherService:
    @staticmethod
    def get_weather_data(city):
        """Fetch 5-day weather forecast"""
        url = f"{WEATHER_API_URL}?q={city}&appid={st.secrets['OPENWEATHER_API_KEY']}&units=metric&lang=id"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None
    
    @staticmethod
    def format_weather_data(weather_data, prompt):
        """Format weather data into structured format"""
        if not weather_data or 'list' not in weather_data:
            return "Data cuaca tidak tersedia"
        
        try:
            # Mengambil nama kota dan negara dari respons API
            city_name = weather_data['city']['name']
            country_code = weather_data['city']['country']
            query = f"{city_name}, {country_code}"  # Format: "Jakarta, ID"
            
            output = f"Data Cuaca untuk {query}:\n\n"
            
            current_date = datetime.now().date()
            forecasts_by_date = {}
            
            for forecast in weather_data['list']:
                forecast_time = datetime.fromtimestamp(forecast['dt'])
                date_key = forecast_time.date()
                
                if date_key not in forecasts_by_date:
                    forecasts_by_date[date_key] = []
                forecasts_by_date[date_key].append(forecast)
            
            for date in sorted(forecasts_by_date.keys())[:5]:
                day_forecasts = forecasts_by_date[date]
                
                if date == current_date:
                    output += f"\n📅 Hari ini ({date.strftime('%d %B %Y')})\n"
                else:
                    days_ahead = (date - current_date).days
                    output += f"\n📅 {days_ahead} hari ke depan ({date.strftime('%d %B %Y')})\n"
                
                for forecast in day_forecasts:
                    forecast_time = datetime.fromtimestamp(forecast['dt'])
                    output += WeatherService._format_forecast(forecast, forecast_time)
            
            return output.strip()
        except Exception as e:
            return f"Error dalam memformat data cuaca: {str(e)}"
    
    @staticmethod
    def _format_forecast(forecast, forecast_time):
        return f"""
⏰ Pukul {forecast_time.strftime('%H:%M')}
🌡️ Suhu: {forecast['main']['temp']}°C
🌡️ Terasa seperti: {forecast['main']['feels_like']}°C
💧 Kelembaban: {forecast['main']['humidity']}%
💨 Kecepatan Angin: {forecast['wind']['speed']} m/s
🌥️ Kondisi: {forecast['weather'][0]['description']}
📊 Tekanan: {forecast['main']['pressure']} hPa
---"""