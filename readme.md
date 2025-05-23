# 🎬 Text-to-Manim Video Generator

This project lets you generate educational videos using natural language prompts. You can describe a concept like _"Graph y = x² and show its shift to (x-2)²"_, and the app will create a Manim animation script and render a video for it.

Supports both CLI and API usage.

---

## ⚙️ Environment Setup

1. **Create a virtual environment** (first time only):

```bash
python -m venv venv
```

2. **Activate the virtual environment**:

```bash
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your-api-key-here
```

> 🔐 `.env` Add your Gemini API key here.

---

## ▶️ Running in CLI Mode

To generate videos from your terminal:

```bash
python -m app.main
```

- You'll be prompted for a natural language description (e.g., `"Visualize a vector addition"`).
- The script will be saved in `app/static/outputs/generated_scene.py`.
- The video will be rendered and saved to:

```
app/static/outputs/videos/generated_scene/480p15/scene.mp4
```

---

## 🌐 Running the API

To run the FastAPI server:

```bash
uvicorn app.main:app
```

Visit the interactive Swagger docs at:

📍 http://localhost:8000/docs

### API call to GET all chats

#### GET /chats

```bash
curl http://localhost:8000/chats/user_123
```

### API call to use chat

#### POST /chat

params: 
- user_id = user_123
- chat_id = uuid string
- prompt = string

```bash
curl -X POST http://localhost:8001/chat -H "Content-Type: application/json" -d "{\"user_id\":\"user_123\",\"chat_id\":\"8ca1f3a4-5ef3-4d26-9e58-dd394fd4dd6e\",\"prompt\":\"draw a red circle\"}"
```

Returns:

```json
{
  "video_url": "/static/outputs/videos/generated_scene/480p15/scene.mp4"
}
```

Access the video at:

📽️ http://localhost:8000/static/outputs/videos/generated_scene/480p15/scene.mp4

---

## 📁 Project Structure (Simplified)

```
app/
├── main.py               # CLI & FastAPI entry
├── script_gen.py         # Gemini + prompt pipeline
├── renderer.py           # Manim rendering subprocess
├── models.py             # Request/response schemas
├── prompt_engine/
│   ├── prompts.py
│   ├── intent_detector.py
│   └── smart_intent_detector.py
└── static/
    └── outputs/
        ├── generated_scene.py
        └── videos/
```

---

## 🛑 Git-ignored Files

- `.env` — contains sensitive API keys
- `app/static/outputs/` — stores generated scripts/videos

---

## 🧠 Examples to Try

- `"Explain the Pythagorean theorem step by step"`
- `"Graph y = sin(x) and y = cos(x)"`
- `"Show how a negative charge moves through an electric field"`
- `"Steps to make chicken curry"`

---

## 📦 Dependencies

Ensure you have Manim CE 0.19.0 installed and `pdflatex` (from MiKTeX/TeX Live) for MathTex support.
