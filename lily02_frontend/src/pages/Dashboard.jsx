import React from 'react';
import { BarChart2, TrendingUp, AlertCircle } from 'lucide-react';

export default function Dashboard() {
    return (
        <div className="page-wrapper">
            <h1 style={{ marginBottom: '2.5rem', fontSize: '2.25rem', fontWeight: 800, letterSpacing: '-0.04em' }}>Ocean Analytics</h1>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
                <div className="glass-card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                        <BarChart2 size={20} color="#0891b2" />
                        <h3 style={{ color: 'var(--accent-teal)', fontSize: '1.1rem', fontWeight: 700 }}>Argo Insights</h3>
                    </div>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: '1.6' }}>Select an application type from the Command Center to populate this dashboard with real-time analytics.</p>
                </div>

                <div className="glass-card" style={{ gridColumn: '1 / -1' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                        <AlertCircle size={20} color="#64748b" />
                        <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Global Temperature Trends</h3>
                    </div>
                    <div className="chart-placeholder" style={{ height: '350px', borderRadius: '12px' }}>
                        <span>Integrated Plotly/Chart.js charts will appear here based on your queries.</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
