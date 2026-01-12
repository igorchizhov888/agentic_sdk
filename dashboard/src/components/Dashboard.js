import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [traces, setTraces] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, tracesData] = await Promise.all([
          api.getTraceStats(),
          api.getTraces(null, 10)
        ]);
        setStats(statsData);
        setTraces(tracesData.traces);
      } catch (error) {
        console.error('Failed to load data:', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <div style={styles.loading}>Loading...</div>;
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>AgenticSDK Dashboard</h1>
      
      {/* Stats Cards */}
      <div style={styles.statsGrid}>
        <StatCard 
          title="Total Traces" 
          value={stats?.total_traces || 0}
        />
        <StatCard 
          title="Success Rate" 
          value={`${((stats?.success_rate || 0) * 100).toFixed(1)}%`}
        />
        <StatCard 
          title="Avg Duration" 
          value={`${(stats?.avg_duration || 0).toFixed(2)}s`}
        />
        <StatCard 
          title="Failed" 
          value={stats?.failed || 0}
        />
      </div>

      {/* Recent Traces */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Recent Traces</h2>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Trace ID</th>
              <th style={styles.th}>Agent</th>
              <th style={styles.th}>Task</th>
              <th style={styles.th}>Duration</th>
              <th style={styles.th}>Status</th>
            </tr>
          </thead>
          <tbody>
            {traces.map(trace => (
              <tr key={trace.trace_id} style={styles.tr}>
                <td style={styles.td}>{trace.trace_id.slice(0, 8)}...</td>
                <td style={styles.td}>{trace.agent_id?.slice(0, 8)}...</td>
                <td style={styles.td}>{trace.task?.slice(0, 50)}...</td>
                <td style={styles.td}>{trace.duration_seconds?.toFixed(2)}s</td>
                <td style={styles.td}>
                  <span style={trace.success ? styles.success : styles.failed}>
                    {trace.success ? 'SUCCESS' : 'FAILED'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatCard({ title, value }) {
  return (
    <div style={styles.card}>
      <div style={styles.cardTitle}>{title}</div>
      <div style={styles.cardValue}>{value}</div>
    </div>
  );
}

const styles = {
  container: {
    padding: '20px',
    fontFamily: 'Arial, sans-serif',
    maxWidth: '1200px',
    margin: '0 auto'
  },
  title: {
    fontSize: '32px',
    marginBottom: '30px'
  },
  loading: {
    textAlign: 'center',
    padding: '50px',
    fontSize: '18px'
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '20px',
    marginBottom: '40px'
  },
  card: {
    background: '#f5f5f5',
    padding: '20px',
    borderRadius: '8px',
    border: '1px solid #ddd'
  },
  cardTitle: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '10px'
  },
  cardValue: {
    fontSize: '28px',
    fontWeight: 'bold'
  },
  section: {
    marginTop: '40px'
  },
  sectionTitle: {
    fontSize: '24px',
    marginBottom: '20px'
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse'
  },
  th: {
    textAlign: 'left',
    padding: '12px',
    background: '#f5f5f5',
    borderBottom: '2px solid #ddd'
  },
  tr: {
    borderBottom: '1px solid #eee'
  },
  td: {
    padding: '12px'
  },
  success: {
    color: 'green',
    fontWeight: 'bold'
  },
  failed: {
    color: 'red',
    fontWeight: 'bold'
  }
};

export default Dashboard;
