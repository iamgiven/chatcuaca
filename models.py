# models.py
import streamlit as st
import groq
from groq import AsyncGroq
import google.generativeai as genai
from mistralai import Mistral
import asyncio
from config import MODELS
from typing import AsyncGenerator, Dict

class ModelManager:
    def __init__(self):
        self.initialize_clients()
        
    def initialize_clients(self):
        """Initialize all API clients"""
        try:
            self.mistral_client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
            self.async_groq_client = AsyncGroq(api_key=st.secrets["GROQ_API_KEY"])
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        except Exception as e:
            st.error(f"Error initializing API clients: {str(e)}")
            st.stop()

    async def get_single_response(self, model_type: str, prompt: str) -> str:
        """Get a single non-streaming response for analysis purposes"""
        try:
            if model_type == "mistral":
                completion = self.mistral_client.chat.completions.create(
                    model=MODELS["mistral"]["name"],
                    messages=[{"role": "user", "content": prompt}]
                )
                return completion.choices[0].message.content
            elif model_type == "gemini":
                model = genai.GenerativeModel(MODELS["gemini"]["name"])
                response = model.generate_content(prompt)
                return response.text
            elif model_type == "llama":
                completion = await self.async_groq_client.chat.completions.create(
                    model=MODELS["llama"]["name"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=MODELS["llama"]["temperature"],
                    max_tokens=MODELS["llama"]["max_tokens"]
                )
                return completion.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def get_streaming_responses(self, model_types: list, prompt: str, weather_data: Dict = None) -> Dict[str, AsyncGenerator]:
        """Get streaming responses from specified models concurrently"""
        streams = {}
        for model_type in model_types:
            if model_type == "mistral":
                streams[model_type] = self._get_mistral_stream(prompt, weather_data)
            elif model_type == "gemini":
                streams[model_type] = self._get_gemini_stream(prompt, weather_data)
            elif model_type == "llama":
                streams[model_type] = self._get_llama_stream(prompt, weather_data)
        return streams

    async def _get_mistral_stream(self, prompt: str, weather_data: Dict = None) -> AsyncGenerator[str, None]:
        try:
            stream = self.mistral_client.chat.stream(
                model=MODELS["mistral"]["name"],
                messages=[{"role": "user", "content": prompt}]
            )
            for chunk in stream:
                if hasattr(chunk, 'data'):
                    content = chunk.data.choices[0].delta.content
                    if content:
                        yield content
                elif hasattr(chunk, 'choices') and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error from Mistral: {str(e)}"

    async def _get_gemini_stream(self, prompt: str, weather_data: Dict = None) -> AsyncGenerator[str, None]:
        try:
            model = genai.GenerativeModel(MODELS["gemini"]["name"])
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error from Gemini: {str(e)}"

    async def _get_llama_stream(self, prompt: str, weather_data: Dict = None) -> AsyncGenerator[str, None]:
        try:
            stream = await self.async_groq_client.chat.completions.create(
                model=MODELS["llama"]["name"],
                messages=[{"role": "user", "content": prompt}],
                temperature=MODELS["llama"]["temperature"],
                max_tokens=MODELS["llama"]["max_tokens"],
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error from Llama: {str(e)}"