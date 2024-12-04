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
    async def is_weather_query(model_manager, prompt):
        """Determine if prompt is asking about weather"""
        try:
            response = await model_manager.get_single_response(
                "gemini",
                WEATHER_ANALYSIS_PROMPT.format(prompt=prompt)
            )
            return response.strip().lower() == "yes"
        except Exception as e:
            st.error("Error analyzing query type. Treating as general conversation.")
            return False

    @staticmethod
    async def extract_city_from_prompt(model_manager, prompt):
        """Extract city name from weather query"""
        try:
            response = await model_manager.get_single_response(
                "gemini",
                CITY_EXTRACTION_PROMPT.format(prompt=prompt)
            )
            return response.strip().lower().replace(" ", "")
        except Exception as e:
            st.error("Tidak dapat memahami nama kota. Mohon coba lagi dengan nama kota yang valid.")
            return None

async def main():
    # Initialize helper
    helper = AppHelper()
    
    # Check for required API keys
    helper.check_required_keys()
    
    # Initialize services
    model_manager = ModelManager()
    weather_service = WeatherService()
    
    # Setup UI
    UI.setup()
    UI.display_sidebar()
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    UI.display_chat_history(st.session_state.chat_history)
    
    # Handle new user input
    user_input = st.chat_input("Tanyakan tentang cuaca...")
    
    if user_input:
        with st.spinner("Memahami pertanyaan Anda..."):
            is_weather = await helper.is_weather_query(model_manager, user_input)
        
        weather_data = None
        if is_weather:
            city = await helper.extract_city_from_prompt(model_manager, user_input)
            if city:
                with st.spinner(f"Mengambil data cuaca untuk {city}..."):
                    weather_data = weather_service.get_weather_data(city)
                    if not weather_data:
                        st.error(f"Tidak dapat mengambil data cuaca untuk {city}. Mohon periksa nama kota dan coba lagi.")
                        st.stop()

        # Display user message
        st.chat_message("user").write(user_input)
        
        if weather_data:
            UI.display_weather_data(weather_service.format_weather_data(weather_data, user_input))

        # Prepare prompt
        prompt = (WEATHER_RESPONSE_PROMPT if weather_data else GENERAL_CONVERSATION_PROMPT).format(
            prompt=user_input,
            weather_info=weather_service.format_weather_data(weather_data, user_input) if weather_data else ""
        )

        # Create containers for streaming responses
        response_containers, tab_containers = UI.create_response_containers()
        responses = {model: "" for model in MODELS.keys()}

        # Get streaming responses
        streams = await model_manager.get_streaming_responses(
            list(MODELS.keys()),
            prompt,
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