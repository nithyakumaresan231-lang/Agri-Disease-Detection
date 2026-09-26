import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Camera,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  TrendingUp,
  Search,
  ExternalLink,
  ChevronRight,
  Leaf
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { profileAPI, historyAPI } from "../services/api";

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    total_analyses: 0,
    diseases_detected: 0,
    healthy_results: 0,
    recent_analysis_at: null
  });
  const [recentAnalyses, setRecentAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [statsData, historyData] = await Promise.all([
          profileAPI.getStats(),
          historyAPI.getAll({ sort: "desc" })
        ]);

        setStats(statsData);
        setRecentAnalyses(historyData.slice(0, 5));
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  };

  return (
    <div className="dashboard-view">
      {/* Welcome Banner */}
      <section className="welcome-banner">
        <div className="welcome-text">
          <span className="welcome-tag">FARMER DASHBOARD</span>
          <h2>Welcome back, {user?.name || "Farmer"}</h2>
          <p>Monitor your crops, diagnose foliar conditions, and review preventive recommendations early.</p>
        </div>

        <div className="welcome-action">
          <Link to="/detect" className="btn-large-cta">
            <Camera size={22} />
            <span>Start Disease Detection</span>
          </Link>
        </div>
      </section>

      {/* Metrics Cards Grid */}
      <section className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon-box bg-blue-100">
            <Activity size={24} color="#2563eb" />
          </div>
          <div className="metric-details">
            <span className="metric-label">Total Analyses</span>
            <strong className="metric-value">{stats.total_analyses}</strong>
            <small className="metric-sub">Foliar tests conducted</small>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-box bg-amber-100">
            <AlertTriangle size={24} color="#d97706" />
          </div>
          <div className="metric-details">
            <span className="metric-label">Diseases Detected</span>
            <strong className="metric-value text-amber">{stats.diseases_detected}</strong>
            <small className="metric-sub">Interventions advised</small>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-box bg-green-100">
            <CheckCircle2 size={24} color="#16a34a" />
          </div>
          <div className="metric-details">
            <span className="metric-label">Healthy Results</span>
            <strong className="metric-value text-green">{stats.healthy_results}</strong>
            <small className="metric-sub">Optimal vigor</small>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-box bg-purple-100">
            <Clock size={24} color="#7c3aed" />
          </div>
          <div className="metric-details">
            <span className="metric-label">Recent Analysis</span>
            <strong className="metric-value-sm">
              {stats.recent_analysis_at ? formatDate(stats.recent_analysis_at) : "None yet"}
            </strong>
            <small className="metric-sub">Last scan activity</small>
          </div>
        </div>
      </section>

      {/* Workflow Step Banner */}
      <section className="workflow-compact-banner">
        <div className="workflow-compact-header">
          <Leaf size={18} color="#2e5b3b" />
          <span>SYSTEM WORKFLOW</span>
        </div>
        <div className="workflow-steps-row">
          <div className="wf-step">
            <span className="wf-num">1</span>
            <span className="wf-title">Capture</span>
          </div>
          <ChevronRight size={18} className="wf-arrow" />
          <div className="wf-step">
            <span className="wf-num">2</span>
            <span className="wf-title">Detect</span>
          </div>
          <ChevronRight size={18} className="wf-arrow" />
          <div className="wf-step">
            <span className="wf-num">3</span>
            <span className="wf-title">Analyze</span>
          </div>
          <ChevronRight size={18} className="wf-arrow" />
          <div className="wf-step active">
            <span className="wf-num">4</span>
            <span className="wf-title">Advisory</span>
          </div>
        </div>
      </section>

      {/* Recent Analyses Section */}
      <section className="recent-analyses-card">
        <div className="card-header-row">
          <div>
            <h3>Recent Analyses</h3>
            <p className="card-subtitle">Your latest 5 crop leaf diagnoses</p>
          </div>

          <Link to="/history" className="view-all-link">
            <span>View Full History</span>
            <ArrowRight size={16} />
          </Link>
        </div>

        {loading ? (
          <div className="loading-placeholder">
            <p>Loading recent scans...</p>
          </div>
        ) : recentAnalyses.length === 0 ? (
          <div className="empty-state-box">
            <Leaf size={44} color="#8fac95" />
            <h4>No analyses recorded yet</h4>
            <p>Upload or snap a leaf photo using the camera to receive your first diagnostic advisory.</p>
            <Link to="/detect" className="btn-empty-action">
              <Camera size={16} />
              <span>Perform First Detection</span>
            </Link>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="recent-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Crop</th>
                  <th>Detected Condition</th>
                  <th>Confidence</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {recentAnalyses.map((item) => {
                  const isHealthy = item.status?.toLowerCase() === "healthy";
                  return (
                    <tr key={item.id}>
                      <td className="text-muted">{formatDate(item.created_at)}</td>
                      <td>
                        <strong>{item.crop}</strong>
                      </td>
                      <td>{item.disease}</td>
                      <td>
                        <div className="confidence-pill">
                          <div
                            className="confidence-mini-bar"
                            style={{ width: `${item.confidence}%` }}
                          />
                          <span>{item.confidence.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td>
                        <span className={`status-badge ${isHealthy ? "badge-healthy" : "badge-detected"}`}>
                          {item.status}
                        </span>
                      </td>
                      <td>
                        <Link to={`/analysis/${item.id}`} className="table-view-btn">
                          <span>View Details</span>
                          <ExternalLink size={14} />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
