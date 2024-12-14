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
        if is_weather and st.session_state.use_weather_api:
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

        # Create containers for responses
        response_containers, tab_containers = UI.create_response_containers()
        responses = {model: "" for model in MODELS.keys()}

        # Prepare prompts for both API and non-API responses
        context = AppHelper.format_chat_context()
        
        # Format prompts for both scenarios
        api_prompt = WEATHER_RESPONSE_PROMPT.format(
            context=context,
            prompt=user_input,
            weather_info=weather_service.format_weather_data(weather_data, user_input) if weather_data else ""
        )
        
        no_api_prompt = GENERAL_CONVERSATION_PROMPT.format(
            context=context,
            prompt=user_input + "\n[API OpenWeatherMap tidak digunakan. Berikan respons umum berdasarkan pengetahuan yang dimiliki.]"
        )

        # Process responses in two groups
        async def process_responses(use_api: bool):
            prompt = api_prompt if use_api else no_api_prompt
            streams = await model_manager.get_streaming_responses(
                list(MODELS.keys()),
                prompt,
                weather_data if use_api else None
            )

            async def process_stream(model_type: str, stream):
                async for chunk in stream:
                    if chunk:
                        if use_api:
                            responses[model_type] = responses.get(model_type, "") + chunk
                        else:
                            # For non-API responses, append to existing content
                            current_content = responses.get(model_type, "")
                            if current_content:
                                current_content += "\n\n---\nRespons tanpa API:\n"
                            responses[model_type] = current_content + chunk
                        
                        # Update UI
                        if responses[model_type]:
                            response_containers[model_type].markdown(responses[model_type])
                            tab_containers[model_type].markdown(responses[model_type])

            tasks = [
                asyncio.create_task(process_stream(model_type, stream))
                for model_type, stream in streams.items()
            ]
            await asyncio.gather(*tasks)

        # Process responses sequentially based on API toggle
        if st.session_state.use_weather_api:
            # First process with API
            with st.spinner("Mendapatkan respons dengan API..."):
                await process_responses(use_api=True)
            # Then process without API
            with st.spinner("Mendapatkan respons tanpa API..."):
                await process_responses(use_api=False)
        else:
            # Only process without API
            with st.spinner("Mendapatkan respons..."):
                await process_responses(use_api=False)

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