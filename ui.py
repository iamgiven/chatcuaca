# ui.py
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
            @media (orientation: portrait) {
                .stColumn, .stColumns, .stHorizontalBlock {
                    display: none;
                }
            }
            @media (orientation: landscape) {
                .stTabs {
                    display: none;
                }
            }
            </style>

        """, unsafe_allow_html=True)
       
        st.title("🌤️ ChatCuaca")

    @staticmethod
    def display_sidebar():
        """Display sidebar information"""
        with st.sidebar:
            # Tambahkan toggle untuk API OpenWeatherMap
            if 'use_weather_api' not in st.session_state:
                st.session_state.use_weather_api = True
            
            st.session_state.use_weather_api = st.toggle(
                "OpenWeatherMap API",
                value=st.session_state.use_weather_api,
                help="Matikan untuk melihat respons model tanpa data cuaca real-time"
            )
            
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

    @staticmethod
    def display_weather_data(weather_data):
        """Display weather data in an expander"""
        with st.expander("Data Cuaca Lengkap"):
            st.code(weather_data)

    @staticmethod
    def display_responses(responses):
        """Display model responses in both column and tab format"""
        # Column layout for landscape
        cols = st.columns(3)
        for i, (model_type, response) in enumerate(responses.items()):
            with cols[i]:
                with st.container(border=True):
                    st.subheader(MODELS[model_type]["display_name"])
                    st.markdown(response)
        
        # Tab layout for portrait
        tabs = st.tabs([MODELS[model]["display_name"] for model in responses.keys()])
        for tab, (model_type, response) in zip(tabs, responses.items()):
            with tab:
                st.markdown(response)

    @staticmethod
    def display_chat_history(chat_history):
        """Display full chat history"""
        for chat in chat_history:
            st.chat_message("user").write(chat["user_input"])
            
            if "weather_data" in chat:
                UI.display_weather_data(chat["weather_data"])
            
            UI.display_responses(chat["responses"])

    @staticmethod
    def create_response_containers():
        """Create and return containers for streaming responses"""
        cols = st.columns(3)
        response_containers = {}
        
        for i, model_type in enumerate(MODELS.keys()):
            with cols[i]:
                with st.container(border=True):
                    st.subheader(MODELS[model_type]["display_name"])
                    response_containers[model_type] = st.empty()
        
        tabs = st.tabs([MODELS[model]["display_name"] for model in MODELS])
        tab_containers = {}
        for model_type, tab in zip(MODELS.keys(), tabs):
            with tab:
                tab_containers[model_type] = st.empty()
                
        return response_containers, tab_containers