# JARVIS - Autonomous AI Assistant

An advanced AI assistant with voice and text interaction, task automation, and persistent memory. Inspired by Iron Man's J.A.R.V.I.S. Now featuring **True Jarvis Mode** for autonomous system control.

![Jarvis UI](docs/jarvis-preview.png)

## 🔮 Capabilities & Feature Status

| Feature | Status | Notes |
| :--- | :--- | :--- |
| **1. Voice & Text Input** | 🟡 **Working** | Text is perfect. Voice Input is active in UI & Backend, relying on browser Speech API. |
| **2. Local & Web Search** | 🟢 **Working** | Uses Perplexity/Groq for fast, sourced answers. |
| **3. File & App Ops** | 🟢 **Working** | Can open apps, read/write files, and move folders. |
| **4. Screen Perception** | 🟡 **Partial** | "See this" coming soon via Gemini Vision. |
| **5. Modern Web UI** | 🟢 **Full** | React + TypeScript + Tailwind. Beautiful & Responsive. |
| **6. Natural Voice** | 🟢 **Full** | Edge-TTS provides high-quality AI speech output. |
| **7. True Jarvis Mode** | 🟢 **Active** | "Safe Mode" vs "God Mode" logic implemented. |
| **8. AGI Core (CrewAI)** | 🟢 **Enabled** | **Multi-Agent Swarms active** (Python 3.12). |
| **9. Omniscient Memory** | 🟢 **Enabled** | **ChromaDB Vector Store active** for long-term recall. |
| **10. Aircraft Tracker** | 🟢 **Active** | Tracks flights overhead using OpenSky Network. |
| **11. Smart Weather** | 🟢 **Active** | Delivers real-time spoken weather briefs. |
| **12. Messaging** | 🟢 **Active** | Automates WhatsApp, Discord, Slack, Telegram. |
| **13. Stealth Browser** | 🟢 **Active** | Headless browsing for deep research. |
| **14. YouTube Tools** | 🟢 **Active** | Can search and summarize videos. |
| **15. Email Automation** | 🟢 **Active** | Drafts and sends emails via SMTP. |
| **16. Multi-User Login** | 🔵 **Personal** | Designed as a **Personal** Single-User Assistant. |
| **17. Self-Evolution** | 🟡 **Planned** | Roadmap item for self-modification. |

## 🚀 Getting Started

1. **Run `Jarvis.exe`** (Found in root folder).
2. It will launch the Backend and open the UI in your browser.
3. Start chatting or speaking!

### 🔒 Security Check

- **Safe Mode**: By default, Jarvis asks before running shell commands.
- **Personal Mode**: This is a single-user system. No login required (protected by local access).
- **⏰ Task Scheduling** - Automates recurring tasks
- **🌐 Modern Web UI** - Minimalist, responsive React interface
- **🔊 Natural Voice** - Edge-TTS for human-like responses
- **🛡️ True Jarvis Mode** - Autonomous system control (File/Shell access)
- **🧠 AGI Proactive Core** - Multi-Agent Swarms (Researcher, Planner) powered by CrewAI
- **✈️ Aircraft Tracker** - Real-time flight tracking via OpenSky
- **☁️ Smart Weather** - Spoken weather reports via wttr.in
- **💬 Universal Messaging** - Send messages on WhatsApp, Discord, Slack, Telegram
- **🕵️ Stealth Browser** - Undetectable headless browsing
- **📺 YouTube Tools** - Download videos and extract transcripts
- **📧 Email Automation** - Send emails via SMTP
- **🔐 Multi-User Login** - Secure authentication with guest mode
- **🔎 Multi-Provider AI** - Supports Groq, OpenAI, and Perplexity

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/jarvis-ai.git
   cd jarvis-ai/AI-Assistant-for-Computer
   ```

2. **Run the Start Script (Recommended)**

   Double-click `start-jarvis.bat` to automatically set up the environment, install dependencies, and launch both servers.

   *Or manually:*

   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate
   pip install -r requirements.txt
   python main.py

   # Frontend
   cd ../frontend
   npm install
   npm run dev
   ```

3. **Configuration**

   The `start-jarvis.bat` script will prompt you to create a `.env` file if it's missing. You'll need:
   - `GROQ_API_KEY`: For the main AI engine
   - `OPENAI_API_KEY`: (Optional) for fallback
   - `PERPLEXITY_API_KEY`: (Optional) for research
   - `SMTP_USER` / `SMTP_PASSWORD`: (Optional) for email features

## 🎤 Voice Commands

Try saying:

- "Open Chrome"
- "Note that I'm working on the fusion reactor project" (Saves to Memory)
- "Research the latest quantum computing breakthroughs" (Uses Perplexity)
- "Login to Amazon and check my orders" (Uses Stealth Browser)
- "Summarize this YouTube video [url]" (Uses YouTube Tool)
- "Send an email to Tony saying the suit is ready" (Uses SMTP)

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           Frontend (React)              │
│  • Chat Interface • Voice Input • TTS   │
│  • Settings • True Jarvis Toggle        │
└─────────────────┬───────────────────────┘
                  │ HTTP/WebSocket
┌─────────────────▼───────────────────────┐
│           Backend (FastAPI)             │
│  • ReAct Agent  • Dynamic Tooler        │
│  • OpenClaw Skills (Browser, YT, Email) │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│        Computer Control Layer           │
│  • Apps • Browser • Files • Commands    │
│  • PARA Memory System                   │
└─────────────────────────────────────────┘
```

## ⚙️ Configuration

### AI Providers

| Provider       | Env Var              | Capability                    |
| :------------- | :------------------- | :---------------------------- |
| **Groq**       | `GROQ_API_KEY`       | Fast, Low Latency (Llama 3)   |
| **OpenAI**     | `OPENAI_API_KEY`     | High Intelligence (GPT-4)     |
| **Perplexity** | `PERPLEXITY_API_KEY` | Web Research (Sonar)          |

### Voice Settings

Change the voice in `.env`:

```env
TTS_VOICE=en-GB-RyanNeural    # British male (default)
TTS_VOICE=en-US-GuyNeural     # American male
TTS_VOICE=en-GB-SoniaNeural   # British female
```

## 🔒 Security & True Jarvis Mode

- **Standard Mode**: System tools are restricted. AI can only answer questions and schedule tasks.
- **True Jarvis Mode**: Grants full system access (File I/O, Shell execution). Must be explicitly enabled in Settings.
- **Stealth Browser**: Operates logically separate from your main browser for privacy and automation.

## 📜 License

MIT License - feel free to use and modify!

## 🙏 Credits

- Original concept by [FatihMakes](https://youtube.com/@FatihMakes)
- Voice synthesis by [Edge-TTS](https://github.com/rany2/edge-tts)
- AI powered by [Groq](https://groq.com)
- OpenClaw Ecosystem for skill inspiration
