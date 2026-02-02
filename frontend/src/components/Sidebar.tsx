import { useState } from 'react';
import RenameModal from './RenameModal';
import './Sidebar.css';

interface ChatSession {
    id: string;
    title: string;
    createdAt: Date;
    updatedAt: Date;
    pinned?: boolean;
}

interface SidebarProps {
    isOpen: boolean;
    sessions: ChatSession[];
    activeSessionId: string | null;
    onNewChat: () => void;
    onSelectSession: (id: string) => void;
    onDeleteSession: (id: string) => void;
    onToggle: () => void;
    onOpenSettings: () => void;
    onPinSession?: (id: string) => void;
    onOpenDocs?: () => void;
    onRenameSession?: (id: string, newTitle: string) => void;
    onOpenChangelog?: () => void;
}

function Sidebar({
    isOpen,
    sessions,
    activeSessionId,
    onNewChat,
    onSelectSession,
    onDeleteSession,
    onOpenSettings,
    onPinSession,
    onOpenDocs,
    onRenameSession,
    onOpenChangelog
}: SidebarProps) {
    const [showDocs, setShowDocs] = useState(false);
    const [renameSessionId, setRenameSessionId] = useState<string | null>(null);
    const [renameModalOpen, setRenameModalOpen] = useState(false);

    // Find session title for rename modal
    const sessionToRename = sessions.find(s => s.id === renameSessionId);

    const formatDate = (date: Date) => {
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) return 'Today';
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;
        return date.toLocaleDateString();
    };

    // Separate pinned and regular sessions
    const pinnedSessions = sessions.filter(s => s.pinned);
    const regularSessions = sessions.filter(s => !s.pinned);

    // Group sessions by date
    const groupedSessions = regularSessions.reduce((groups: Record<string, ChatSession[]>, session) => {
        const dateKey = formatDate(session.updatedAt);
        if (!groups[dateKey]) groups[dateKey] = [];
        groups[dateKey].push(session);
        return groups;
    }, {});

    const handlePinClick = (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        onPinSession?.(sessionId);
    };

    const toggleDocs = () => {
        if (onOpenDocs) {
            onOpenDocs();
        } else {
            setShowDocs(!showDocs);
        }
    };

    return (
        <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
            <div className="sidebar-header">
                <button className="new-chat-btn" onClick={onNewChat} title="Start new chat" aria-label="Start new chat">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    <span>New chat</span>
                </button>
            </div>

            <div className="sidebar-content">
                {/* Pinned Chats Section */}
                {pinnedSessions.length > 0 && (
                    <div className="session-group pinned-group">
                        <div className="session-group-title">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M16 9V4h1c.55 0 1-.45 1-1s-.45-1-1-1H7c-.55 0-1 .45-1 1s.45 1 1 1h1v5c0 1.66-1.34 3-3 3h-.5v2h5.5v7h2v-7h5.5v-2H17c-1.66 0-3-1.34-3-3z" />
                            </svg>
                            Pinned
                        </div>
                        {pinnedSessions.map((session) => (
                            <div
                                key={session.id}
                                className={`session-item ${session.id === activeSessionId ? 'active' : ''}`}
                                onClick={() => onSelectSession(session.id)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(e) => e.key === 'Enter' && onSelectSession(session.id)}
                            >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                                </svg>
                                <span className="session-title">{session.title || 'New Chat'}</span>
                                <div className="session-actions">
                                    <button
                                        className="pin-btn pinned"
                                        onClick={(e) => handlePinClick(e, session.id)}
                                        title="Unpin chat"
                                        aria-label="Unpin chat"
                                    >
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M16 9V4h1c.55 0 1-.45 1-1s-.45-1-1-1H7c-.55 0-1 .45-1 1s.45 1 1 1h1v5c0 1.66-1.34 3-3 3h-.5v2h5.5v7h2v-7h5.5v-2H17c-1.66 0-3-1.34-3-3z" />
                                        </svg>
                                    </button>
                                    <button
                                        className="edit-btn"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setRenameSessionId(session.id);
                                            setRenameModalOpen(true);
                                        }}
                                        title="Rename chat"
                                        aria-label="Rename chat"
                                    >
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                                        </svg>
                                    </button>
                                    <button
                                        className="delete-btn"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onDeleteSession(session.id);
                                        }}
                                        title="Delete chat"
                                        aria-label="Delete chat"
                                    >
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <polyline points="3 6 5 6 21 6" />
                                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Regular Session Groups */}
                {Object.entries(groupedSessions).map(([dateKey, dateSessions]) => (
                    <div key={dateKey} className="session-group">
                        <div className="session-group-title">{dateKey}</div>
                        {dateSessions.map((session) => (
                            <div
                                key={session.id}
                                className={`session-item ${session.id === activeSessionId ? 'active' : ''}`}
                                onClick={() => onSelectSession(session.id)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(e) => e.key === 'Enter' && onSelectSession(session.id)}
                            >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                                </svg>
                                <span className="session-title">{session.title || 'New Chat'}</span>
                                <div className="session-actions">
                                    <button
                                        className="pin-btn"
                                        onClick={(e) => handlePinClick(e, session.id)}
                                        title="Pin chat"
                                        aria-label="Pin chat"
                                    >
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M16 9V4h1c.55 0 1-.45 1-1s-.45-1-1-1H7c-.55 0-1 .45-1 1s.45 1 1 1h1v5c0 1.66-1.34 3-3 3h-.5v2h5.5v7h2v-7h5.5v-2H17c-1.66 0-3-1.34-3-3z" />
                                        </svg>
                                    </button>
                                    <button
                                        className="edit-btn"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setRenameSessionId(session.id);
                                            setRenameModalOpen(true);
                                        }}
                                        title="Rename chat"
                                        aria-label="Rename chat"
                                    >
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                                        </svg>
                                    </button>
                                    <button
                                        className="delete-btn"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onDeleteSession(session.id);
                                        }}
                                        title="Delete chat"
                                        aria-label="Delete chat"
                                    >
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <polyline points="3 6 5 6 21 6" />
                                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                ))}

                {sessions.length === 0 && (
                    <div className="empty-sessions">
                        <p>No conversations yet</p>
                        <p>Start a new chat to begin</p>
                    </div>
                )}
            </div>

            <div className="sidebar-footer">
                {/* Docs Button - Above Settings */}
                <button className="footer-btn" onClick={toggleDocs} title="View documentation" aria-label="View documentation">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                        <polyline points="10 9 9 9 8 9" />
                    </svg>
                    <span>Docs</span>
                </button>

                {/* Settings Button */}
                <button className="footer-btn" onClick={onOpenSettings} title="Open settings" aria-label="Open settings">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="3" />
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                    </svg>
                    <span>Settings</span>
                </button>
            </div>

            {/* Inline Docs Panel */}
            {showDocs && (
                <div className="docs-panel">
                    <div className="docs-header">
                        <h3>Documentation</h3>
                        <button onClick={() => setShowDocs(false)} title="Close docs" aria-label="Close documentation">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <line x1="18" y1="6" x2="6" y2="18" />
                                <line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                        </button>
                    </div>
                    {/* Docs content */}
                </div>
            )}

            {/* Rename Modal */}
            <RenameModal
                isOpen={renameModalOpen}
                initialTitle={sessionToRename?.title || ''}
                onClose={() => setRenameModalOpen(false)}
                onSave={(newTitle) => {
                    if (renameSessionId && onRenameSession) {
                        onRenameSession(renameSessionId, newTitle);
                    }
                    setRenameModalOpen(false);
                }}
            />
        </aside>
    );
}

export default Sidebar;
