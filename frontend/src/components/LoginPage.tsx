import { useState } from 'react';
import './LoginPage.css';

interface LoginPageProps {
    onLogin: (username: string) => void;
}

function LoginPage({ onLogin }: LoginPageProps) {
    const [mode, setMode] = useState<'signin' | 'create'>('signin');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!username.trim() || !password.trim()) {
            setError('Please fill in all fields');
            return;
        }

        if (mode === 'create') {
            if (password !== confirmPassword) {
                setError('Passwords do not match');
                return;
            }
            if (password.length < 4) {
                setError('Password must be at least 4 characters');
                return;
            }

            // Check if user exists
            const users = JSON.parse(localStorage.getItem('jarvis-users') || '{}');
            if (users[username]) {
                setError('Username already exists');
                return;
            }

            // Create new user
            users[username] = { password, createdAt: new Date().toISOString() };
            localStorage.setItem('jarvis-users', JSON.stringify(users));

            // Auto sign in
            localStorage.setItem('jarvis-current-user', username);
            onLogin(username);
        } else {
            // Sign in
            const users = JSON.parse(localStorage.getItem('jarvis-users') || '{}');
            if (!users[username] || users[username].password !== password) {
                setError('Invalid username or password');
                return;
            }

            localStorage.setItem('jarvis-current-user', username);
            onLogin(username);
        }
    };

    const handleGuestLogin = () => {
        localStorage.setItem('jarvis-current-user', 'guest');
        onLogin('guest');
    };

    return (
        <div className="login-page">
            <div className="login-container">
                <div className="login-header">
                    <div className="login-logo">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <circle cx="12" cy="12" r="10" />
                            <circle cx="12" cy="12" r="4" />
                            <line x1="12" y1="2" x2="12" y2="6" />
                            <line x1="12" y1="18" x2="12" y2="22" />
                            <line x1="2" y1="12" x2="6" y2="12" />
                            <line x1="18" y1="12" x2="22" y2="12" />
                        </svg>
                    </div>
                    <h1>JARVIS</h1>
                    <p>Your AI Assistant</p>
                </div>

                <div className="login-tabs">
                    <button
                        className={mode === 'signin' ? 'active' : ''}
                        onClick={() => { setMode('signin'); setError(''); }}
                    >
                        Sign In
                    </button>
                    <button
                        className={mode === 'create' ? 'active' : ''}
                        onClick={() => { setMode('create'); setError(''); }}
                    >
                        Create Account
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label htmlFor="username">Username</label>
                        <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter username"
                            autoComplete="username"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter password"
                            autoComplete={mode === 'create' ? 'new-password' : 'current-password'}
                        />
                    </div>

                    {mode === 'create' && (
                        <div className="form-group">
                            <label htmlFor="confirm-password">Confirm Password</label>
                            <input
                                id="confirm-password"
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="Confirm password"
                                autoComplete="new-password"
                            />
                        </div>
                    )}

                    {error && <div className="error-message">{error}</div>}

                    <button type="submit" className="submit-btn">
                        {mode === 'signin' ? 'Sign In' : 'Create Account'}
                    </button>
                </form>

                <div className="login-divider">
                    <span>or</span>
                </div>

                <button className="guest-btn" onClick={handleGuestLogin}>
                    Continue as Guest
                </button>

                <p className="login-info">
                    All data is stored locally on your device.
                </p>
            </div>
        </div>
    );
}

export default LoginPage;
