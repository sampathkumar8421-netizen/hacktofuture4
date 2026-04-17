import React from 'react';
import { Download, Terminal, TerminalSquare, Layers, Cpu, Globe, Settings, Copy, Check } from 'lucide-react';

export default function LocalInstallation() {
    const [copied, setCopied] = React.useState(null);

    const copyToClipboard = (text, id) => {
        navigator.clipboard.writeText(text);
        setCopied(id);
        setTimeout(() => setCopied(null), 2000);
    };

    const installCommand = "pip install lily02-agentic";
    const launchCommand = "lily02 ask 'What is the current OHC trend?' --automl";

    return (
        <div className="main-content" style={{ padding: '2rem 4rem' }}>
            <header style={{ marginBottom: '3rem' }}>
                <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.5rem' }}>Local Installation Hub</h1>
                <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>Deploy the Lily02 Agentic Model and Hyperpipeline on your local infrastructure.</p>
            </header>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '3rem' }}>
                <div className="stats-card" style={{ padding: '2rem', background: 'white' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                        <div style={{ background: 'var(--accent-teal-soft)', padding: '0.8rem', borderRadius: '12px' }}>
                            <Download size={24} className="text-teal" />
                        </div>
                        <h3 style={{ margin: 0 }}>CLI Package Installer</h3>
                    </div>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                        Install the cross-platform Lily02 CLI for Windows, Linux, and iSH (iOS).
                    </p>
                    <div style={{ background: '#1e293b', padding: '1rem', borderRadius: '8px', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <code style={{ color: '#94a3b8', fontSize: '0.9rem' }}>$ {installCommand}</code>
                        <button
                            className="btn-ghost"
                            style={{ color: '#94a3b8', padding: '0.4rem' }}
                            onClick={() => copyToClipboard(installCommand, 'install')}
                        >
                            {copied === 'install' ? <Check size={16} color="#10b981" /> : <Copy size={16} />}
                        </button>
                    </div>
                </div>

                <div className="stats-card" style={{ padding: '2rem', background: 'white' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                        <div style={{ background: 'var(--accent-teal-soft)', padding: '0.8rem', borderRadius: '12px' }}>
                            <TerminalSquare size={24} className="text-teal" />
                        </div>
                        <h3 style={{ margin: 0 }}>Terminal Interaction</h3>
                    </div>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                        Run the hyperpipeline directly from your terminal with rich diagnostics.
                    </p>
                    <div style={{ background: '#1e293b', padding: '1rem', borderRadius: '8px', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <code style={{ color: '#94a3b8', fontSize: '0.9rem' }}>$ {launchCommand}</code>
                        <button
                            className="btn-ghost"
                            style={{ color: '#94a3b8', padding: '0.4rem' }}
                            onClick={() => copyToClipboard(launchCommand, 'launch')}
                        >
                            {copied === 'launch' ? <Check size={16} color="#10b981" /> : <Copy size={16} />}
                        </button>
                    </div>
                </div>
            </div>

            <section style={{ background: 'white', padding: '3rem', borderRadius: '16px', border: '1px solid var(--border-frost)' }}>
                <h2 style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Cpu size={28} className="text-teal" />
                    Embedded Model Configuration: gpt-oss-120b
                </h2>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem' }}>
                    <div>
                        <h4 style={{ color: 'var(--accent-teal)', marginBottom: '1rem', textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 800 }}>Requirements</h4>
                        <ul className="persona-list" style={{ listStyle: 'none', padding: 0 }}>
                            <li>VRAM: 80GB (GGUF 4-bit)</li>
                            <li>Storage: 120GB SSD</li>
                            <li>Engine: Ollama / LM Studio</li>
                        </ul>
                    </div>
                    <div>
                        <h4 style={{ color: 'var(--accent-teal)', marginBottom: '1rem', textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 800 }}>CLI settings</h4>
                        <ul className="persona-list" style={{ listStyle: 'none', padding: 0 }}>
                            <li>--model "gpt-oss-120b"</li>
                            <li>--mode "scientific"</li>
                            <li>--forensics enable</li>
                        </ul>
                    </div>
                    <div>
                        <h4 style={{ color: 'var(--accent-teal)', marginBottom: '1rem', textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 800 }}>Features</h4>
                        <ul className="persona-list" style={{ listStyle: 'none', padding: 0 }}>
                            <li>Termianl UI (Rich)</li>
                            <li>Open Source Core</li>
                            <li>Cross-Platform CLI</li>
                        </ul>
                    </div>
                </div>

                <div style={{ marginTop: '3rem', padding: '1.5rem', background: 'var(--bg-main)', borderRadius: '12px', borderLeft: '4px solid var(--accent-teal)' }}>
                    <p style={{ margin: 0, fontWeight: 600, fontSize: '0.95rem' }}>
                        Note: For iOS (iPad/iPhone) use the <strong>iSH Terminal</strong> app. Install python3 and run the pip command to access Lily02 on the go.
                    </p>
                </div>
            </section>
        </div>
    );
}
