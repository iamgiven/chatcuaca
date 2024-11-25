import streamlit as st
import groq
import google.generativeai as genai
from mistralai import Mistral
from config import MODELS

class ModelManager:
    def __init__(self):
        self.initialize_clients()
        
    def initialize_clients(self):
        """Initialize all API clients"""
        try:
            self.mistral_client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            self.groq_client = groq.Client(api_key=st.secrets["GROQ_API_KEY"])
        except Exception as e:
            st.error(f"Error initializing API clients: {str(e)}")
            st.stop()
    
    def get_response(self, model_type, prompt, weather_data=None):
        """Get response from specified model"""
        try:
            if model_type == "mistral":
                return self._get_mistral_response(prompt, weather_data)
            elif model_type == "gemini":
                return self._get_gemini_response(prompt, weather_data)
            elif model_type == "llama":
                return self._get_llama_response(prompt, weather_data)
        except Exception as e:
            return f"Maaf, terjadi kesalahan dalam mendapatkan respons: {str(e)}"
    
    def _get_mistral_response(self, prompt, weather_data):
        completion = self.mistral_client.chat.complete(
            model=MODELS["mistral"]["name"],
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    
    def _get_gemini_response(self, prompt, weather_data):
        model = genai.GenerativeModel(MODELS["gemini"]["name"])
        response = model.generate_content(prompt)
        return response.text
    
    def _get_llama_response(self, prompt, weather_data):
        completion = self.groq_client.chat.completions.create(
            model=MODELS["llama"]["name"],
            messages=[{"role": "user", "content": prompt}],
            temperature=MODELS["llama"]["temperature"],
            max_tokens=MODELS["llama"]["max_tokens"]
        )
        return completion.choices[0].message.content