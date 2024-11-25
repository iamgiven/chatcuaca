import streamlit as st
import requests
from datetime import datetime, timedelta
import groq
import google.generativeai as genai
from openai import OpenAI
from mistralai import Mistral
import json

# Check for required API keys
required_keys = ['MISTRAL_API_KEY', 'GROQ_API_KEY', 'GOOGLE_API_KEY']
for key in required_keys:
    if key not in st.secrets:
        st.error(f'Missing {key} in secrets.toml')
        st.stop()

# Initialize clients with API keys from secrets
try:
    mistral_client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    groq_client = groq.Client(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"Error initializing API clients: {str(e)}")
    st.stop()

def is_weather_query(prompt):
    """Use Gemini to determine if the prompt is asking about weather"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        analysis_prompt = f"""
        Analyze if this query is asking about weather: "{prompt}"
        Return only "yes" or "no".
        Examples:
        "What's the weather like in New York?" → "yes"
        "Hi" → "no"
        "How are you?" → "no"
        "Will it rain in Jakarta tomorrow?" → "yes"
        """
        
        response = model.generate_content(analysis_prompt)
        return response.text.strip().lower() == "yes"
    except Exception as e:
        st.error("Error analyzing query type. Treating as general conversation.")
        return False

def extract_city_from_prompt(prompt):
    """Use Gemini to extract city from the prompt"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        analysis_prompt = f"""
        From this weather query: "{prompt}"
        Extract only the city name and return it as a single word.
        Do not include any other text or punctuation.
        Example 1: "What's the weather like in New York tomorrow?" → "new%20york"
        Example 2: "Bagaimana cuaca di Yogyakarta?" → "yogyakarta"
        Example 3: "berikan cuaca untuk kota sleman, pada tanggal 20 november 2024 jam 20:00" → "sleman"
        Translate any city name in english standard
        Example 4: "Seperti apa cuaca di Swedia besok malam?" → "Sweden"
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

def get_model_response(client, model_type, prompt, weather_data=None):
    """Get response from specified model with error handling"""
    try:
        # For weather queries, use the RAG prompt
        if weather_data:
            weather_info = format_weather_data(weather_data, prompt)
            rag_prompt = f"""Berdasarkan data cuaca berikut, berikan respons yang natural dan informatif untuk pertanyaan pengguna: "{prompt}"

{weather_info}

Pahami dengan teliti apa yang ditanyakan user. Jika tanggal yang ditanyakan tidak ada di dalam data, sampaikan saja tidak tahu. Berikan analisis singkat tentang kondisi cuaca dan saran yang relevan berdasarkan data tersebut. Gunakan bahasa yang ramah dan mudah dipahami."""
            final_prompt = rag_prompt
        else:
            # For general conversation, create a conversational prompt
            final_prompt = f"""Berikan respons yang ramah dan natural untuk pesan pengguna: "{prompt}"

Gunakan bahasa Indonesia yang sopan dan informal. Anda adalah asisten AI yang dapat memberikan informasi cuaca, tetapi juga bisa bercakap-cakap tentang topik umum."""
        
        if model_type == "mistral":
            completion = mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": final_prompt}]
            )
            return completion.choices[0].message.content
        
        elif model_type == "gemini":
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(final_prompt)
            return response.text
        
        elif model_type == "llama":
            completion = groq_client.chat.completions.create(
                model="llama-3.2-90b-vision-preview",
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.7,
                max_tokens=500
            )
            return completion.choices[0].message.content
            
    except Exception as e:
        return f"Maaf, terjadi kesalahan dalam mendapatkan respons: {str(e)}"

# Streamlit UI
st.set_page_config(
    page_title="ChatCuaca",
    page_icon="🌤️",
    layout="wide"
)

# Custom CSS to style the weather data container
st.markdown("""
    <style>
    .stCode {
        max-height: 400px;
        overflow-y: auto;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌤️ ChatCuaca")

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# User input
user_input = st.chat_input("Tanyakan tentang cuaca...")

if user_input:
    # Check if it's a weather query
    with st.spinner("Memahami pertanyaan Anda..."):
        is_weather = is_weather_query(user_input)
    
    weather_data = None
    if is_weather:
        # Extract city and get weather data for weather queries
        city = extract_city_from_prompt(user_input)
        if city:
            with st.spinner(f"Mengambil data cuaca untuk {city}..."):
                weather_data = get_weather_data(city)
                if not weather_data:
                    st.error(f"Tidak dapat mengambil data cuaca untuk {city}. Mohon periksa nama kota dan coba lagi.")
                    st.stop()

    # Get responses from all models
    with st.spinner("Menganalisis..."):
        responses = {}
        
        for model_type, display_name in [
            ("mistral", "Mistral Large"),
            ("gemini", "Gemini 1.5 Flash"),
            ("llama", "Llama 3.2 90B")
        ]:
            responses[display_name] = get_model_response(
                None, model_type, user_input, weather_data
            )

    # Store in chat history
    chat_entry = {
        "user_input": user_input,
        "responses": responses
    }
    if weather_data:
        chat_entry["weather_data"] = format_weather_data(weather_data, user_input)
    st.session_state.chat_history.append(chat_entry)

# Display chat history
for chat in st.session_state.chat_history:
    # User message
    st.chat_message("user").write(chat["user_input"])
    
    # Weather data (if available)
    if "weather_data" in chat:
        with st.expander("Data Cuaca Lengkap"):
            st.code(chat["weather_data"])
    
    # Model responses in tabs
    tabs = st.tabs(["Mistral Large", "Gemini 1.5 Flash", "Llama 3.2 90B"])
    for tab, (model, response) in zip(tabs, chat["responses"].items()):
        with tab:
            st.markdown(response)

# Sidebar with information
with st.sidebar:
    st.markdown("""
    ### Tentang Asisten Cuaca
    Asisten ini dapat memberikan informasi cuaca dan bercakap-cakap umum dengan fitur:
    
    ✨  Prakiraan cuaca hingga 5 hari ke depan

    🎯  Informasi detail per 3 jam

    🌍  Menggunakan bahasa Indonesia

    🤖  Analisis dari 3 model AI berbeda:
    - Mistral Large (via Mistral)
    - Gemini 1.5 Flash (via Google AI)
    - Llama 3.2 90B (via Groq)

    💬  Dapat melakukan percakapan umum
    
    Contoh interaksi:
    - "Bagaimana cuaca di Jakarta hari ini?"
    - "Prakiraan cuaca Yogyakarta besok"
    - "Cuaca Surabaya 3 hari ke depan"
    """)