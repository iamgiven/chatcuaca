# main.py
import streamlit as st
import asyncio
from models import ModelManager
from weather_service import WeatherService
from ui import UI
from config import MODELS, REQUIRED_API_KEYS, WEATHER_ANALYSIS_PROMPT, CITY_EXTRACTION_PROMPT, WEATHER_RESPONSE_PROMPT, GENERAL_CONVERSATION_PROMPT

class AppHelper:
    @staticmethod
    def check_required_keys():
        """Verify all required API keys are present"""
        for key in REQUIRED_API_KEYS:
            if key not in st.secrets:
                st.error(f'Missing {key} in secrets.toml')
                st.stop()

    @staticmethod
    def initialize_session_state():
        """Initialize session state variables"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'message_history' not in st.session_state:
            st.session_state.message_history = []

    @staticmethod
    def format_chat_context():
        """Format message history for model context"""
        formatted_history = ""
        for msg in st.session_state.message_history[-5:]:  # Ambil 5 pesan terakhir saja
            role = "Assistant" if msg["role"] == "assistant" else "Human"
            formatted_history += f"{role}: {msg['content']}\n"
        return formatted_history.strip()

    @staticmethod
    async def is_weather_query(model_manager, prompt):
        """Determine if prompt is asking about weather"""
        context = AppHelper.format_chat_context()
        formatted_prompt = WEATHER_ANALYSIS_PROMPT.format(
            context=context,
            prompt=prompt
        )
        try:
            response = await model_manager.get_single_response("gemini", formatted_prompt)
            return response.strip().lower() == "yes"
        except Exception as e:
            st.error("Error analyzing query type. Treating as general conversation.")
            return False

    @staticmethod
    async def extract_city_from_prompt(model_manager, prompt):
        """Extract city name from weather query with chat history context"""
        context = AppHelper.format_chat_context()
        formatted_prompt = CITY_EXTRACTION_PROMPT.format(
            context=context,
            prompt=prompt
        )
        try:
            response = await model_manager.get_single_response("gemini", formatted_prompt)
            return response.strip().lower()
        except Exception as e:
            st.error("Error extracting city. Please try again with a valid city name.")
            return None

async def main():
    # Initialize helper and session state
    helper = AppHelper()
    helper.check_required_keys()
    helper.initialize_session_state()
    
    # Initialize services
    model_manager = ModelManager()
    weather_service = WeatherService()
    
    # Setup UI
    UI.setup()
    UI.display_sidebar()
    
    # Display chat history
    UI.display_chat_history(st.session_state.chat_history)
    
    # Handle new user input
    user_input = st.chat_input("Tanyakan tentang cuaca...")
    
    if user_input:
        st.session_state.message_history.append({
            "role": "user",
            "content": user_input
        })

        context = AppHelper.format_chat_context()

        with st.spinner("Memahami pertanyaan Anda..."):
            is_weather = await helper.is_weather_query(model_manager, user_input)
        
        weather_data = None
        if is_weather and st.session_state.use_weather_api:  # Tambahkan pengecekan use_weather_api
            city = await helper.extract_city_from_prompt(model_manager, user_input)
            if city and city != "lokasi%20tidak%20diketahui":
                with st.spinner(f"Mengambil data cuaca untuk {city}..."):
                    weather_data = weather_service.get_weather_data(city)
                    if not weather_data:
                        st.error(f"Tidak dapat mengambil data cuaca untuk {city}. Mohon periksa nama kota dan coba lagi.")
                        st.stop()

        # Display user message
        st.chat_message("user").write(user_input)
        
        if weather_data:
            UI.display_weather_data(weather_service.format_weather_data(weather_data, user_input))

        # Prepare full prompt with context and API status
        context = AppHelper.format_chat_context()
        api_status_info = "" if st.session_state.use_weather_api else "\n[API OpenWeatherMap tidak digunakan. Berikan respons umum berdasarkan pengetahuan yang dimiliki.]"
        
        prompt_template = WEATHER_RESPONSE_PROMPT if weather_data else GENERAL_CONVERSATION_PROMPT
        full_prompt = prompt_template.format(
            context=context,
            prompt=user_input + api_status_info,
            weather_info=weather_service.format_weather_data(weather_data, user_input) if weather_data else ""
        )

        # Create containers for streaming responses
        response_containers, tab_containers = UI.create_response_containers()
        responses = {model: "" for model in MODELS.keys()}

        # Get streaming responses
        streams = await model_manager.get_streaming_responses(
            list(MODELS.keys()),
            full_prompt,
            weather_data
        )

        # Process streams
        async def process_stream(model_type: str, stream) -> None:
            async for chunk in stream:
                if chunk:
                    responses[model_type] += chunk
                    await asyncio.sleep(0)
                    response_containers[model_type].markdown(responses[model_type])
                    tab_containers[model_type].markdown(responses[model_type])

        # Run all tasks concurrently
        tasks = [
            asyncio.create_task(process_stream(model_type, stream))
            for model_type, stream in streams.items()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Add assistant response to message history
        st.session_state.message_history.append({
            "role": "assistant",
            "content": responses["mistral"]
        })

        # Store in chat history
        chat_entry = {
            "user_input": user_input,
            "responses": responses.copy()
        }
        if weather_data:
            chat_entry["weather_data"] = weather_service.format_weather_data(weather_data, user_input)
        st.session_state.chat_history.append(chat_entry)

if __name__ == "__main__":
    asyncio.run(main())