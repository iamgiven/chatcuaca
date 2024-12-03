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
Analyze if this query is asking about weather: "{prompt}"
Return only "yes" or "no".
Examples:
"What's the weather like in New York?" → "yes"
"Hi" → "no"
"How are you?" → "no"
"Will it rain in Jakarta tomorrow?" → "yes"
"""

CITY_EXTRACTION_PROMPT = """
Ekstrak nama kota dari query cuaca berikut: "{prompt}"

Tugas:
1. Identifikasi nama kota yang disebutkan dalam query.
2. Jika nama kota terdiri dari lebih dari satu kata, gabungkan menjadi satu kata dengan pemisah spasi diganti menjadi '%20'.
3. Jika nama kota memiliki nama alternatif atau singkatan umum, gunakan nama yang paling umum digunakan dalam konteks perkiraan cuaca. Contoh: "Jogja" menjadi "yogyakarta", "NY" menjadi "new%20york".
4. Jika query tidak menyebutkan kota secara eksplisit, coba tebak berdasarkan konteks geografis yang mungkin. Jika tidak memungkinkan, kembalikan "lokasi%20tidak%20diketahui".
5. Kembalikan HANYA nama kota yang diekstrak sebagai satu kata tunggal tanpa tambahan teks atau tanda baca.

Contoh:
*   "What's the weather like in New York tomorrow?" → "new%20york"
*   "Bagaimana cuaca di Jogja?" → "yogyakarta"
*   "berikan cuaca untuk kota sleman, pada tanggal 20 november 2024 jam 20:00" → "sleman"
*   "Seperti apa cuaca di Swedia besok malam?" → "sweden"
*   "Cuaca hari ini?" (dengan asumsi pengguna berada di Jakarta) → "jakarta"
*   "Bagaimana cuacanya?" (tanpa konteks lokasi) → "lokasi%20tidak%20diketahui"
*   "Cuaca di London, UK?" → "london"
*   "Perkiraan cuaca untuk LA?" → "los%20angeles"
"""

WEATHER_RESPONSE_PROMPT = """Berdasarkan data cuaca berikut, berikan respons yang natural dan informatif untuk pertanyaan pengguna: "{prompt}"

{weather_info}

Pahami dengan teliti apa yang ditanyakan user. Jika tanggal yang ditanyakan tidak ada di dalam data, sampaikan saja tidak tahu. Berikan analisis singkat tentang kondisi cuaca dan saran yang relevan berdasarkan data tersebut. Gunakan bahasa yang ramah dan mudah dipahami."""

GENERAL_CONVERSATION_PROMPT = """Berikan respons yang ramah dan natural untuk pesan pengguna: "{prompt}"

Gunakan bahasa Indonesia yang sopan dan informal. Anda adalah asisten AI yang dapat memberikan informasi cuaca, tetapi juga bisa bercakap-cakap tentang topik umum."""