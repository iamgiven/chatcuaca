import streamlit as st

# Model configurations loaded from secrets.toml
MODELS = {
    "mistral": {
        "name": st.secrets["MISTRAL_MODEL_NAME"],
        "display_name": st.secrets["MISTRAL_DISPLAY_NAME"],
        "temperature": st.secrets["MISTRAL_TEMPERATURE"],
        "max_tokens": st.secrets["MISTRAL_MAX_TOKENS"]
    },
    "gemini": {
        "name": st.secrets["GEMINI_MODEL_NAME"],
        "display_name": st.secrets["GEMINI_DISPLAY_NAME"]
    },
    "llama": {
        "name": st.secrets["LLAMA_MODEL_NAME"],
        "display_name": st.secrets["LLAMA_DISPLAY_NAME"],
        "temperature": st.secrets["LLAMA_TEMPERATURE"],
        "max_tokens": st.secrets["LLAMA_MAX_TOKENS"]
    }
}

# API configurations
WEATHER_API_URL = st.secrets["WEATHER_API_URL"]
REQUIRED_API_KEYS = ['MISTRAL_API_KEY', 'GROQ_API_KEY', 'GOOGLE_API_KEY', 'OPENWEATHER_API_KEY']

# UI configurations
PAGE_CONFIG = {
    "page_title": "ChatCuaca",
    "page_icon": "🌤️",
    "layout": "wide"
}

# Prompt templates
WEATHER_ANALYSIS_PROMPT = """
Previous conversation:
{context}

Current query: "{prompt}"

Analyze if this query is asking about weather information.
Consider references like "disana", "disitu", "di kota itu" as weather queries if they refer to previously mentioned locations.
Return only "yes" or "no".

Examples:
"What's the weather like in New York?" → "yes"
"Where is Tokyo?" → "no"
"Seperti apa cuaca disana?" (after discussing about Paris) → "yes"
"Cuaca di kota itu bagaimana?" (after mentioning London) → "yes"
"Hi" → "no"
"How are you?" → "no"
"""

CITY_EXTRACTION_PROMPT = """
Previous conversation:
{context}

Current query: "{prompt}"

Extract the city name being discussed. Consider:
1. If the query uses words like "disana", "disitu", "di kota itu", extract the last mentioned city from the conversation
2. If a new city is mentioned explicitly, use that instead
3. Return "lokasi%20tidak%20diketahui" if no city can be determined
4. Convert multi-word city names using '%20' (e.g., "new york" → "new%20york")
5. Use common names for aliases (e.g., "jogja" → "yogyakarta")

Return ONLY the city name without any additional text.
"""

WEATHER_RESPONSE_PROMPT = """
Previous conversation:
{context}

Current query: "{prompt}"

Berdasarkan data cuaca berikut, berikan respons yang natural dan informatif:

{weather_info}

Pahami dengan teliti apa yang ditanyakan user. Jika tanggal yang ditanyakan tidak ada di dalam data, sampaikan saja tidak tahu. 
Berikan analisis singkat tentang kondisi cuaca dan saran yang relevan berdasarkan data tersebut. 
Gunakan bahasa yang ramah dan mudah dipahami.
"""

GENERAL_CONVERSATION_PROMPT = """
Previous conversation:
{context}

Current query: "{prompt}"

Berikan respons yang ramah dan natural untuk pesan pengguna di atas.
Gunakan bahasa Indonesia yang sopan dan informal. 
Anda adalah asisten AI yang dapat memberikan informasi cuaca, tetapi juga bisa bercakap-cakap tentang topik umum.
"""