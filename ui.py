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
            
            /* Hide tab indicators in column mode */
            .landscape-mode .stTabs [data-baseweb="tab-list"] {
                display: none;
            }
            
            .landscape-mode .stTabs [data-baseweb="tab-panel"] {
                padding-top: 0;
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
        # Get viewport size using experimental_get_viewport_size
        width = st.session_state.get("viewport_width", 1200)  # Default to landscape
        height = st.session_state.get("viewport_height", 800)
        
        if "viewport_width" not in st.session_state:
            # Only run once at startup
            try:
                width, height = st.experimental_get_viewport_size()
                st.session_state.viewport_width = width
                st.session_state.viewport_height = height
            except Exception:
                # Fallback if experimental feature is not available
                pass
        
        return width > height

    @staticmethod
    def display_responses(responses_with_api, responses_without_api):
        """Display model responses in nested tabs format"""
        # Create container for batch tabs
        batch_container = st.container()
        
        # Create batch tabs
        batch_tabs = batch_container.tabs(["OpenWeatherMap API", "Tanpa OpenWeatherMap API"])
        
        # Process each batch
        for batch_idx, (responses, batch_tab) in enumerate(zip([responses_with_api, responses_without_api], batch_tabs)):
            with batch_tab:
                if UI.is_landscape():
                    # Landscape mode: columns with containers
                    cols = st.columns(len(MODELS))
                    for idx, (model_type, response) in enumerate(responses.items()):
                        with cols[idx]:
                            with st.container(border=True):
                                st.markdown(f"### {MODELS[model_type]['display_name']}")
                                st.markdown(response)
                else:
                    # Portrait mode: nested tabs
                    model_tabs = st.tabs([MODELS[model]["display_name"] for model in MODELS.keys()])
                    for tab, (model_type, response) in zip(model_tabs, responses.items()):
                        with tab:
                            st.markdown(response)

    @staticmethod
    def create_response_containers():
        """Create and return containers for streaming responses"""
        # Container for all responses
        response_container = st.container()
        
        # Create batch tabs
        batch_tabs = response_container.tabs(["OpenWeatherMap API", "Tanpa OpenWeatherMap API"])
        
        tab_containers = {}
        
        # Process each batch
        for batch_idx, suffix in enumerate(['api', 'no_api']):
            with batch_tabs[batch_idx]:
                if UI.is_landscape():
                    # Landscape mode: columns with containers
                    cols = st.columns(len(MODELS))
                    for idx, model_type in enumerate(MODELS.keys()):
                        with cols[idx]:
                            with st.container(border=True):
                                st.markdown(f"### {MODELS[model_type]['display_name']}")
                                tab_containers[f"{model_type}_{suffix}"] = st.empty()
                else:
                    # Portrait mode: nested tabs
                    model_tabs = st.tabs([MODELS[model]["display_name"] for model in MODELS.keys()])
                    for model_type, tab in zip(MODELS.keys(), model_tabs):
                        with tab:
                            tab_containers[f"{model_type}_{suffix}"] = st.empty()
        
        return tab_containers

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