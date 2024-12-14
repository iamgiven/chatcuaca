import streamlit as st
from config import PAGE_CONFIG, MODELS

class UI:
    @staticmethod
    def setup():
        """Initialize Streamlit UI configuration"""
        st.set_page_config(**PAGE_CONFIG)
       
        st.markdown("""
            <style>
            .stCode {
                max-height: 400px;
                overflow-y: auto;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<h1 style='padding-top: 0rem; margin-top: -2.5rem;'>🌤️ ChatCuaca</h1>", unsafe_allow_html=True)

    @staticmethod
    def display_sidebar():
        """Display sidebar information"""
        with st.sidebar:
            st.markdown("""
            ### Tentang Asisten Cuaca
            Asisten ini dapat memberikan informasi cuaca dan bercakap-cakap umum dengan fitur:
           
            ✨  Prakiraan cuaca hingga 5 hari ke depan

            🎯  Informasi detail per 3 jam
           
            🌍  Menggunakan bahasa Indonesia
           
            🤖  Analisis dari 3 model AI berbeda dengan dan tanpa data cuaca real-time:
            - Mistral Large (via Mistral)
            - Gemini 1.5 Flash (via Google AI)
            - Llama 3.2 90B (via Groq)
           
            💬  Dapat melakukan percakapan umum
           
            Contoh interaksi:
            - "Bagaimana cuaca di Jakarta hari ini?"
            - "Prakiraan cuaca Yogyakarta besok"
            - "Cuaca Surabaya 3 hari ke depan"
            """)

    @staticmethod
    def display_weather_data(weather_data):
        """Display weather data in an expander"""
        with st.expander("Data Cuaca Lengkap"):
            st.code(weather_data)

    @staticmethod
    def display_responses(responses_with_api, responses_without_api):
        """Display model responses in nested tabs format"""
        # Create parent tabs
        parent_tabs = st.tabs(["Dengan OpenWeatherMap API", "Tanpa OpenWeatherMap API"])
        
        # Tab with API
        with parent_tabs[0]:
            model_tabs = st.tabs([MODELS[model]["display_name"] for model in MODELS.keys()])
            for model_tab, (model_type, response) in zip(model_tabs, responses_with_api.items()):
                with model_tab:
                    st.markdown(response)
        
        # Tab without API
        with parent_tabs[1]:
            model_tabs = st.tabs([MODELS[model]["display_name"] for model in MODELS.keys()])
            for model_tab, (model_type, response) in zip(model_tabs, responses_without_api.items()):
                with model_tab:
                    st.markdown(response)

    @staticmethod
    def display_chat_history(chat_history):
        """Display full chat history"""
        for chat in chat_history:
            st.chat_message("user").write(chat["user_input"])
            
            if "weather_data" in chat:
                UI.display_weather_data(chat["weather_data"])
            
            UI.display_responses(
                chat["responses_with_api"],
                chat["responses_without_api"]
            )

    @staticmethod
    def create_response_containers():
        """Create and return containers for streaming responses in nested tabs"""
        # Create parent tabs
        parent_tabs = st.tabs(["OpenWeatherMap API", "Tanpa OpenWeatherMap API"])
        
        tab_containers = {}
        
        # Tab with API
        with parent_tabs[0]:
            model_tabs = st.tabs([MODELS[model]["display_name"] for model in MODELS.keys()])
            for model_type, model_tab in zip(MODELS.keys(), model_tabs):
                with model_tab:
                    tab_containers[f"{model_type}_api"] = st.empty()
        
        # Tab without API
        with parent_tabs[1]:
            model_tabs = st.tabs([MODELS[model]["display_name"] for model in MODELS.keys()])
            for model_type, model_tab in zip(MODELS.keys(), model_tabs):
                with model_tab:
                    tab_containers[f"{model_type}_no_api"] = st.empty()
                
        return tab_containers