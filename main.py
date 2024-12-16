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
        if 'message_history_no_api' not in st.session_state:
            st.session_state.message_history_no_api = []

    @staticmethod
    def format_chat_context(with_api=True):
        """Format message history for model context"""
        formatted_history = ""
        history = st.session_state.message_history if with_api else st.session_state.message_history_no_api
        
        for msg in history[-5:]:  # Ambil 5 pesan terakhir saja
            role = "Assistant" if msg["role"] == "assistant" else "Human"
            # Untuk model tanpa API, hilangkan data cuaca dari respons asisten
            content = msg["content"]
            if not with_api and msg["role"] == "assistant":
                # Hapus bagian yang berisi data cuaca (misalnya suhu, kelembaban, dll)
                content = AppHelper.remove_weather_data(content)
            formatted_history += f"{role}: {content}\n"
        return formatted_history.strip()

    @staticmethod
    def remove_weather_data(text):
        """Menghapus informasi cuaca spesifik dari text"""
        # Daftar kata kunci yang menandakan adanya data cuaca
        weather_keywords = [
            "suhu:", "kelembaban:", "kecepatan angin:", "arah angin:",
            "tekanan:", "cuaca:", "°C", "km/h", "hPa", "%",
            "temperature:", "humidity:", "wind speed:", "wind direction:",
            "pressure:", "weather:", "precipitation:", "rainfall:",
            "forecast:", "predicted:", "akan turun", "kemungkinan hujan"
        ]
        
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Cek apakah baris mengandung data cuaca
            contains_weather_data = any(keyword.lower() in line.lower() for keyword in weather_keywords)
            if not contains_weather_data:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

    @staticmethod
    async def is_weather_query(model_manager, prompt):
        """Determine if prompt is asking about weather"""
        context = AppHelper.format_chat_context(with_api=True)
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
        context = AppHelper.format_chat_context(with_api=True)
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

async def process_batch(model_manager, prompt, weather_data, tab_containers, is_api_batch=True):
    """Process a batch of models in parallel"""
    responses = {model: "" for model in MODELS.keys()}

    async def process_model(model_type):
        stream = await model_manager.get_single_model_stream(
            model_type,
            prompt,
            weather_data if is_api_batch else None
        )
        suffix = "api" if is_api_batch else "no_api"
        async for chunk in stream:
            if chunk:
                responses[model_type] += chunk
                tab_containers[f"{model_type}_{suffix}"].markdown(responses[model_type])
                await asyncio.sleep(0)

    # Create tasks for all models in the batch
    tasks = [process_model(model_type) for model_type in MODELS.keys()]
    await asyncio.gather(*tasks)
    return responses

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
        # Add user message to both histories
        st.session_state.message_history.append({
            "role": "user",
            "content": user_input
        })
        st.session_state.message_history_no_api.append({
            "role": "user",
            "content": user_input
        })

        context = AppHelper.format_chat_context(with_api=True)
        is_weather = await helper.is_weather_query(model_manager, user_input)

        weather_data = None
        if is_weather:
            city = await helper.extract_city_from_prompt(model_manager, user_input)
            if city and city != "lokasi%20tidak%20diketahui":
                weather_data = weather_service.get_weather_data(city)
                if not weather_data:
                    st.error(f"Tidak dapat mengambil data cuaca untuk {city}. Mohon periksa nama kota dan coba lagi.")
                    st.stop()

        # Display user message
        st.chat_message("user").write(user_input)

        if weather_data:
            UI.display_weather_data(weather_service.format_weather_data(weather_data, user_input))

        # Prepare prompts for both API and non-API responses
        context_with_api = AppHelper.format_chat_context(with_api=True)
        context_no_api = AppHelper.format_chat_context(with_api=False)

        # Prompt with API data
        prompt_with_api = WEATHER_RESPONSE_PROMPT.format(
            context=context_with_api,
            prompt=user_input,
            weather_info=weather_service.format_weather_data(weather_data, user_input) if weather_data else ""
        )

        # Prompt without API data
        prompt_without_api = WEATHER_RESPONSE_PROMPT.format(
            context=context_no_api,
            prompt=user_input + "\n[API OpenWeatherMap tidak digunakan. Berikan respons umum berdasarkan pengetahuan yang dimiliki.]",
            weather_info=""
        ) if is_weather else GENERAL_CONVERSATION_PROMPT.format(
            context=context_no_api,
            prompt=user_input
        )

        # Create containers for streaming responses
        tab_containers = UI.create_response_containers()

        # Create placeholder containers for no-API tabs with spinners
        no_api_placeholders = {}
        for model in MODELS.keys():
            no_api_placeholders[model] = tab_containers[f"{model}_no_api"].empty()

        # Show spinners in no-API tabs
        for model in MODELS.keys():
            no_api_placeholders[model].markdown("⏳ Menunggu respon model dengan API selesai...")

        # Process first batch (with API) - all models in parallel
        responses_with_api = await process_batch(
            model_manager, 
            prompt_with_api, 
            weather_data, 
            tab_containers, 
            is_api_batch=True
        )

        # Clear spinners and process second batch
        for model in MODELS.keys():
            no_api_placeholders[model].empty()

        responses_without_api = await process_batch(
            model_manager, 
            prompt_without_api, 
            None, 
            tab_containers, 
            is_api_batch=False
        )

        # Store in chat history
        chat_entry = {
            "user_input": user_input,
            "responses_with_api": responses_with_api.copy(),
            "responses_without_api": responses_without_api.copy()
        }
        if weather_data:
            chat_entry["weather_data"] = weather_service.format_weather_data(weather_data, user_input)
        st.session_state.chat_history.append(chat_entry)

        # Add assistant responses to respective histories
        st.session_state.message_history.append({
            "role": "assistant",
            "content": responses_with_api["mistral"]
        })
        
        st.session_state.message_history_no_api.append({
            "role": "assistant",
            "content": responses_without_api["mistral"]
        })

if __name__ == "__main__":
    asyncio.run(main())