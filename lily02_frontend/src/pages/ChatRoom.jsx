import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Paperclip, Loader2, Database, Download, Anchor, BarChart2, Zap, ShieldAlert, Search, Plus } from 'lucide-react';

function renderMarkdown(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
        .replace(/\n/g, '<br/>');
}

export default function ChatRoom() {
    const [messages, setMessages] = useState([
        { role: 'lily', content: 'Greeting. I am <strong>Lily02</strong>. Deep-sea pipeline initialized. How can I assist your research today?', metadata: null }
    ]);
    const [input, setInput] = useState('');
    const [uploadProgress, setUploadProgress] = useState(null);
    const [showInsights, setShowInsights] = useState(false);
    const [showSecondary, setShowSecondary] = useState(false);
    const [autoMLMode, setAutoMLMode] = useState(false);
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    useEffect(() => { scrollToBottom(); }, [messages, isTyping]);

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploadProgress(`Uploading ${file.name}...`);
        const formData = new FormData();
        formData.append('file', file);

        try {
            await axios.post('/api/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setShowSecondary(false);
            setMessages(prev => [...prev, {
                role: 'lily',
                content: `<strong>File Agency</strong>: Successfully ingested <code>${file.name}</code>. I am ready to perform forensics on this data.`,
                metadata: null
            }]);
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'lily',
                content: `<strong>Upload Error</strong>: Failed to sync <code>${file.name}</code> with backend agency.`,
                metadata: null
            }]);
        } finally {
            setUploadProgress(null);
        }
    };

    const runPipeline = async (queryOverride) => {
        const query = queryOverride || input;
        if (!query.trim()) return;

        const userMessage = { role: 'user', content: query, metadata: null };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setShowInsights(false);
        setShowSecondary(false);
        setIsTyping(true);

        try {
            const historyStr = messages.slice(-4).map(m => `${m.role}: ${m.content}`).join('\n');
            const response = await axios.post('/api/orchestrate', {
                query: userMessage.content,
                chat_history: historyStr,
                enable_automl: autoMLMode
            });

            const data = response.data;
            setMessages(prev => [...prev, {
                role: 'lily',
                content: data.lily_response,
                metadata: data
            }]);
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'lily',
                content: `<strong>Critical Failure</strong>: Logic core unreachable. Details: ${err.message}`,
                metadata: null
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleSend = (e) => {
        e.preventDefault();
        runPipeline();
    };

    const handleInsightClick = (prompt) => {
        runPipeline(prompt);
    };

    const handleDownload = (payloadString, format, fileName) => {
        const blob = new Blob([payloadString], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = fileName || `lily_analysis.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="main-content">
            <header style={{ padding: '2rem 4rem', borderBottom: '1px solid var(--border-frost)', background: 'white', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ background: 'var(--accent-teal-soft)', padding: '0.5rem', borderRadius: '10px' }}>
                        <Anchor size={20} className="text-teal" />
                    </div>
                    <div>
                        <div style={{ fontWeight: 800, fontSize: '0.9rem', letterSpacing: '-0.02em' }}>COMMAND CENTER</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Argo Intelligence Node // SYNC_ACTIVE</div>
                    </div>
                </div>
            </header>

            <div className="chat-viewport">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message-node ${msg.role}`}>
                        <div className={`bubble ${msg.role}`}>
                            <div dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />

                            {msg.metadata && msg.metadata.plan_steps && (
                                <div style={{ marginTop: '1.25rem', padding: '1rem', background: '#f8fafc', borderLeft: '3px solid var(--accent-teal)', borderRadius: '8px', fontSize: '0.85rem' }}>
                                    <div style={{ color: 'var(--accent-teal)', marginBottom: '0.5rem', fontSize: '0.7rem', fontWeight: 800, textTransform: 'uppercase' }}>Pipeline Execution</div>
                                    <div style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                                        {msg.metadata.plan_steps.map((s, i) => <div key={i}> {i === msg.metadata.plan_steps.length - 1 ? '└' : '├'} {s}</div>)}
                                    </div>
                                </div>
                            )}

                            {msg.metadata && msg.metadata.file_format && msg.metadata.raw_file_payload && (
                                <button
                                    className="btn-ghost"
                                    style={{ marginTop: '1rem', border: '1px solid var(--border-frost)', padding: '0.6rem 1.2rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}
                                    onClick={() => handleDownload(msg.metadata.raw_file_payload, msg.metadata.file_format)}
                                >
                                    <Download size={16} />
                                    Download {msg.metadata.file_format.toUpperCase()} Analysis
                                </button>
                            )}
                        </div>
                    </div>
                ))}
                {isTyping && (
                    <div className="message-node lily">
                        <div className="bubble">
                            <div className="loading-orbit">
                                <div className="dot"></div><div className="dot"></div><div className="dot"></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-dock">
                {showInsights && (
                    <div className="insights-popover">
                        {[
                            { title: 'Heat Content Trend', icon: <Zap size={14} />, desc: 'Global 700m OHC Analysis', prompt: 'Perform a global 0-700m Ocean Heat Content trend analysis using the latest hyperpipeline.' },
                            { title: 'BGC Health Scan', icon: <Anchor size={14} />, desc: 'Oxygen/Nitrate Assessment', prompt: 'Lily, evaluate the biometric health of the BGC Argo network focusing on deoxygenation.' },
                            { title: 'Semantic Retrieval', icon: <Search size={14} />, desc: 'Complex Multi-Node Search', prompt: 'List all floats that show subsurface temperature spikes over 4 degrees in the Pacific.' }
                        ].map((insight, i) => (
                            <div key={i} className="insight-option" onClick={() => handleInsightClick(insight.prompt)}>
                                <div className="insight-icon">{insight.icon}</div>
                                <div className="insight-label">
                                    <div className="insight-title">{insight.title}</div>
                                    <div className="insight-desc">{insight.desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {uploadProgress && <div style={{ fontSize: '0.75rem', color: 'var(--accent-teal)', marginBottom: '0.8rem', marginLeft: '1.5rem', fontWeight: 600 }}>{uploadProgress}</div>}
                <form className="control-bar" onSubmit={handleSend}>
                    <button type="button" className={`btn-ghost action-btn plus-btn ${showSecondary ? 'active' : ''}`} onClick={() => { setShowSecondary(!showSecondary); setShowInsights(false); }}>
                        <Plus size={20} />
                    </button>

                    <div className={`actions-container ${showSecondary ? 'expanded' : 'collapsed'}`} style={{ width: showSecondary ? '140px' : '0' }}>
                        <button type="button" className={`btn-ghost action-btn ${showInsights ? 'active' : ''}`} onClick={() => setShowInsights(!showInsights)} title="Scientific Presets">
                            <BarChart2 size={18} />
                        </button>
                        <button type="button" className={`btn-ghost action-btn ${autoMLMode ? 'active' : ''}`} style={autoMLMode ? { color: '#10b981', background: 'rgba(16, 185, 129, 0.1)' } : {}} onClick={() => setAutoMLMode(!autoMLMode)} title="Auto-ML Analysis">
                            <Zap size={18} />
                        </button>
                        <button type="button" className="btn-ghost action-btn" onClick={() => fileInputRef.current.click()} title="Upload Data">
                            <Paperclip size={18} />
                        </button>
                    </div>

                    <input
                        type="file"
                        ref={fileInputRef}
                        style={{ display: 'none' }}
                        onChange={handleFileUpload}
                    />
                    <input
                        type="text"
                        className="ocean-input"
                        placeholder="Dive into ocean intelligence..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={isTyping}
                    />
                    <button type="submit" className="btn-primary action-btn" disabled={isTyping || !input.trim()}>
                        {isTyping ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
                    </button>
                </form>
            </div>
        </div>
    );
}
