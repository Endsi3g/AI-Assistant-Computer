import React, { memo } from 'react';
import './ChatMessage.css';

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
    duration_ms?: number;
}

interface ChatMessageProps {
    message: Message;
}

const ChatMessage = memo(({ message }: ChatMessageProps) => {
    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const renderContent = (content: string) => {
        // Simple markdown-like rendering
        const lines = content.split('\n');
        const elements: React.JSX.Element[] = [];
        let inCodeBlock = false;
        let codeContent = '';
        let codeLanguage = '';

        lines.forEach((line, index) => {
            if (line.startsWith('```')) {
                if (inCodeBlock) {
                    // End code block
                    elements.push(
                        <div key={`code-${index}`} className="code-block">
                            {codeLanguage && <div className="code-lang">{codeLanguage}</div>}
                            <pre><code>{codeContent.trim()}</code></pre>
                            <button
                                className="copy-btn"
                                onClick={() => navigator.clipboard.writeText(codeContent.trim())}
                            >
                                Copy
                            </button>
                        </div>
                    );
                    codeContent = '';
                    codeLanguage = '';
                    inCodeBlock = false;
                } else {
                    // Start code block
                    codeLanguage = line.slice(3);
                    inCodeBlock = true;
                }
            } else if (inCodeBlock) {
                codeContent += line + '\n';
            } else if (line.startsWith('# ')) {
                elements.push(<h1 key={index}>{line.slice(2)}</h1>);
            } else if (line.startsWith('## ')) {
                elements.push(<h2 key={index}>{line.slice(3)}</h2>);
            } else if (line.startsWith('### ')) {
                elements.push(<h3 key={index}>{line.slice(4)}</h3>);
            } else if (line.startsWith('- ') || line.startsWith('* ')) {
                elements.push(<li key={index}>{renderInline(line.slice(2))}</li>);
            } else if (line.match(/^\d+\. /)) {
                elements.push(<li key={index}>{renderInline(line.replace(/^\d+\. /, ''))}</li>);
            } else if (line.trim() === '') {
                elements.push(<br key={index} />);
            } else {
                elements.push(<p key={index}>{renderInline(line)}</p>);
            }
        });

        return elements;
    };

    const renderInline = (text: string) => {
        // Bold, italic, code
        return text
            .split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g)
            .map((part, i) => {
                if (part.startsWith('**') && part.endsWith('**')) {
                    return <strong key={i}>{part.slice(2, -2)}</strong>;
                }
                if (part.startsWith('*') && part.endsWith('*')) {
                    return <em key={i}>{part.slice(1, -1)}</em>;
                }
                if (part.startsWith('`') && part.endsWith('`')) {
                    return <code key={i} className="inline-code">{part.slice(1, -1)}</code>;
                }
                return part;
            });
    };

    return (
        <div className={`message ${message.role}`}>
            <div className="message-avatar">
                {message.role === 'user' ? (
                    <div className="avatar user-avatar">U</div>
                ) : (
                    <div className="avatar assistant-avatar">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                            <circle cx="12" cy="12" r="4" />
                            <line x1="12" y1="2" x2="12" y2="6" />
                            <line x1="12" y1="18" x2="12" y2="22" />
                            <line x1="2" y1="12" x2="6" y2="12" />
                            <line x1="18" y1="12" x2="22" y2="12" />
                        </svg>
                    </div>
                )}
            </div>

            <div className="message-content">
                <div className="message-header">
                    <span className="message-author">
                        {message.role === 'user' ? 'You' : 'Jarvis'}
                    </span>
                    <span className="message-time">{formatTime(message.timestamp)}</span>
                </div>

                <div className="message-body">
                    {renderContent(message.content)}
                </div>

                {/* Tool calls summary */}
                {message.steps && message.steps.length > 0 && (
                    <div className="steps-summary">
                        <details>
                            <summary>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                                </svg>
                                {message.steps.filter(s => s.type === 'tool_call').length} tools used
                            </summary>
                            <div className="steps-list">
                                {message.steps
                                    .filter(s => s.type === 'tool_call')
                                    .map((step) => (
                                        <div key={step.id} className="step-item">
                                            <span className="step-tool">{step.tool_name}</span>
                                            {step.duration_ms && (
                                                <span className="step-duration">{step.duration_ms}ms</span>
                                            )}
                                        </div>
                                    ))}
                            </div>
                        </details>
                    </div>
                )}
            </div>
        </div>
    );
}, (prevProps, nextProps) => {
    // Custom comparison to prevent re-renders unless message content/steps changes
    return prevProps.message.id === nextProps.message.id &&
        prevProps.message.content === nextProps.message.content &&
        (prevProps.message.steps?.length ?? 0) === (nextProps.message.steps?.length ?? 0);
});

export default ChatMessage;
