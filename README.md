# Agile Wellness AI Chatbot

A modern, responsive AI chatbot web application for **Agile Wellness**, designed to provide wellness, fitness, nutrition, and health habits guidance.

## Project Structure

```
agile-ai-assistant/
├── backend/
│   ├── .env                 # Port and Gemini API Key configuration
│   ├── main.py              # FastAPI server & Gemini integration
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # UI Components (ChatWindow, InputBar, TypingIndicator, MessageBubble)
│   │   ├── services/        # Axios API client
│   │   ├── App.jsx          # Root Component & Chat state orchestration
│   │   ├── App.css          # Layout & Header styles
│   │   ├── index.css        # Global CSS, dark mode design system tokens
│   │   └── main.jsx         # React application entry point
│   ├── index.html           # Main HTML file
│   ├── package.json         # Frontend dependencies and scripts
│   └── vite.config.js       # Vite bundler configuration
└── .gitignore               # Root git ignore patterns
```

---

## Getting Started

### 1. Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your Gemini API key in `backend/.env`:
   Open `backend/.env` and replace `your_gemini_api_key_here` with your actual API key from [Google AI Studio](https://aistudio.google.com).
5. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The backend will be running at `http://localhost:8000`.

### 2. Frontend Setup (React + Vite)

1. Open a new terminal window and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The web application will be running at `http://localhost:5173`. Open this URL in your web browser.

---

## Key Features & Decisions

- **Aesthetics & Theme**: Implemented a modern dark-mode layout matching wellness/medical aesthetics (deep blue/black canvas, clean green gradients, glowing interactive badges).
- **Responsive Layout**: Fluid UI adapts from desktop screen resolutions down to mobile layouts.
- **Axios client**: Handled error propagation nicely so network problems or backend errors display inside user-friendly alert bubbles in the chat log instead of crashing.
- **FastAPI CORS**: Enabled cross-origin requests specifically for `http://localhost:5173`.
