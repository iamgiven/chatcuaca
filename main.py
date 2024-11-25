import streamlit as st
from models import ModelManager
from weather_service import WeatherService
from ui import UI
from config import MODELS, REQUIRED_API_KEYS, WEATHER_ANALYSIS_PROMPT, CITY_EXTRACTION_PROMPT, WEATHER_RESPONSE_PROMPT, GENERAL_CONVERSATION_PROMPT

def check_required_keys():
    """Verify all required API keys are present"""
    for key in REQUIRED_API_KEYS:
        if key not in st.secrets:
            st.error(f'Missing {key} in secrets.toml')
            st.stop()

def is_weather_query(model_manager, prompt):
    """Determine if prompt is asking about weather"""
    try:
        response = model_manager.get_response(
            "gemini",
            WEATHER_ANALYSIS_PROMPT.format(prompt=prompt)
        )
        return response.strip().lower() == "yes"
    except Exception as e:
        st.error("Error analyzing query type. Treating as general conversation.")
        return False

def extract_city_from_prompt(model_manager, prompt):
    """Extract city name from weather query"""
    try:
        response = model_manager.get_response(
            "gemini",
            CITY_EXTRACTION_PROMPT.format(prompt=prompt)
        )
        return response.strip().lower().replace(" ", "")
    except Exception as e:
        st.error("Tidak dapat memahami nama kota. Mohon coba lagi dengan nama kota yang valid.")
        return None

def main():
    # Check for required API keys
    check_required_keys()
    
    # Initialize services
    model_manager = ModelManager()
    weather_service = WeatherService()
    
    # Setup UI
    UI.setup()
    UI.display_sidebar()
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Handle user input
    user_input = st.chat_input("Tanyakan tentang cuaca...")
    
    if user_input:
        with st.spinner("Memahami pertanyaan Anda..."):
            is_weather = is_weather_query(model_manager, user_input)
        
        weather_data = None
        if is_weather:
            city = extract_city_from_prompt(model_manager, user_input)
            if city:
                with st.spinner(f"Mengambil data cuaca untuk {city}..."):
                    weather_data = weather_service.get_weather_data(city)
                    if not weather_data:
                        st.error(f"Tidak dapat mengambil data cuaca untuk {city}. Mohon periksa nama kota dan coba lagi.")
                        st.stop()
        
        # Get responses from all models
        with st.spinner("Menganalisis..."):
            responses = {}
            for model_type, config in MODELS.items():
                prompt = (WEATHER_RESPONSE_PROMPT if weather_data else GENERAL_CONVERSATION_PROMPT).format(
                    prompt=user_input,
                    weather_info=weather_service.format_weather_data(weather_data, user_input) if weather_data else ""
                )
                responses[config["display_name"]] = model_manager.get_response(
                    model_type, prompt, weather_data
                )
        
        # Store in chat history
        chat_entry = {
            "user_input": user_input,
            "responses": responses
        }
        if weather_data:
            chat_entry["weather_data"] = weather_service.format_weather_data(weather_data, user_input)
        st.session_state.chat_history.append(chat_entry)
    
    # Display chat history
    UI.display_chat_history(st.session_state.chat_history)

if __name__ == "__main__":
    main()