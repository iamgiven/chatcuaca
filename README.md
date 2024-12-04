# ChatCuaca 🌤️

[![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-v1.31+-red.svg)](https://streamlit.io)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> Asisten cuaca pintar yang bisa ngobrol santai dalam bahasa Indonesia, didukung beberapa model AI canggih dan data cuaca akurat.

<div align="center">
  <img src="https://raw.githubusercontent.com/iamgiven/chatcuaca/master/images/portrait_1.png" width="32.5%" />
  <img src="https://raw.githubusercontent.com/iamgiven/chatcuaca/master/images/portrait_2.png" width="32.5%" />
  <img src="https://raw.githubusercontent.com/iamgiven/chatcuaca/master/images/portrait_3.png" width="32.5%" />
  <img src="https://raw.githubusercontent.com/iamgiven/chatcuaca/master/images/landscape_1.png" width="97.5%" />
  <img src="https://raw.githubusercontent.com/iamgiven/chatcuaca/master/images/landscape_2.png" width="97.5%" />
</div>

## 🚀 Cara Pakai

### Yang Harus Disiapkan

- Python 3.9 ke atas
- pip
- git

### Instalasi

1. Clone dulu repo-nya
```bash
git clone https://github.com/iamgiven/chatcuaca.git
cd chatcuaca
```

2. Bikin virtual environment
```bash
# Kalo pake Windows
python -m venv venv
venv\Scripts\activate

# Kalo pake macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install yang dibutuhin
```bash
pip install -r requirements.txt
```

4. Setting API key
```bash
# Bikin folder .streamlit
mkdir .streamlit

# Copy template secrets.toml
cp secrets.toml.example .streamlit/secrets.toml
```

### Setting API Key

Edit file `.streamlit/secrets.toml`, terus isi API key kamu:

```toml
# API Keys
OPENWEATHER_API_KEY = "api_key_openweather_kamu"
GROQ_API_KEY = "api_key_groq_kamu"
GOOGLE_API_KEY = "api_key_google_kamu"
MISTRAL_API_KEY = "api_key_mistral_kamu"

# Setting lainnya udah ada di template
```

### Jalanin Aplikasinya

```bash
streamlit run main.py
```

Buka `http://localhost:8501` di browser kamu.

## 📁 Struktur Project

```
chatcuaca/
├── .streamlit/
│   └── secrets.toml     # Tempat API key
├── config.py           # Konfigurasi aplikasi
├── models.py           # Kode untuk model AI
├── weather_service.py  # Servis data cuaca
├── ui.py              # Tampilan aplikasi
├── main.py            # Program utama
├── requirements.txt    # Daftar package
└── README.md          # Dokumentasi
```

## 🔑 API Key yang Dibutuhin

Kamu perlu daftar dulu buat dapetin API key dari:

- [OpenWeather](https://openweathermap.org/api) - Buat data cuaca
- [Groq](https://console.groq.com/) - Buat akses model Llama
- [Google AI](https://makersuite.google.com/) - Buat akses model Gemini
- [Mistral AI](https://console.mistral.ai/) - Buat akses model Mistral

## 💡 Contoh Penggunaan

```python
# Tanya cuaca
"Bagaimana cuaca di Jakarta hari ini?"
"Prakiraan cuaca Yogyakarta besok"
"Cuaca Surabaya 3 hari ke depan"
```

## 📝 Cara Kontribusi

1. Fork dulu repo-nya
2. Bikin branch baru
   ```bash
   git checkout -b fitur/keren-banget
   ```
3. Commit perubahan kamu
   ```bash
   git commit -m 'Tambah fitur..'
   ```
4. Push ke branch
   ```bash
   git push origin fitur/keren-banget
   ```
5. Bikin Pull Request

