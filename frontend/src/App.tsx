import { useState, useEffect, useRef, useCallback } from 'react';
import { Virtuoso, type VirtuosoHandle } from 'react-virtuoso';
import Sidebar from './components/Sidebar';
import SettingsPanel from './components/SettingsPanel';
import ChatMessage from './components/ChatMessage';
import StepVisualizer from './components/StepVisualizer';
import LoginPage from './components/LoginPage';
import Changelog from './components/Changelog';
import './App.css';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  steps?: AgentStep[];
}

interface AgentStep {
  id: string;
  type: 'thinking' | 'planning' | 'tool_call' | 'observation' | 'response' | 'error';
  content: string;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  tool_result?: string;
  duration_ms?: number;
  tokens_used?: number;
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  pinned?: boolean;
}

interface Settings {
  provider: 'ollama' | 'groq' | 'openai' | 'perplexity';
  model: string;
  voice: string;
  voiceEnabled: boolean;
  voiceRate: string;
  voicePitch: string;
  appLanguage: string;
  mode: 'standard' | 'true_jarvis';
}

const MODELS: Record<string, { models: string[]; description: string }> = {
  ollama: { models: ['llama3.2', 'llama3.1', 'mistral', 'codellama'], description: 'Self-hosted' },
  groq: { models: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768'], description: 'Fast cloud' },
  openai: { models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'], description: 'OpenAI' },
  perplexity: { models: ['sonar-pro', 'sonar', 'sonar-reasoning-pro'], description: 'Search AI' }
};

function App() {
  // Auth State
  const [user, setUser] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  // State
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const activeSessionIdRef = useRef<string | null>(null);

  // Sync ref with state
  useEffect(() => {
    activeSessionIdRef.current = activeSessionId;
  }, [activeSessionId]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showChangelog, setShowChangelog] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentSteps, setCurrentSteps] = useState<AgentStep[]>([]);
  const [showModelPicker, setShowModelPicker] = useState(false);
  const [settings, setSettings] = useState<Settings>({
    provider: 'groq',
    model: 'llama-3.3-70b-versatile',
    voice: 'en-GB-RyanNeural',
    voiceEnabled: true,
    voiceRate: '+5%',
    voicePitch: '+0Hz',
    appLanguage: 'en',
    mode: 'standard',
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const virtuosoRef = useRef<VirtuosoHandle>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const modelPickerRef = useRef<HTMLDivElement>(null);

  // API Base URL
  const API_BASE = 'http://localhost:8000';

  // Check auth on mount
  useEffect(() => {
    const currentUser = localStorage.getItem('jarvis-current-user');
    if (currentUser) {
      setUser(currentUser);
    }
    setAuthLoading(false);
  }, []);

  // Login handler
  const handleLogin = (username: string) => {
    setUser(username);
  };



  // Close model picker on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modelPickerRef.current && !modelPickerRef.current.contains(event.target as Node)) {
        setShowModelPicker(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Check backend connection
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/health`);
        setIsConnected(response.ok);
      } catch {
        setIsConnected(false);
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 10000);
    return () => clearInterval(interval);
  }, []);

  // Load sessions from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('jarvis-sessions');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSessions(parsed.map((s: ChatSession) => ({
          ...s,
          createdAt: new Date(s.createdAt),
          updatedAt: new Date(s.updatedAt),
          messages: s.messages.map(m => ({ ...m, timestamp: new Date(m.timestamp) }))
        })));
      } catch (e) {
        console.error('Failed to load sessions', e);
      }
    }
  }, []);

  // Save sessions to localStorage
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem('jarvis-sessions', JSON.stringify(sessions));
    }
  }, [sessions]);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentSteps]);

  // Setup WebSocket
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(`ws://localhost:8000/ws`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'step') {
          setCurrentSteps(prev => [...prev, data.step]);
        } else if (data.type === 'response') {
          setIsLoading(false);
          setCurrentSteps([]);

          const assistantMsg: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.content,
            timestamp: new Date(),
            steps: data.steps
          };

          setMessages(prev => [...prev, assistantMsg]);

          // Speak response if voice enabled
          if (settings.voiceEnabled && data.content) {
            speakText(data.content);
          }

          // Persist to session
          setSessions(prev => prev.map(s => {
            if (s.id === activeSessionIdRef.current) {
              return {
                ...s,
                messages: [...s.messages, assistantMsg],
                updatedAt: new Date()
              };
            }
            return s;
          }));
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Attempt reconnection after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = () => {
        setIsConnected(false);
      };

      wsRef.current = ws;
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Generate title from first message using AI
  const generateTitle = async (messageContent: string): Promise<string> => {
    try {
      const response = await fetch(`${API_BASE}/api/chat/title`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageContent })
      });

      if (response.ok) {
        const data = await response.json();
        return data.title || messageContent.slice(0, 30);
      }
    } catch (e) {
      console.error('Failed to generate title', e);
    }
    return messageContent.slice(0, 30);
  };

  // Create new chat session
  const createNewSession = useCallback(() => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      pinned: false
    };
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setMessages([]);
    setCurrentSteps([]);
    setInput('');

    // Focus input after creating new chat
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  // Select session - Fixed to properly reset state
  const selectSession = useCallback((sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setActiveSessionId(sessionId);
      setMessages([...session.messages]); // Create new array to trigger re-render
      setCurrentSteps([]);
      setInput('');
      setIsLoading(false);

      // Focus input after switching chat
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [sessions]);

  // Delete session
  const deleteSession = useCallback((sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (activeSessionId === sessionId) {
      setActiveSessionId(null);
      setMessages([]);
      setCurrentSteps([]);
    }
  }, [activeSessionId]);

  // Pin/unpin session
  const pinSession = useCallback((sessionId: string) => {
    setSessions(prev => prev.map(s => {
      if (s.id === sessionId) {
      }
      return s;
    }));
  }, []);

  // Rename session
  const renameSession = useCallback((sessionId: string, newTitle: string) => {
    setSessions(prev => prev.map(s => {
      if (s.id === sessionId) {
        return { ...s, title: newTitle };
      }
      return s;
    }));
  }, []);



  // Update session with new messages and auto-generate title
  const updateSession = useCallback(async (msgs: Message[], isNewMessage: boolean = false) => {
    if (!activeSessionId) return;

    let newTitle = msgs[0]?.content.slice(0, 30) || 'New Chat';

    // Generate AI title for first message only
    if (isNewMessage && msgs.length === 1) {
      newTitle = await generateTitle(msgs[0].content);
    }

    setSessions(prev => prev.map(s => {
      if (s.id === activeSessionId) {
        return {
          ...s,
          messages: msgs,
          title: msgs.length === 1 ? newTitle : s.title,
          updatedAt: new Date()
        };
      }
      return s;
    }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSessionId]);

  // Effect to handle True Jarvis mode visual theme
  useEffect(() => {
    if (settings.mode === 'true_jarvis') {
      document.body.classList.add('true-jarvis-mode');
    } else {
      document.body.classList.remove('true-jarvis-mode');
    }
  }, [settings.mode]);

  // Send message
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    // Create session if none exists
    let currentSessionId = activeSessionId;
    if (!currentSessionId) {
      const newSession: ChatSession = {
        id: Date.now().toString(),
        title: 'New Chat',
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        pinned: false
      };
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      currentSessionId = newSession.id;
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    await updateSession(newMessages, messages.length === 0);
    setInput('');
    setIsLoading(true);
    setCurrentSteps([]);

    // Send via WebSocket if connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'message',
        content: input.trim(),
        settings: settings
      }));
    } else {
      // Fallback to HTTP
      try {
        const response = await fetch(`${API_BASE}/api/chat/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: input.trim(),
            provider: settings.provider,
            model: settings.model
          })
        });

        const data = await response.json();

        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response || data.message || 'No response',
          timestamp: new Date(),
          steps: data.steps
        };

        const updatedMessages = [...newMessages, assistantMsg];
        setMessages(updatedMessages);
        await updateSession(updatedMessages);

        if (settings.voiceEnabled && assistantMsg.content) {
          speakText(assistantMsg.content);
        }
      } catch (error) {
        console.error('Chat error:', error);
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Connection error. Please check if the backend is running.',
          timestamp: new Date()
        }]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  // Voice input
  const toggleListening = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = settings.appLanguage === 'fr' ? 'fr-FR' : 'en-US';

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };

      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);

      recognition.start();
      recognitionRef.current = recognition;
      setIsListening(true);
    }
  };

  // Text-to-speech
  const speakText = async (text: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/voice/synthesize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          voice: settings.voice,
          rate: settings.voiceRate,
          pitch: settings.voicePitch
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const audio = new Audio(URL.createObjectURL(blob));
        audio.play();
      }
    } catch (error) {
      console.error('TTS error:', error);
    }
  };

  // Handle keyboard
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Get greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  // Change model
  const selectModel = (provider: typeof settings.provider, model: string) => {
    setSettings(prev => ({ ...prev, provider, model }));
    setShowModelPicker(false);
  };

  return (
    <>
      {/* Auth loading state */}
      {authLoading && (
        <div className="app loading-container">
          <div className="loading-indicator">Loading...</div>
        </div>
      )}

      {/* Login Page */}
      {!authLoading && !user && (
        <LoginPage onLogin={handleLogin} />
      )}

      {/* Main App */}
      {!authLoading && user && (
        <div className="app">
          {/* Sidebar */}
          <Sidebar
            isOpen={sidebarOpen}
            sessions={sessions}
            activeSessionId={activeSessionId}
            onNewChat={createNewSession}
            onSelectSession={selectSession}
            onDeleteSession={deleteSession}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            onOpenSettings={() => setShowSettings(true)}
            onPinSession={pinSession}
            onRenameSession={renameSession}
            onOpenChangelog={() => setShowChangelog(true)}
          />

          {/* Main Content */}
          <main className={`main-content ${sidebarOpen ? '' : 'expanded'}`}>
            {showChangelog && <Changelog onClose={() => setShowChangelog(false)} />}
            {/* Header */}
            <header className="header">
              <button
                className="menu-btn"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                title="Toggle sidebar"
                aria-label="Toggle sidebar"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 12h18M3 6h18M3 18h18" />
                </svg>
              </button>

              {/* ChatGPT-style Model Picker */}
              <div className="model-picker-container" ref={modelPickerRef}>
                <button
                  className="model-picker-btn"
                  onClick={() => setShowModelPicker(!showModelPicker)}
                  title="Select model"
                  aria-label="Select AI model"
                  aria-expanded={showModelPicker ? 'true' : 'false'}
                >
                  <span className="model-name">JARVIS</span>
                  <span className="model-version">{settings.model.split('-').slice(0, 2).join('-')}</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {showModelPicker && (
                  <div className="model-picker-dropdown">
                    {Object.entries(MODELS).map(([provider, data]) => (
                      <div key={provider} className="model-group">
                        <div className="model-group-header">
                          <span className="provider-name">{provider.toUpperCase()}</span>
                          <span className="provider-desc">{data.description}</span>
                        </div>
                        {data.models.map(model => (
                          <button
                            key={model}
                            className={`model-option ${settings.provider === provider && settings.model === model ? 'active' : ''}`}
                            onClick={() => selectModel(provider as typeof settings.provider, model)}
                          >
                            <span className="model-label">{model}</span>
                            {settings.provider === provider && settings.model === model && (
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                              </svg>
                            )}
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="header-right">
                <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} title={isConnected ? 'Connected' : 'Disconnected'} />
                <button
                  className="settings-btn"
                  onClick={() => setShowSettings(true)}
                  title="Open settings"
                  aria-label="Open settings"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
                  </svg>
                </button>
              </div>
            </header>

            {/* Chat Area */}
            <div className="chat-area">
              {messages.length === 0 ? (
                <div className="welcome-screen">
                  <div className="welcome-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <circle cx="12" cy="12" r="10" />
                      <circle cx="12" cy="12" r="4" />
                      <line x1="12" y1="2" x2="12" y2="6" />
                      <line x1="12" y1="18" x2="12" y2="22" />
                      <line x1="2" y1="12" x2="6" y2="12" />
                      <line x1="18" y1="12" x2="22" y2="12" />
                    </svg>
                  </div>
                  <h1>{getGreeting()}, sir.</h1>
                  <p>How may I assist you today?</p>

                  <div className="quick-actions">
                    <button onClick={() => setInput('What can you do?')}>
                      What can you do?
                    </button>
                    <button onClick={() => setInput('Open Chrome')}>
                      Open Chrome
                    </button>
                    <button onClick={() => setInput('What time is it?')}>
                      Current time
                    </button>
                    <button onClick={() => setInput('Search for AI news')}>
                      Search the web
                    </button>
                  </div>
                </div>
              ) : (
                <div className="messages messages-container">
                  <Virtuoso
                    className="virtuoso-scroll"
                    data={messages}
                    followOutput="auto"
                    ref={virtuosoRef}
                    initialTopMostItemIndex={messages.length - 1}
                    itemContent={(_, msg) => (
                      <div className="message-spacer">
                        <ChatMessage key={msg.id} message={msg} />
                      </div>
                    )}
                    components={{
                      Footer: () => (
                        <>
                          {/* Live Steps */}
                          {currentSteps.length > 0 && (
                            <StepVisualizer steps={currentSteps} isLive={true} />
                          )}

                          {/* Loading */}
                          {isLoading && currentSteps.length === 0 && (
                            <div className="message assistant loading">
                              <div className="typing-indicator">
                                <span></span><span></span><span></span>
                              </div>
                            </div>
                          )}
                          <div className="bottom-spacer" />
                        </>
                      )
                    }}
                  />
                </div>
              )}
            </div>

            {/* Input Area - ChatGPT Style */}
            <div className="input-area">
              <div className="input-container">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Message Jarvis..."
                  rows={1}
                  disabled={isLoading}
                  aria-label="Message input"
                />

                <div className="input-actions">
                  <button
                    className={`voice-btn ${isListening ? 'listening' : ''}`}
                    onClick={toggleListening}
                    title={isListening ? 'Stop listening' : 'Voice input'}
                    aria-label={isListening ? 'Stop listening' : 'Voice input'}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                      <line x1="12" y1="19" x2="12" y2="23" />
                      <line x1="8" y1="23" x2="16" y2="23" />
                    </svg>
                  </button>

                  <button
                    className="send-btn"
                    onClick={sendMessage}
                    disabled={!input.trim() || isLoading}
                    title="Send message"
                    aria-label="Send message"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="22" y1="2" x2="11" y2="13" />
                      <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                  </button>
                </div>
              </div>

              <p className="input-hint">
                Jarvis can make mistakes. Verify important information.
              </p>
            </div>
          </main >

          {/* Settings Panel */}
          {
            showSettings && (
              <SettingsPanel
                settings={settings}
                onClose={() => setShowSettings(false)}
                onSave={setSettings}
                isConnected={isConnected}
              />
            )
          }
        </div >
      )
      }
    </>
  );
}

export default App;
