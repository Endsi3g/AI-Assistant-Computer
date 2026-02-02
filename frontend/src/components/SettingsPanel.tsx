import { useState, useEffect } from 'react';
import './SettingsPanel.css';

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

interface SettingsPanelProps {
    settings: Settings;
    onClose: () => void;
    onSave: (settings: Settings) => void;
    isConnected: boolean;
}

const MODELS: Record<string, string[]> = {
    ollama: ['llama3.2', 'llama3.1', 'codellama', 'mistral', 'mixtral', 'deepseek-coder', 'phi3'],
    groq: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'llama-3.1-70b-versatile', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
    openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
    perplexity: ['sonar-pro', 'sonar', 'sonar-reasoning-pro', 'sonar-reasoning']
};

const VOICES = [
    { id: 'en-GB-RyanNeural', name: 'Ryan (British Male)', lang: 'en' },
    { id: 'en-GB-SoniaNeural', name: 'Sonia (British Female)', lang: 'en' },
    { id: 'en-US-GuyNeural', name: 'Guy (American Male)', lang: 'en' },
    { id: 'en-US-JennyNeural', name: 'Jenny (American Female)', lang: 'en' },
    { id: 'en-AU-WilliamNeural', name: 'William (Australian Male)', lang: 'en' },
    { id: 'fr-FR-HenriNeural', name: 'Henri (French Male)', lang: 'fr' },
    { id: 'fr-FR-DeniseNeural', name: 'Denise (French Female)', lang: 'fr' },
    { id: 'es-ES-AlvaroNeural', name: 'Alvaro (Spanish Male)', lang: 'es' },
    { id: 'de-DE-ConradNeural', name: 'Conrad (German Male)', lang: 'de' },
];

const LANGUAGES = [
    { id: 'en', name: 'English' },
    { id: 'fr', name: 'Français' },
    { id: 'es', name: 'Español' },
    { id: 'de', name: 'Deutsch' },
];

const VOICE_RATES = [
    { id: '-20%', name: 'Very Slow' },
    { id: '-10%', name: 'Slow' },
    { id: '+0%', name: 'Normal' },
    { id: '+5%', name: 'Slightly Fast' },
    { id: '+10%', name: 'Fast' },
    { id: '+20%', name: 'Very Fast' },
];

const VOICE_PITCHES = [
    { id: '-10Hz', name: 'Lower' },
    { id: '+0Hz', name: 'Normal' },
    { id: '+10Hz', name: 'Higher' },
];

function SettingsPanel({ settings, onClose, onSave, isConnected }: SettingsPanelProps) {
    const [localSettings, setLocalSettings] = useState<Settings>(settings);
    const [activeTab, setActiveTab] = useState<'general' | 'voice' | 'advanced'>('general');
    const [ollamaStatus, setOllamaStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
    const [ollamaModels, setOllamaModels] = useState<string[]>([]);

    // Check Ollama connection and get models
    useEffect(() => {
        const checkOllama = async () => {
            try {
                const response = await fetch('http://localhost:11434/api/tags');
                if (response.ok) {
                    const data = await response.json();
                    setOllamaStatus('connected');
                    // Extract model names from Ollama response
                    if (data.models && Array.isArray(data.models)) {
                        setOllamaModels(data.models.map((m: { name: string }) => m.name));
                    }
                } else {
                    setOllamaStatus('disconnected');
                }
            } catch {
                setOllamaStatus('disconnected');
            }
        };

        checkOllama();
    }, []);

    const handleSave = () => {
        onSave(localSettings);
        onClose();
    };

    // Get available models for current provider
    const getModels = () => {
        if (localSettings.provider === 'ollama' && ollamaModels.length > 0) {
            return ollamaModels;
        }
        return MODELS[localSettings.provider] || [];
    };

    // Filter voices by language
    const getVoices = () => {
        return VOICES.filter(v => v.lang === localSettings.appLanguage || localSettings.appLanguage === 'en');
    };

    return (
        <div className="settings-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="settings-title">
            <div className="settings-panel" onClick={(e) => e.stopPropagation()}>
                <div className="settings-header">
                    <h2 id="settings-title">Settings</h2>
                    <button className="close-btn" onClick={onClose} title="Close settings" aria-label="Close settings">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="18" y1="6" x2="6" y2="18" />
                            <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                    </button>
                </div>

                <div className="settings-tabs">
                    <button
                        className={activeTab === 'general' ? 'active' : ''}
                        onClick={() => setActiveTab('general')}
                    >
                        General
                    </button>
                    <button
                        className={activeTab === 'voice' ? 'active' : ''}
                        onClick={() => setActiveTab('voice')}
                    >
                        Voice
                    </button>
                    <button
                        className={activeTab === 'advanced' ? 'active' : ''}
                        onClick={() => setActiveTab('advanced')}
                    >
                        Advanced
                    </button>
                </div>

                <div className="settings-content">
                    {activeTab === 'general' && (
                        <div className="settings-section">
                            <div className="setting-group">
                                <label>AI Provider</label>
                                <div className="provider-options">
                                    <button
                                        className={`provider-btn ${localSettings.provider === 'ollama' ? 'active' : ''}`}
                                        onClick={() => setLocalSettings(s => ({ ...s, provider: 'ollama', model: ollamaModels[0] || MODELS.ollama[0] }))}
                                    >
                                        <div className="provider-icon">O</div>
                                        <div className="provider-info">
                                            <span>Ollama</span>
                                            <small>Self-hosted</small>
                                        </div>
                                        {localSettings.provider === 'ollama' && (
                                            <span className={`status-badge ${ollamaStatus}`}>
                                                {ollamaStatus === 'connected' ? 'Connected' : ollamaStatus === 'disconnected' ? 'Offline' : 'Checking'}
                                            </span>
                                        )}
                                    </button>

                                    <button
                                        className={`provider-btn ${localSettings.provider === 'groq' ? 'active' : ''}`}
                                        onClick={() => setLocalSettings(s => ({ ...s, provider: 'groq', model: MODELS.groq[0] }))}
                                    >
                                        <div className="provider-icon">G</div>
                                        <div className="provider-info">
                                            <span>Groq</span>
                                            <small>Fast cloud</small>
                                        </div>
                                    </button>

                                    <button
                                        className={`provider-btn ${localSettings.provider === 'openai' ? 'active' : ''}`}
                                        onClick={() => setLocalSettings(s => ({ ...s, provider: 'openai', model: MODELS.openai[0] }))}
                                    >
                                        <div className="provider-icon">AI</div>
                                        <div className="provider-info">
                                            <span>OpenAI</span>
                                            <small>GPT-4</small>
                                        </div>
                                    </button>

                                    <button
                                        className={`provider-btn ${localSettings.provider === 'perplexity' ? 'active' : ''}`}
                                        onClick={() => setLocalSettings(s => ({ ...s, provider: 'perplexity', model: MODELS.perplexity[0] }))}
                                    >
                                        <div className="provider-icon">P</div>
                                        <div className="provider-info">
                                            <span>Perplexity</span>
                                            <small>Search AI</small>
                                        </div>
                                    </button>
                                </div>
                            </div>

                            <div className="setting-group">
                                <label>Mode</label>
                                <div className="mode-options">
                                    <button
                                        className={`mode-btn ${localSettings.mode === 'standard' ? 'active' : ''}`}
                                        onClick={() => setLocalSettings(s => ({ ...s, mode: 'standard' }))}
                                        title="Standard AI assistant mode"
                                    >
                                        <div className="mode-icon">🛡️</div>
                                        <div className="mode-info">
                                            <span>Standard</span>
                                            <small>Safe, restricted access</small>
                                        </div>
                                    </button>

                                    <button
                                        className={`mode-btn ${localSettings.mode === 'true_jarvis' ? 'active danger' : ''}`}
                                        onClick={() => setLocalSettings(s => ({ ...s, mode: 'true_jarvis' }))}
                                        title="Full autonomous system control"
                                    >
                                        <div className="mode-icon">⚡</div>
                                        <div className="mode-info">
                                            <span>True Jarvis</span>
                                            <small>Full system control</small>
                                        </div>
                                    </button>
                                </div>
                                {localSettings.mode === 'true_jarvis' && (
                                    <div className="warning-box">
                                        ⚠️ <strong>Warning:</strong> True Jarvis mode allows the AI to execute commands, modify files, and control applications without explicit confirmation. Use with caution.
                                    </div>
                                )}
                            </div>

                            <div className="setting-group">
                                <label htmlFor="model-select">Model</label>
                                <select
                                    id="model-select"
                                    value={localSettings.model}
                                    onChange={(e) => setLocalSettings(s => ({ ...s, model: e.target.value }))}
                                    title="Select AI model"
                                >
                                    {getModels().map((model) => (
                                        <option key={model} value={model}>{model}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="setting-group">
                                <label htmlFor="language-select">App Language</label>
                                <select
                                    id="language-select"
                                    value={localSettings.appLanguage}
                                    onChange={(e) => setLocalSettings(s => ({ ...s, appLanguage: e.target.value }))}
                                    title="Select app language"
                                >
                                    {LANGUAGES.map((lang) => (
                                        <option key={lang.id} value={lang.id}>{lang.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="setting-group">
                                <label>Backend Status</label>
                                <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
                                    <span className="status-dot"></span>
                                    {isConnected ? 'Connected to Jarvis Backend' : 'Backend Offline'}
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'voice' && (
                        <div className="settings-section">
                            <div className="setting-group">
                                <label className="toggle-label">
                                    <span>Enable Voice Output</span>
                                    <input
                                        type="checkbox"
                                        checked={localSettings.voiceEnabled}
                                        onChange={(e) => setLocalSettings(s => ({ ...s, voiceEnabled: e.target.checked }))}
                                    />
                                    <span className="toggle-switch"></span>
                                </label>
                            </div>

                            <div className="setting-group">
                                <label htmlFor="voice-select">Voice</label>
                                <select
                                    id="voice-select"
                                    value={localSettings.voice}
                                    onChange={(e) => setLocalSettings(s => ({ ...s, voice: e.target.value }))}
                                    disabled={!localSettings.voiceEnabled}
                                    title="Select voice"
                                >
                                    {getVoices().map((voice) => (
                                        <option key={voice.id} value={voice.id}>{voice.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="setting-group">
                                <label htmlFor="rate-select">Speech Rate</label>
                                <select
                                    id="rate-select"
                                    value={localSettings.voiceRate}
                                    onChange={(e) => setLocalSettings(s => ({ ...s, voiceRate: e.target.value }))}
                                    disabled={!localSettings.voiceEnabled}
                                    title="Select speech rate"
                                >
                                    {VOICE_RATES.map((rate) => (
                                        <option key={rate.id} value={rate.id}>{rate.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="setting-group">
                                <label htmlFor="pitch-select">Voice Pitch</label>
                                <select
                                    id="pitch-select"
                                    value={localSettings.voicePitch}
                                    onChange={(e) => setLocalSettings(s => ({ ...s, voicePitch: e.target.value }))}
                                    disabled={!localSettings.voiceEnabled}
                                    title="Select voice pitch"
                                >
                                    {VOICE_PITCHES.map((pitch) => (
                                        <option key={pitch.id} value={pitch.id}>{pitch.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="setting-info">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10" />
                                    <path d="M12 16v-4M12 8h.01" />
                                </svg>
                                <span>Voice output uses Edge-TTS for natural speech synthesis</span>
                            </div>
                        </div>
                    )}

                    {activeTab === 'advanced' && (
                        <div className="settings-section">
                            <div className="setting-group">
                                <label htmlFor="ollama-url">Ollama URL</label>
                                <input id="ollama-url" type="text" defaultValue="http://localhost:11434" disabled placeholder="Ollama server URL" title="Ollama server URL" />
                                <small>Configure in .env file</small>
                            </div>

                            <div className="setting-group">
                                <label htmlFor="max-steps">Max Agent Steps</label>
                                <input id="max-steps" type="number" defaultValue={50} disabled placeholder="Maximum steps" title="Maximum agent steps per task" />
                                <small>Maximum steps per task</small>
                            </div>

                            <div className="setting-group">
                                <label>Docker Sandbox</label>
                                <div className="status-indicator disconnected">
                                    <span className="status-dot"></span>
                                    Not configured
                                </div>
                                <small>For secure Python/terminal execution</small>
                            </div>

                            <div className="setting-group">
                                <button className="danger-btn">Clear All Data</button>
                                <small>Delete all chat history and preferences</small>
                            </div>
                        </div>
                    )}
                </div>

                <div className="settings-footer">
                    <button className="cancel-btn" onClick={onClose}>Cancel</button>
                    <button className="save-btn" onClick={handleSave}>Save Changes</button>
                </div>
            </div>
        </div>
    );
}

export default SettingsPanel;
