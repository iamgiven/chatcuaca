import streamlit as st
import requests
from datetime import datetime, timedelta
import groq
from google.ai import generativelanguage as glm
import google.generativeai as genai
from openai import OpenAI
import re
from utils import (
    extract_city_and_date,
    get_weather_data,
    format_weather_data,
    handle_general_chat
)

# Set page config
st.set_page_config(
    page_title="Weather Chatbot",
    page_icon="🌤️",
    layout="wide"
)

# Check for required API keys
required_keys = [
    'OPENWEATHER_API_KEY',
    'GROQ_API_KEY',
    'GOOGLE_API_KEY',
    'OPENROUTER_API_KEY'
]

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
        return "Maaf, saya sedang mengalami kendala teknis. Silakan coba lagi nanti."

def get_gemini_response(prompt):
    """Get response from Gemini model"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "Maaf, saya sedang mengalami kendala teknis. Silakan coba lagi nanti."

def get_claude_response(prompt):
    """Get response from Claude 3 Haiku via OpenRouter"""
    try:
        completion = openrouter_client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return "Maaf, saya sedang mengalami kendala teknis. Silakan coba lagi nanti."

def get_ai_response(prompt, client_func):
    """Generic function to get AI response with error handling"""
    try:
        return client_func(prompt)
    except Exception as e:
        return "Maaf, saya sedang mengalami kendala teknis. Silakan coba lagi nanti."

# Streamlit UI
st.title("🌤️ WeatherChat")

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# User input
user_input = st.chat_input("Tanyakan tentang cuaca...")

if user_input:
    # First check if it's general chat
    general_response = handle_general_chat(user_input)
    
    if general_response:
        st.session_state.chat_history.append({
            "user_input": user_input,
            "weather_data": None,
            "responses": {
                "Gemma 9B": general_response,
                "Gemini 1.5 Pro": general_response,
                "Claude 3 Haiku": general_response
            }
        })
    else:
        # Extract city and date from user input
        city, target_date = extract_city_and_date(user_input)
        
        if not city:
            response = "Maaf, saya tidak mengerti pertanyaan Anda. Silakan tanyakan tentang cuaca di kota tertentu, misalnya 'Bagaimana cuaca di Jakarta hari ini?'"
            st.session_state.chat_history.append({
                "user_input": user_input,
                "weather_data": None,
                "responses": {
                    "Gemma 9B": response,
                    "Gemini 1.5 Pro": response,
                    "Claude 3 Haiku": response
                }
            })
        else:
            # Get weather data
            with st.spinner("Mengambil data cuaca..."):
                weather_data = get_weather_data(city, target_date)
                if weather_data:
                    weather_info = format_weather_data(weather_data)
                else:
                    st.error(f"Maaf, tidak dapat menemukan data cuaca untuk {city}")
                    st.stop()
            
            # Construct prompt with RAG
            rag_prompt = f"""Based on this weather data, please provide a natural and informative response in Indonesian language to the user's question: "{user_input}"

Weather Data:
{weather_info}

Please provide a conversational response that includes the current conditions and any relevant recommendations based on the weather. If the question is about a future date, make sure to mention that this is a forecast."""

            # Get responses from all models
            with st.spinner("Mendapatkan respons dari model AI..."):
                responses = {
                    "Gemma 9B": get_ai_response(rag_prompt, lambda p: get_gemma_response(p)),
                    "Gemini 1.5 Pro": get_ai_response(rag_prompt, lambda p: get_gemini_response(p)),
                    "Claude 3 Haiku": get_ai_response(rag_prompt, lambda p: get_claude_response(p))
                }
                
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
    if chat["weather_data"]:
        with st.expander("Data Cuaca Lengkap"):
            st.code(chat["weather_data"])
    
    # Model responses in tabs
    tabs = st.tabs(["Gemma 9B", "Gemini 1.5 Pro", "Claude 3 Haiku"])
    for tab, (model, response) in zip(tabs, chat["responses"].items()):
        with tab:
            st.markdown(response)

# Sidebar with information
with st.sidebar:
    st.markdown("""
    ### Tentang Chatbot Ini
    Chatbot cuaca ini menggunakan teknologi RAG (Retrieval Augmented Generation) untuk memberikan informasi cuaca akurat yang dikombinasikan dengan respons AI dari tiga model berbeda:
    
    - Gemma 9B (via Groq)
    - Gemini 1.5 Pro (via Google AI)
    - Claude 3 Haiku (via OpenRouter)
    
    Data cuaca diambil dari OpenWeatherMap API.
    
    ### Cara Penggunaan
    Anda dapat menanyakan tentang:
    - Cuaca saat ini: "Bagaimana cuaca di Jakarta hari ini?"
    - Prakiraan cuaca: "Seperti apa cuaca di Tokyo besok?"
    """)