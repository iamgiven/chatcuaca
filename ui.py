import streamlit as st
from config import PAGE_CONFIG

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
        
        st.title("🌤️ ChatCuaca")
    
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
    def display_chat_history(chat_history):
        """Display chat history with responses"""
        for chat in chat_history:
            st.chat_message("user").write(chat["user_input"])
            
            if "weather_data" in chat:
                with st.expander("Data Cuaca Lengkap"):
                    st.code(chat["weather_data"])
            
            tabs = st.tabs(list(chat["responses"].keys()))
            for tab, (model, response) in zip(tabs, chat["responses"].items()):
                with tab:
                    st.markdown(response)