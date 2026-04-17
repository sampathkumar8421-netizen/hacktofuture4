import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, BarChart2, Activity, Shield, Code, HelpCircle, FileText, Anchor } from 'lucide-react';

export default function Sidebar() {
    const links = [
        { to: "/", icon: <Home size={18} />, label: "Command Center" },
        { to: "/analysis", icon: <BarChart2 size={18} />, label: "Ocean Analytics" },
        { to: "/data-ops", icon: <Activity size={18} />, label: "Data Ops Monitor" },
        { to: "/security", icon: <Shield size={18} />, label: "Security & Logs" },
        { to: "/local-install", icon: <Layers size={18} />, label: "Local Installation" },
        { to: "/help", icon: <HelpCircle size={18} />, label: "Support" },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <Anchor size={24} color="#0891b2" />
                <span style={{ marginLeft: '8px' }}>Lily02</span>
            </div>

            <nav className="nav-links">
                {links.map((link) => (
                    <NavLink
                        key={link.to}
                        to={link.to}
                        className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                    >
                        {link.icon}
                        <span>{link.label}</span>
                    </NavLink>
                ))}
            </nav>

            <div className="nav-footer" style={{ marginTop: 'auto', paddingTop: '1rem' }}>
                <a href="#docs" className="nav-item">
                    <FileText size={18} />
                    <span>Documentation</span>
                </a>
            </div>
        </aside>
    );
}
