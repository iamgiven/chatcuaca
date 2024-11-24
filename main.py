[main.py]
import streamlit as st
import requests
from datetime import datetime
import groq
from google.ai import generativelanguage as glm
import google.generativeai as genai
from openai import OpenAI

# Check for required API keys
if 'OPENWEATHER_API_KEY' not in st.secrets:
    st.error('Missing OpenWeatherMap API key in secrets.toml')
    st.stop()
if 'GROQ_API_KEY' not in st.secrets:
    st.error('Missing Groq API key in secrets.toml')
    st.stop()
if 'GOOGLE_API_KEY' not in st.secrets:
    st.error('Missing Google API key in secrets.toml')
    st.stop()
if 'OPENROUTER_API_KEY' not in st.secrets:
    st.error('Missing OpenRouter API key in secrets.toml')
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

def get_weather_data(city):
    """Fetch weather data from OpenWeatherMap API"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={st.secrets['OPENWEATHER_API_KEY']}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {str(e)}")
        return None

def format_weather_data(weather_data):
    """Format weather data into a structured prompt"""
    if not weather_data:
        return "Weather data unavailable"
    
    return f"""
Current weather in {weather_data['name']}:
Temperature: {weather_data['main']['temp']}°C
Feels like: {weather_data['main']['feels_like']}°C
Humidity: {weather_data['main']['humidity']}%
Wind Speed: {weather_data['wind']['speed']} km/h
Conditions: {weather_data['weather'][0]['description']}
    """

def get_gemma_response(prompt):
    """Get response from Gemma 2B model via Groq"""
    try:
        completion = groq_client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error getting Gemma response: {str(e)}"

def get_gemini_response(prompt):
    """Get response from Gemini model"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error getting Gemini response: {str(e)}"

def get_claude_response(prompt):
    """Get response from Claude 3 Haiku via OpenRouter"""
    try:
        completion = openrouter_client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error getting Claude response: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="RAG Weather Chatbot", page_icon="🌤️")

st.title("🌤️ RAG Weather Chatbot")

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# User input
user_input = st.chat_input("Ask about the weather in any city...")

if user_input:
    # Extract city name from user input
    city = user_input.lower().replace("weather in ", "").replace("how is the weather in ", "").strip()
    
    # Get weather data
    with st.spinner("Fetching weather data..."):
        weather_data = get_weather_data(city)
        if weather_data:
            weather_info = format_weather_data(weather_data)
        else:
            st.error(f"Could not fetch weather data for {city}")
            st.stop()
    
    # Construct prompt with RAG
    rag_prompt = f"""Based on this weather data, please provide a natural and informative response to the user's question: "{user_input}"

Weather Data:
{weather_info}

Please include relevant information about the current conditions and any notable patterns or recommendations based on the weather."""

    # Get responses from all models
    with st.spinner("Getting responses from AI models..."):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.spinner("Getting Gemma response..."):
                gemma_response = get_gemma_response(rag_prompt)
        
        with col2:
            with st.spinner("Getting Gemini response..."):
                gemini_response = get_gemini_response(rag_prompt)
        
        with col3:
            with st.spinner("Getting Claude response..."):
                claude_response = get_claude_response(rag_prompt)

    # Store in chat history
    st.session_state.chat_history.append({
        "user_input": user_input,
        "weather_data": weather_info,
        "responses": {
            "Gemma 2B": gemma_response,
            "Gemini 1.5 Pro": gemini_response,
            "Claude 3 Haiku": claude_response
        }
    })

# Display chat history
for chat in st.session_state.chat_history:
    # User message
    st.chat_message("user").write(chat["user_input"])
    
    # Weather data
    with st.expander("Raw Weather Data"):
        st.code(chat["weather_data"])
    
    # Model responses in tabs
    tabs = st.tabs(["Gemma 9B", "Gemini 1.5 Pro", "Claude 3 Haiku"])
    for tab, (model, response) in zip(tabs, chat["responses"].items()):
        with tab:
            st.markdown(response)

# Sidebar with information
with st.sidebar:
    st.markdown("""
    ### About this Chatbot
    This weather chatbot uses RAG (Retrieval Augmented Generation) to provide accurate weather information combined with AI-generated responses from three different models:
    
    - Gemma 9B (via Groq)
    - Gemini 1.5 Pro (via Google AI)
    - Claude 3 Haiku (via OpenRouter)
    
    Weather data is retrieved from OpenWeatherMap API.
    """)