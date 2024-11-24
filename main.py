import streamlit as st
import requests
from datetime import datetime, timedelta
import groq
import google.generativeai as genai
from openai import OpenAI
import json

# Check for required API keys
required_keys = ['OPENWEATHER_API_KEY', 'GROQ_API_KEY', 'GOOGLE_API_KEY', 'OPENROUTER_API_KEY']
for key in required_keys:
    if key not in st.secrets:
        st.error(f'Missing {key} in secrets.toml')
        st.stop()

# Initialize clients with API keys from secrets
try:
    groq_client = groq.Client(api_key=st.secrets["GROQ_API_KEY"])
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    openrouter_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=st.secrets["OPENROUTER_API_KEY"]
    )
except Exception as e:
    st.error(f"Error initializing API clients: {str(e)}")
    st.stop()

def extract_city_from_prompt(prompt):
    """Use Gemini to extract city from the prompt"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        analysis_prompt = f"""
        From this weather query: "{prompt}"
        Extract only the city name and return it as a single word.
        Do not include any other text or punctuation.
        Example 1: "What's the weather like in New York tomorrow?" → "newyork"
        Example 2: "Bagaimana cuaca di Yogyakarta?" → "yogyakarta"
        Example 3: "berikan cuaca untuk kota sleman, pada tanggal 20 november 2024 jam 20:00" → "sleman"
        """
        
        response = model.generate_content(analysis_prompt)
        city = response.text.strip().lower().replace(" ", "")
        return city
    except Exception as e:
        st.error("Tidak dapat memahami nama kota. Mohon coba lagi dengan nama kota yang valid.")
        return None

def get_weather_data(city):
    """Fetch 5-day weather forecast from OpenWeatherMap API"""
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={st.secrets['OPENWEATHER_API_KEY']}&units=metric&lang=id"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def format_weather_data(weather_data, prompt):
    """Format weather data into a structured prompt"""
    if not weather_data or 'list' not in weather_data:
        return "Data cuaca tidak tersedia"
    
    try:
        city_name = weather_data['city']['name']
        output = f"Data Cuaca untuk {city_name}:\n\n"
        
        # Get current date for reference
        current_date = datetime.now().date()
        
        # Group forecasts by date
        forecasts_by_date = {}
        for forecast in weather_data['list']:
            forecast_time = datetime.fromtimestamp(forecast['dt'])
            date_key = forecast_time.date()
            
            if date_key not in forecasts_by_date:
                forecasts_by_date[date_key] = []
            forecasts_by_date[date_key].append(forecast)
        
        # Format data for each date (up to 5 days)
        for date in sorted(forecasts_by_date.keys())[:5]:
            day_forecasts = forecasts_by_date[date]
            
            # Add date header
            if date == current_date:
                output += f"\n📅 Hari ini ({date.strftime('%d %B %Y')})\n"
            else:
                days_ahead = (date - current_date).days
                output += f"\n📅 {days_ahead} hari ke depan ({date.strftime('%d %B %Y')})\n"
            
            # Add forecasts for this date
            for forecast in day_forecasts:
                forecast_time = datetime.fromtimestamp(forecast['dt'])
                output += f"""
⏰ Pukul {forecast_time.strftime('%H:%M')}
🌡️ Suhu: {forecast['main']['temp']}°C
🌡️ Terasa seperti: {forecast['main']['feels_like']}°C
💧 Kelembaban: {forecast['main']['humidity']}%
💨 Kecepatan Angin: {forecast['wind']['speed']} m/s
🌥️ Kondisi: {forecast['weather'][0]['description']}
📊 Tekanan: {forecast['main']['pressure']} hPa
---"""
            
        return output.strip()
    except Exception as e:
        return f"Error dalam memformat data cuaca: {str(e)}"

def get_model_response(client, model_type, prompt, weather_data):
    """Get response from specified model with error handling"""
    try:
        if model_type == "gemma":
            completion = groq_client.chat.completions.create(
                model="gemma2-9b-it",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            return completion.choices[0].message.content
        
        elif model_type == "gemini":
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text
        
        elif model_type == "claude":
            completion = openrouter_client.chat.completions.create(
                model="anthropic/claude-3-haiku",
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content
            
    except Exception as e:
        return f"Maaf, terjadi kesalahan dalam mendapatkan respons: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="Asisten Cuaca Indonesia", page_icon="🌤️")

st.title("🌤️ Asisten Cuaca Indonesia")

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# User input
user_input = st.chat_input("Tanyakan tentang cuaca di kota manapun (contoh: 'Bagaimana cuaca di Jakarta besok?')")

if user_input:
    # Extract city from prompt
    with st.spinner("Memahami pertanyaan Anda..."):
        city = extract_city_from_prompt(user_input)
        if not city:
            st.stop()
    
    # Get weather data
    with st.spinner(f"Mengambil data cuaca untuk {city}..."):
        weather_data = get_weather_data(city)
        if not weather_data:
            st.error(f"Tidak dapat mengambil data cuaca untuk {city}. Mohon periksa nama kota dan coba lagi.")
            st.stop()
        
        weather_info = format_weather_data(weather_data, user_input)
    
    # Construct prompt with RAG
    rag_prompt = f"""Berdasarkan data cuaca berikut, berikan respons yang natural dan informatif untuk pertanyaan pengguna: "{user_input}"

{weather_info}

Berikan analisis singkat tentang kondisi cuaca dan saran yang relevan berdasarkan data tersebut. Gunakan bahasa yang ramah dan mudah dipahami. IMPORTANT!! -> Jika tanggal yang ditanyakan tidak tersedia di dalam data, sampaikan saja tidak tahu. Jika ada, ikuti instruksi sebelumnya."""

    # Get responses from all models
    with st.spinner("Menganalisis data cuaca..."):
        responses = {}
        
        for model_type, display_name in [
            ("gemma", "Gemma 2 9B"),
            ("gemini", "Gemini 1.5 Flash"),
            ("claude", "Claude 3 Haiku")
        ]:
            responses[display_name] = get_model_response(
                None, model_type, rag_prompt, weather_data
            )

    # Store in chat history
    st.session_state.chat_history.append({
        "user_input": user_input,
        "weather_data": weather_info,
        "responses": responses
    })

# Display chat history
for chat in st.session_state.chat_history:
    # User message
    st.chat_message("user").write(chat["user_input"])
    
    # Weather data
    with st.expander("Data Cuaca Lengkap"):
        st.code(chat["weather_data"])
    
    # Model responses in tabs
    tabs = st.tabs(["Gemma 2 9B", "Gemini 1.5 Flash", "Claude 3 Haiku"])
    for tab, (model, response) in zip(tabs, chat["responses"].items()):
        with tab:
            st.markdown(response)

# Sidebar with information
with st.sidebar:
    st.markdown("""
    ### Tentang Asisten Cuaca
    Asisten ini memberikan informasi cuaca untuk kota-kota di Indonesia dan dunia dengan fitur:
    
    ✨ Prakiraan cuaca hingga 5 hari ke depan
    🎯 Informasi detail per 3 jam
    🌍 Mendukung bahasa Indonesia
    🤖 Analisis dari 3 model AI berbeda
    
    Contoh pertanyaan:
    - "Bagaimana cuaca di Jakarta hari ini?"
    - "Prakiraan cuaca Yogyakarta besok"
    - "Cuaca Surabaya 3 hari ke depan"
    """)