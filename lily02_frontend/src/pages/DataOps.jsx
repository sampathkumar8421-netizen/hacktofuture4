import { Activity, Shield, Thermometer, Droplets, Map } from 'lucide-react';

export default function DataOps() {
    const systems = [
        { name: 'GDAC Brest', status: 'Healthy', latency: '42ms', icon: <Shield size={20} /> },
        { name: 'US GDAC', status: 'Healthy', latency: '115ms', icon: <Shield size={20} /> },
        { name: 'Hyperpipeline Core', status: 'Active', latency: '12ms', icon: <Activity size={20} /> },
        { name: 'Indic Translator', status: 'Online', latency: '5ms', icon: <Droplets size={20} /> }
    ];

    return (
        <div className="page-wrapper">
            <h1 style={{ marginBottom: '2rem', fontSize: '2.5rem', fontWeight: 700 }}>Data Ops Monitor</h1>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2rem' }}>
                {systems.map((sys, idx) => (
                    <div key={idx} className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                        <div style={{ background: 'rgba(6, 182, 212, 0.1)', padding: '1rem', borderRadius: '12px', color: 'var(--accent-teal)' }}>
                            {sys.icon}
                        </div>
                        <div>
                            <div style={{ fontSize: '0.875rem', color: 'var(--text-dim)' }}>{sys.name}</div>
                            <div style={{ fontWeight: 600 }}>{sys.status}</div>
                            <div style={{ fontSize: '0.75rem', opacity: 0.6 }}>Ping: {sys.latency}</div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="glass-card" style={{ marginTop: '3rem' }}>
                <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Map size={20} />
                    Global Float Health Distribution
                </h3>
                <div style={{ height: '400px', background: 'rgba(0,0,0,0.2)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyCenter: 'center', border: '1px solid var(--border-glass)' }}>
                    <span style={{ color: 'var(--text-dim)' }}>Argo Float Network Visualization arriving in next sub-phase.</span>
                </div>
            </div>
        </div>
    );
}
