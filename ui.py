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
    def is_landscape():
        """Check if the screen is in landscape mode"""
        width = st.session_state.get("viewport_width", 1200)  # Default to landscape
        height = st.session_state.get("viewport_height", 800)

        if "viewport_width" not in st.session_state:
            try:
                width, height = st.experimental_get_viewport_size()
                st.session_state.viewport_width = width
                st.session_state.viewport_height = height
            except Exception:
                pass

        return width > height

    @staticmethod
    def display_responses(responses_with_api, responses_without_api):
        """Display model responses in a vertical or horizontal layout based on screen orientation"""
        if UI.is_landscape():
            # Landscape mode: Two rows of three columns
            cols = st.columns(len(MODELS))
            for idx, (model_type, response) in enumerate(responses_with_api.items()):
                with cols[idx]:
                    with st.container(border=True):
                        st.markdown(f"### {MODELS[model_type]['display_name']}")
                        st.markdown(response)
            
            cols = st.columns(len(MODELS))
            for idx, (model_type, response) in enumerate(responses_without_api.items()):
                with cols[idx]:
                    with st.container(border=True):
                        st.markdown(f"### {MODELS[model_type]['display_name']} (Tanpa API)")
                        st.markdown(response)
        else:
            # Portrait mode: Single column layout
            for model_type, response in responses_with_api.items():
                with st.container(border=True):
                    st.markdown(f"### {MODELS[model_type]['display_name']}")
                    st.markdown(response)
            
            for model_type, response in responses_without_api.items():
                with st.container(border=True):
                    st.markdown(f"### {MODELS[model_type]['display_name']} (Tanpa API)")
                    st.markdown(response)

    @staticmethod
    def create_response_containers():
        """Create and return containers for streaming responses"""
        containers = {}
        
        if UI.is_landscape():
            # Landscape mode: Two rows of three columns
            cols_api = st.columns(len(MODELS))
            for idx, model_type in enumerate(MODELS.keys()):
                with cols_api[idx]:
                    with st.container(border=True):
                        st.markdown(f"### {MODELS[model_type]['display_name']}")
                        containers[f"{model_type}_api"] = st.empty()
            
            cols_no_api = st.columns(len(MODELS))
            for idx, model_type in enumerate(MODELS.keys()):
                with cols_no_api[idx]:
                    with st.container(border=True):
                        st.markdown(f"### {MODELS[model_type]['display_name']} (Tanpa API)")
                        containers[f"{model_type}_no_api"] = st.empty()
        else:
            # Portrait mode: Single column layout
            for model_type in MODELS.keys():
                with st.container(border=True):
                    st.markdown(f"### {MODELS[model_type]['display_name']}")
                    containers[f"{model_type}_api"] = st.empty()
            
            for model_type in MODELS.keys():
                with st.container(border=True):
                    st.markdown(f"### {MODELS[model_type]['display_name']} (Tanpa API)")
                    containers[f"{model_type}_no_api"] = st.empty()

        return containers

    @staticmethod
    def display_chat_history(chat_history):
        """Display full chat history"""
        for chat in chat_history:
            # Display user message
            st.chat_message("user").write(chat["user_input"])

            # Display weather data if available
            if "weather_data" in chat:
                UI.display_weather_data(chat["weather_data"])

            # Display model responses
            UI.display_responses(
                chat["responses_with_api"],
                chat["responses_without_api"]
            )