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
        if is_weather:
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

        # Prepare prompts for both API and non-API responses
        context = AppHelper.format_chat_context()
        
        # Prompt with API data
        prompt_with_api = WEATHER_RESPONSE_PROMPT.format(
            context=context,
            prompt=user_input,
            weather_info=weather_service.format_weather_data(weather_data, user_input) if weather_data else ""
        )
        
        # Prompt without API data
        prompt_without_api = WEATHER_RESPONSE_PROMPT.format(
            context=context,
            prompt=user_input + "\n[API OpenWeatherMap tidak digunakan. Berikan respons umum berdasarkan pengetahuan yang dimiliki.]",
            weather_info=""
        ) if is_weather else GENERAL_CONVERSATION_PROMPT.format(
            context=context,
            prompt=user_input
        )

        # Create containers for streaming responses
        tab_containers = UI.create_response_containers()
        
        # Initialize response dictionaries
        responses_with_api = {model: "" for model in MODELS.keys()}
        responses_without_api = {model: "" for model in MODELS.keys()}

        # Get streaming responses for both scenarios
        streams_with_api = await model_manager.get_streaming_responses(
            list(MODELS.keys()),
            prompt_with_api,
            weather_data
        )
        
        streams_without_api = await model_manager.get_streaming_responses(
            list(MODELS.keys()),
            prompt_without_api,
            None
        )

        # Process streams
        async def process_stream(model_type: str, stream, is_api: bool):
            responses_dict = responses_with_api if is_api else responses_without_api
            container_key = f"{model_type}_api" if is_api else f"{model_type}_no_api"
            
            async for chunk in stream:
                if chunk:
                    responses_dict[model_type] += chunk
                    await asyncio.sleep(0)
                    tab_containers[container_key].markdown(responses_dict[model_type])

        # Create tasks for all streams
        tasks = []
        for model_type in MODELS.keys():
            tasks.append(asyncio.create_task(
                process_stream(model_type, streams_with_api[model_type], True)
            ))
            tasks.append(asyncio.create_task(
                process_stream(model_type, streams_without_api[model_type], False)
            ))
        
        await asyncio.gather(*tasks, return_exceptions=True)

        # Store in chat history
        chat_entry = {
            "user_input": user_input,
            "responses_with_api": responses_with_api.copy(),
            "responses_without_api": responses_without_api.copy()
        }
        if weather_data:
            chat_entry["weather_data"] = weather_service.format_weather_data(weather_data, user_input)
        st.session_state.chat_history.append(chat_entry)

        # Add assistant response to message history (using API response as default)
        st.session_state.message_history.append({
            "role": "assistant",
            "content": responses_with_api["mistral"]
        })

if __name__ == "__main__":
    asyncio.run(main())