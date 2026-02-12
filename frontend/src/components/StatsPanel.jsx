
import { BarChart2, DollarSign, Cloud, Users, Clock } from 'lucide-react'

export default function StatsPanel({ data }) {
    if (!data) return null;

    const { stats, path_nodes } = data;

    // Support both new (Google) and old (Local) formats
    // Google format: stats has all fields directly
    // Local format: stats might have nested breakdown (though we removed local engine)

    const {
        total_cost = 0,
        time_cost = 0,
        congestion_penalty = 0,
        emission_cost = 0,
        social_cost = 0,
        travel_time_hours = 0
    } = stats || {};

    // Safety check just in case stats is missing
    if (!stats) return null;

    // Normalize for bars (simple percentage of total cost)
    const getPercent = (val) => Math.min(100, Math.max(5, (val / total_cost) * 100));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', animation: 'fadeIn 0.5s ease' }}>
            <h3 style={{ margin: 0, fontSize: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                Objective Analysis
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div className="stat-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '0.75rem', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Travel Time</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{(travel_time_hours * 60).toFixed(1)} <span style={{ fontSize: '0.875rem' }}>min</span></div>
                </div>
                <div className="stat-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '0.75rem', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total Cost J(P)</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{total_cost.toFixed(2)}</div>
                </div>
            </div>

            {/* Breakdown Bars */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
                <CostBar label="Time" value={time_cost} total={total_cost} color="#3b82f6" icon={<Clock size={12} />} />
                <CostBar label="Congestion" value={congestion_penalty} total={total_cost} color="#f59e0b" icon={<BarChart2 size={12} />} />
                <CostBar label="Emission" value={emission_cost} total={total_cost} color="#10b981" icon={<Cloud size={12} />} />
                <CostBar label="Social" value={social_cost} total={total_cost} color="#8b5cf6" icon={<Users size={12} />} />
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                {path_nodes && path_nodes.length > 0 ? (
                    <>Path Nodes: {path_nodes.length}</>
                ) : (
                    <>Google Maps Route</>
                )}
            </div>
        </div>
    )
}

function CostBar({ label, value, total, color, icon }) {
    const percent = (value / total) * 100;
    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>{icon} {label}</span>
                <span>{value.toFixed(2)}</span>
            </div>
            <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${percent}%`, background: color, transition: 'width 0.5s ease' }} />
            </div>
        </div>
    )
}
