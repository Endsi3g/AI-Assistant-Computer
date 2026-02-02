import './StepVisualizer.css';

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

interface StepVisualizerProps {
    steps: AgentStep[];
    isLive?: boolean;
}

function StepVisualizer({ steps, isLive = false }: StepVisualizerProps) {

    const getStepIcon = (type: string) => {
        switch (type) {
            case 'thinking':
                return '🤔';
            case 'planning':
                return '📋';
            case 'tool_call':
                return '🔧';
            case 'observation':
                return '👁️';
            case 'response':
                return '✅';
            case 'error':
                return '❌';
            default:
                return '▪️';
        }
    };

    const getStepLabel = (type: string) => {
        switch (type) {
            case 'thinking':
                return 'Thinking';
            case 'planning':
                return 'Planning';
            case 'tool_call':
                return 'Tool Call';
            case 'observation':
                return 'Observation';
            case 'response':
                return 'Response';
            case 'error':
                return 'Error';
            default:
                return 'Step';
        }
    };

    return (
        <div className={`step-visualizer ${isLive ? 'live' : ''}`}>
            <div className="step-header">
                <div className="step-title">
                    {isLive && <span className="live-indicator">●</span>}
                    Agent Steps
                </div>
                <span className="step-count">{steps.length} steps</span>
            </div>

            <div className="steps-timeline">
                {steps.map((step, index) => (
                    <div key={step.id} className={`step-node ${step.type}`}>
                        <div className="step-line">
                            {index < steps.length - 1 && <div className="connector" />}
                        </div>

                        <div className="step-content">
                            <div className="step-badge">
                                <span className="step-icon">{getStepIcon(step.type)}</span>
                                <span className="step-label">{getStepLabel(step.type)}</span>
                                {step.tool_name && (
                                    <span className="tool-name">{step.tool_name}</span>
                                )}
                                {step.duration_ms && (
                                    <span className="step-duration">{step.duration_ms}ms</span>
                                )}
                            </div>

                            <div className="step-body">
                                {step.type === 'tool_call' && step.tool_args && (
                                    <div className="tool-args">
                                        <code>{JSON.stringify(step.tool_args, null, 2)}</code>
                                    </div>
                                )}

                                {step.type === 'observation' && (
                                    <div className="observation-content">
                                        {step.content.length > 200
                                            ? step.content.slice(0, 200) + '...'
                                            : step.content
                                        }
                                    </div>
                                )}

                                {step.type === 'error' && (
                                    <div className="error-content">
                                        {step.content}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}

                {isLive && (
                    <div className="step-node loading">
                        <div className="step-line" />
                        <div className="step-content">
                            <div className="step-badge">
                                <span className="step-icon">
                                    <span className="loading-spinner" />
                                </span>
                                <span className="step-label">Processing...</span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default StepVisualizer;
