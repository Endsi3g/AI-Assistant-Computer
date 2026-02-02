import { useState } from 'react';
import './Changelog.css';

interface Version {
    version: string;
    date: string;
    features: string[];
    improvements: string[];
    fixes?: string[];
}

const changelogData: Version[] = [
    {
        version: "1.1.0",
        date: "2026-02-01",
        features: [
            "Dynamic Tool Creation: The AI can now create its own Python tools at runtime.",
            "Conversation Management: Auto-generated titles and manual renaming.",
            "True Jarvis Mode: Full system control via Sidebar settings."
        ],
        improvements: [
            "Enhanced sidebar with edit/pin support.",
            "Integrated Perplexity backend for web search.",
            "Improved memory system with summarization."
        ],
        fixes: [
            "Fixed WebSocket connection stability.",
            "Resolved build errors in frontend components.",
            "Visual polish for chat interface."
        ]
    },
    {
        version: "1.0.0",
        date: "2026-01-20",
        features: [
            "Initial Release",
            "Basic Chat Interface",
            "Local LLM Support (Ollama)",
            "System Monitoring"
        ],
        improvements: []
    }
];

interface ChangelogProps {
    onClose: () => void;
}

export default function Changelog({ onClose }: ChangelogProps) {
    return (
        <div className="changelog-overlay" onClick={onClose}>
            <div className="changelog-modal" onClick={e => e.stopPropagation()}>
                <div className="changelog-header">
                    <h2>Changelog & Updates</h2>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>

                <div className="changelog-content">
                    {changelogData.map((version, index) => (
                        <div key={index} className="version-entry">
                            <div className="version-header">
                                <span className="version-tag">v{version.version}</span>
                                <span className="version-date">{version.date}</span>
                            </div>

                            <div className="version-sections">
                                {version.features.length > 0 && (
                                    <div className="section features">
                                        <h4>✨ New Features</h4>
                                        <ul>
                                            {version.features.map((f, i) => <li key={i}>{f}</li>)}
                                        </ul>
                                    </div>
                                )}

                                {version.improvements.length > 0 && (
                                    <div className="section improvements">
                                        <h4>🚀 Improvements</h4>
                                        <ul>
                                            {version.improvements.map((f, i) => <li key={i}>{f}</li>)}
                                        </ul>
                                    </div>
                                )}

                                {version.fixes && version.fixes.length > 0 && (
                                    <div className="section fixes">
                                        <h4>🐛 Bug Fixes</h4>
                                        <ul>
                                            {version.fixes.map((f, i) => <li key={i}>{f}</li>)}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="changelog-footer">
                    <p>Jarvis is constantly evolving. Use <strong>True Jarvis Mode</strong> for advanced capabilities.</p>
                </div>
            </div>
        </div>
    );
}
