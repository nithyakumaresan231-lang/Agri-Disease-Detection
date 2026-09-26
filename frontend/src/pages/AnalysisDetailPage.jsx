import React, { useState, useEffect } from "react";
import { useParams, useLocation, Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldCheck,
  Wrench,
  Camera,
  Calendar,
  Layers,
  Thermometer,
  AlertCircle
} from "lucide-react";
import { historyAPI, API_BASE_URL } from "../services/api";

export default function AnalysisDetailPage() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  // If passed directly from detection redirect, use state initially
  const [analysis, setAnalysis] = useState(location.state?.result || null);
  const [loading, setLoading] = useState(!location.state?.result);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchDetail() {
      if (!id) return;
      try {
        setLoading(true);
        const data = await historyAPI.getById(id);
        setAnalysis(data);
      } catch (err) {
        console.error("Failed to fetch analysis details:", err);
        setError(err.message || "Could not retrieve the analysis details.");
      } finally {
        setLoading(false);
      }
    }

    if (!location.state?.result) {
      fetchDetail();
    }
  }, [id, location.state]);

  const formatDate = (dateStr) => {
    if (!dateStr) return "Just now";
    return new Date(dateStr).toLocaleString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  if (loading) {
    return (
      <div className="analysis-loading-state">
        <div className="spinner" />
        <p>Loading disease diagnostic report...</p>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="analysis-error-state">
        <AlertCircle size={42} color="#dc2626" />
        <h3>Analysis Not Found</h3>
        <p>{error || "The requested analysis record does not exist or you do not have permission to view it."}</p>
        <Link to="/history" className="btn-return">
          <ArrowLeft size={16} />
          <span>Return to History</span>
        </Link>
      </div>
    );
  }

  const isHealthy = analysis.status?.toLowerCase() === "healthy";
  const advisory = analysis.advisory || {};

  return (
    <div className="analysis-view">
      {/* Top action bar */}
      <div className="analysis-navigation-bar">
        <button
          type="button"
          className="btn-back"
          onClick={() => navigate("/history")}
        >
          <ArrowLeft size={18} />
          <span>Back to History</span>
        </button>

        <Link to="/detect" className="btn-new-scan">
          <Camera size={16} />
          <span>Run Another Scan</span>
        </Link>
      </div>

      {/* Main Analysis Summary Card */}
      <div className="analysis-summary-card">
        <div className="analysis-card-grid">
          {/* Leaf image presentation */}
          <div className="analysis-image-container">
            {analysis.image_url ? (
              <img
                src={`${API_BASE_URL}${analysis.image_url}`}
                alt={`${analysis.crop} - ${analysis.disease}`}
                className="analysis-display-image"
                onError={(e) => {
                  e.target.style.display = "none";
                  e.target.nextSibling.style.display = "flex";
                }}
              />
            ) : null}
            <div className="image-fallback" style={{ display: analysis.image_url ? "none" : "flex" }}>
              <Layers size={40} color="#8fac95" />
              <span>Diagnostic Sample #{analysis.id}</span>
            </div>
            <span className="image-caption">Submitted leaf sample</span>
          </div>

          {/* Diagnostic overview */}
          <div className="analysis-overview">
            <div className="diagnostic-header-tag">
              <span className="tag-label">ANALYSIS REPORT #{analysis.id}</span>
              <span className="analysis-time">
                <Calendar size={14} />
                <span>{formatDate(analysis.created_at)}</span>
              </span>
            </div>

            <h2 className="disease-title">{analysis.disease}</h2>

            <div className="overview-meta-chips">
              <div className="chip">
                <span className="chip-label">Target Crop:</span>
                <strong className="chip-val">{analysis.crop}</strong>
              </div>

              <div className="chip">
                <span className="chip-label">Condition:</span>
                <span className={`status-pill ${isHealthy ? "pill-healthy" : "pill-detected"}`}>
                  {isHealthy ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                  <span>{analysis.status}</span>
                </span>
              </div>
            </div>

            {/* Confidence Score Bar */}
            <div className="confidence-section">
              <div className="confidence-label-row">
                <span className="conf-label">Diagnostic Confidence</span>
                <strong className="conf-percentage">{analysis.confidence.toFixed(1)}%</strong>
              </div>
              <div className="confidence-track">
                <div
                  className={`confidence-fill ${isHealthy ? "fill-green" : "fill-amber"}`}
                  style={{ width: `${analysis.confidence}%` }}
                />
              </div>
              <span className="conf-subtext">
                Multi-class foliar pattern matching calibrated for Solanaceae datasets.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Section A: Disease Information */}
      {advisory.description && (
        <div className="advisory-card">
          <div className="advisory-header">
            <div className="icon-badge bg-blue-50">
              <Info size={20} color="#2563eb" />
            </div>
            <div>
              <h3>Disease Information</h3>
              <p className="section-desc">Biological overview and foliar characteristics</p>
            </div>
          </div>
          <p className="advisory-description-text">{advisory.description}</p>
        </div>
      )}

      {/* Section B: Symptoms */}
      {advisory.symptoms && advisory.symptoms.length > 0 && (
        <div className="advisory-card">
          <div className="advisory-header">
            <div className="icon-badge bg-amber-50">
              <AlertTriangle size={20} color="#d97706" />
            </div>
            <div>
              <h3>Observable Symptoms</h3>
              <p className="section-desc">Key physical indicators identified on plant foliage and stems</p>
            </div>
          </div>
          <ul className="checklist">
            {advisory.symptoms.map((symptom, idx) => (
              <li key={idx}>
                <span className="bullet-indicator" />
                <span>{symptom}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Section C: Preventive Measures */}
      {advisory.preventive_measures && advisory.preventive_measures.length > 0 && (
        <div className="advisory-card highlight-card">
          <div className="advisory-header">
            <div className="icon-badge bg-emerald-50">
              <ShieldCheck size={20} color="#059669" />
            </div>
            <div>
              <h3>Preventive Measures</h3>
              <p className="section-desc">Agronomic field precautions to curb pathogen spread</p>
            </div>
          </div>
          <ul className="action-list">
            {advisory.preventive_measures.map((measure, idx) => (
              <li key={idx}>
                <CheckCircle2 size={17} color="#059669" className="action-icon" />
                <span>{measure}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Section D: Management & Recommended Actions */}
      {advisory.management && advisory.management.length > 0 && (
        <div className="advisory-card">
          <div className="advisory-header">
            <div className="icon-badge bg-purple-50">
              <Wrench size={20} color="#7c3aed" />
            </div>
            <div>
              <h3>Management &amp; Recommended Actions</h3>
              <p className="section-desc">Intervention steps for containment and soil/crop recovery</p>
            </div>
          </div>
          <ul className="action-list">
            {advisory.management.map((action, idx) => (
              <li key={idx}>
                <span className="num-badge">{idx + 1}</span>
                <span>{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Section E: Important Note / Disclaimer */}
      <div className="disclaimer-banner">
        <Info size={22} color="#4b8b5c" />
        <div>
          <h4>Important Agronomic Advisory Note</h4>
          <p>
            Please use this automated analysis as an initial advisory guideline. Severe, rapid-spreading,
            or ambiguous crop conditions should always be confirmed through on-site inspection with a
            certified agricultural extension officer or agronomist before administering major chemical treatments.
          </p>
        </div>
      </div>
    </div>
  );
}
