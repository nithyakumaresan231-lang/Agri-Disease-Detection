
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
  AlertCircle
} from "lucide-react";
import {
  historyAPI,
  API_BASE_URL,
  translationAPI
} from "../services/api";

export default function AnalysisDetailPage() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState(
    location.state?.result || null
  );
  const [loading, setLoading] = useState(!location.state?.result);
  const [error, setError] = useState("");
  const [language, setLanguage] = useState("en-IN");
  const [translatedReport, setTranslatedReport] = useState(null);
  const [translationLoading, setTranslationLoading] = useState(false);
  const [translationError, setTranslationError] = useState("");

  // Load analysis details
  useEffect(() => {
    async function fetchDetail() {
      if (!id) return;

      try {
        setLoading(true);
        const data = await historyAPI.getById(id);
        setAnalysis(data);
      } catch (err) {
        console.error("Failed to fetch analysis:", err);
        setError(err.message || "Could not retrieve the analysis.");
      } finally {
        setLoading(false);
      }
    }

    if (!location.state?.result) {
      fetchDetail();
    }
  }, [id, location.state]);

  // Translate the report when Tamil is selected
  useEffect(() => {
    let cancelled = false;

    async function loadTranslation() {
      if (!analysis || language !== "ta-IN") {
        setTranslatedReport(null);
        setTranslationError("");
        setTranslationLoading(false);
        return;
      }

      setTranslationLoading(true);
      setTranslationError("");

      const advisory = analysis.advisory || {};

      const report = {
        crop: analysis.crop || "",
        disease: analysis.disease || "",
        status: analysis.status || "",
        description: advisory.description || "",
        symptoms: advisory.symptoms || [],
        preventive_measures: advisory.preventive_measures || [],
        management: advisory.management || []
      };

      try {
        const result = await translationAPI.translateReport(
          report,
          "ta"
        );

        if (!cancelled) {
          setTranslatedReport(result.report);
        }
      } catch (err) {
        console.error("Report translation failed:", err);

        if (!cancelled) {
          setTranslationError(
            err.message || "Translation failed. Please try again."
          );
          setTranslatedReport(null);
        }
      } finally {
        if (!cancelled) {
          setTranslationLoading(false);
        }
      }
    }

    loadTranslation();

    return () => {
      cancelled = true;
    };
  }, [analysis, language]);

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
        <p>
          {error ||
            "The requested analysis record does not exist or you do not have permission to view it."}
        </p>
        <Link to="/history" className="btn-return">
          <ArrowLeft size={16} />
          <span>Return to History</span>
        </Link>
      </div>
    );
  }

  const isTamil = language === "ta-IN";
  const isHealthy = analysis.status?.toLowerCase() === "healthy";

  // Use translated report in Tamil mode, otherwise use original report
  const report = isTamil && translatedReport
    ? translatedReport
    : analysis;

  const originalAdvisory = analysis.advisory || {};

  const advisory = isTamil && translatedReport
    ? {
        description: translatedReport.description || "",
        symptoms: translatedReport.symptoms || [],
        preventive_measures:
          translatedReport.preventive_measures || [],
        management: translatedReport.management || []
      }
    : originalAdvisory;

  // Text labels in the selected language
  const labels = isTamil
    ? {
        loading: "தமிழில் அறிக்கை மொழிபெயர்க்கப்படுகிறது...",
        report: "பகுப்பாய்வு அறிக்கை",
        submittedImage: "சமர்ப்பிக்கப்பட்ட இலைப் படம்",
        crop: "பயிர்",
        condition: "நிலை",
        confidence: "கண்டறிதல் நம்பகத்தன்மை",
        confidenceNote: "கண்டறிதல் மாதிரியின் நம்பகத்தன்மை மதிப்பெண்.",
        diseaseInfo: "நோய் விவரம்",
        infoDesc: "நோய் பற்றிய தகவல்கள்",
        symptoms: "அறிகுறிகள்",
        symptomsDesc: "தாவரத்தில் காணப்படும் அறிகுறிகள்",
        prevention: "தடுப்பு முறைகள்",
        preventionDesc: "நோய் பரவுவதைத் தடுக்கும் வழிகள்",
        management: "மேலாண்மை மற்றும் பரிந்துரைக்கப்பட்ட நடவடிக்கைகள்",
        managementDesc: "நோயைக் கட்டுப்படுத்துவதற்கான நடவடிக்கைகள்",
        importantNote: "முக்கிய வேளாண் ஆலோசனை",
        disclaimer:
          "இந்த தானியங்கி பகுப்பாய்வு ஆரம்பகட்ட ஆலோசனையாக மட்டுமே பயன்படுத்தப்பட வேண்டும். நோய் தீவிரமாகவோ வேகமாகப் பரவினாலோ, பெரிய அளவிலான சிகிச்சையை மேற்கொள்வதற்கு முன் வேளாண் நிபுணரிடம் உறுதிப்படுத்தவும்.",
        readAloud: "🔊 அறிக்கையைக் கேட்க",
        stop: "⏹ நிறுத்து",
        back: "வரலாற்றிற்குத் திரும்பு",
        anotherScan: "மீண்டும் பரிசோதிக்கவும்",
        translating: "மொழிபெயர்க்கப்படுகிறது...",
        translationFailed: "மொழிபெயர்ப்பு தோல்வியடைந்தது.",
        healthy: "ஆரோக்கியமானது",
        diseased: "நோய் கண்டறியப்பட்டது"
      }
    : {
        loading: "Translating report...",
        report: "ANALYSIS REPORT",
        submittedImage: "Submitted leaf sample",
        crop: "Target Crop",
        condition: "Condition",
        confidence: "Diagnostic Confidence",
        confidenceNote: "Confidence score provided by the detection model.",
        diseaseInfo: "Disease Information",
        infoDesc: "Information about the disease",
        symptoms: "Observable Symptoms",
        symptomsDesc: "Symptoms observed on the plant",
        prevention: "Preventive Measures",
        preventionDesc: "Ways to prevent disease spread",
        management: "Management & Recommended Actions",
        managementDesc: "Actions to help manage the disease",
        importantNote: "Important Agronomic Advisory Note",
        disclaimer:
          "Use this automated analysis as an initial advisory guideline. If the disease is severe or spreading rapidly, consult an agricultural expert before major treatments.",
        readAloud: "🔊 Read Aloud",
        stop: "⏹ Stop Speaking",
        back: "Back to History",
        anotherScan: "Run Another Scan",
        translating: "Translating...",
        translationFailed: "Translation failed.",
        healthy: "Healthy",
        diseased: "Disease detected"
      };

  const displayCrop = report.crop || analysis.crop || "";
  const displayDisease = report.disease || analysis.disease || "";
  const displayStatus = isTamil && translatedReport
    ? (translatedReport.status || "")
    : (analysis.status || "");

  const speakAnalysis = () => {
    if (!("speechSynthesis" in window)) {
      alert("Text-to-speech is not supported in this browser.");
      return;
    }

    if (isTamil && !translatedReport) {
      alert(
        translationLoading
          ? "Please wait for the Tamil translation."
          : "Please translate the report successfully first."
      );
      return;
    }

    window.speechSynthesis.cancel();

    const confidence = Number(analysis.confidence || 0).toFixed(1);

    const textToRead = isTamil
      ? `பயிர்: ${displayCrop}. நோய்: ${displayDisease}. நிலை: ${displayStatus}. நம்பகத்தன்மை: ${confidence} சதவீதம். நோய் விவரம்: ${advisory.description || ""}. அறிகுறிகள்: ${(advisory.symptoms || []).join(". ")}. தடுப்பு முறைகள்: ${(advisory.preventive_measures || []).join(". ")}. மேலாண்மை: ${(advisory.management || []).join(". ")}.`
      : `Crop: ${displayCrop}. Disease: ${displayDisease}. Status: ${displayStatus}. Confidence: ${confidence} percent. Disease information: ${advisory.description || ""}. Symptoms: ${(advisory.symptoms || []).join(". ")}. Preventive measures: ${(advisory.preventive_measures || []).join(". ")}. Management: ${(advisory.management || []).join(". ")}.`;

    const utterance = new SpeechSynthesisUtterance(textToRead);
    utterance.lang = language;

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
  };

  return (
    <div className="analysis-view">
      <div className="analysis-navigation-bar">
        <select
          value={language}
          onChange={(e) => {
            window.speechSynthesis?.cancel();
            setLanguage(e.target.value);
          }}
          aria-label="Select report language"
        >
          <option value="en-IN">English</option>
          <option value="ta-IN">தமிழ் (Tamil)</option>
        </select>

        <button
          type="button"
          className="btn-new-scan"
          onClick={speakAnalysis}
          disabled={isTamil && (translationLoading || !translatedReport)}
        >
          {labels.readAloud}
        </button>

        <button
          type="button"
          className="btn-back"
          onClick={stopSpeaking}
        >
          {labels.stop}
        </button>

        <button
          type="button"
          className="btn-back"
          onClick={() => navigate("/history")}
        >
          <ArrowLeft size={18} />
          <span>{labels.back}</span>
        </button>

        <Link to="/detect" className="btn-new-scan">
          <Camera size={16} />
          <span>{labels.anotherScan}</span>
        </Link>
      </div>

      {translationLoading && (
        <div className="analysis-loading-state" role="status">
          <div className="spinner" />
          <p>{labels.loading}</p>
        </div>
      )}

      {translationError && (
        <div className="alert-banner alert-error" role="alert">
          <AlertCircle size={20} />
          <span>
            {labels.translationFailed} {translationError}
          </span>
        </div>
      )}

      {/* Main Analysis Summary */}
      <div className="analysis-summary-card">
        <div className="analysis-card-grid">
          <div className="analysis-image-container">
            {analysis.image_url ? (
              <img
                src={`${API_BASE_URL}${analysis.image_url}`}
                alt={`${analysis.crop} - ${analysis.disease}`}
                className="analysis-display-image"
                onError={(e) => {
                  e.target.style.display = "none";
                  if (e.target.nextSibling) {
                    e.target.nextSibling.style.display = "flex";
                  }
                }}
              />
            ) : null}

            <div
              className="image-fallback"
              style={{
                display: analysis.image_url ? "none" : "flex"
              }}
            >
              <Layers size={40} color="#8fac95" />
              <span>Diagnostic Sample #{analysis.id}</span>
            </div>

            <span className="image-caption">
              {labels.submittedImage}
            </span>
          </div>

          <div className="analysis-overview">
            <div className="diagnostic-header-tag">
              <span className="tag-label">
                {labels.report} #{analysis.id}
              </span>
              <span className="analysis-time">
                <Calendar size={14} />
                <span>{formatDate(analysis.created_at)}</span>
              </span>
            </div>

            <h2 className="disease-title">{displayDisease}</h2>

            <div className="overview-meta-chips">
              <div className="chip">
                <span className="chip-label">{labels.crop}:</span>
                <strong className="chip-val">{displayCrop}</strong>
              </div>

              <div className="chip">
                <span className="chip-label">{labels.condition}:</span>
                <span
                  className={`status-pill ${
                    isHealthy ? "pill-healthy" : "pill-detected"
                  }`}
                >
                  {isHealthy ? (
                    <CheckCircle2 size={14} />
                  ) : (
                    <AlertTriangle size={14} />
                  )}
                  <span>
                    {displayStatus ||
                      (isHealthy ? labels.healthy : labels.diseased)}
                  </span>
                </span>
              </div>
            </div>

            <div className="confidence-section">
              <div className="confidence-label-row">
                <span className="conf-label">{labels.confidence}</span>
                <strong className="conf-percentage">
                  {Number(analysis.confidence || 0).toFixed(1)}%
                </strong>
              </div>

              <div className="confidence-track">
                <div
                  className={`confidence-fill ${
                    isHealthy ? "fill-green" : "fill-amber"
                  }`}
                  style={{
                    width: `${Math.min(
                      100,
                      Math.max(0, Number(analysis.confidence) || 0)
                    )}%`
                  }}
                />
              </div>

              <span className="conf-subtext">
                {labels.confidenceNote}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Disease Information */}
      {advisory.description && (
        <div className="advisory-card">
          <div className="advisory-header">
            <div className="icon-badge bg-blue-50">
              <Info size={20} color="#2563eb" />
            </div>
            <div>
              <h3>{labels.diseaseInfo}</h3>
              <p className="section-desc">{labels.infoDesc}</p>
            </div>
          </div>
          <p className="advisory-description-text">
            {advisory.description}
          </p>
        </div>
      )}

      {/* Symptoms */}
      {advisory.symptoms?.length > 0 && (
        <div className="advisory-card">
          <div className="advisory-header">
            <div className="icon-badge bg-amber-50">
              <AlertTriangle size={20} color="#d97706" />
            </div>
            <div>
              <h3>{labels.symptoms}</h3>
              <p className="section-desc">{labels.symptomsDesc}</p>
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

      {/* Preventive Measures */}
      {advisory.preventive_measures?.length > 0 && (
        <div className="advisory-card highlight-card">
          <div className="advisory-header">
            <div className="icon-badge bg-emerald-50">
              <ShieldCheck size={20} color="#059669" />
            </div>
            <div>
              <h3>{labels.prevention}</h3>
              <p className="section-desc">{labels.preventionDesc}</p>
            </div>
          </div>

          <ul className="action-list">
            {advisory.preventive_measures.map((measure, idx) => (
              <li key={idx}>
                <CheckCircle2
                  size={17}
                  color="#059669"
                  className="action-icon"
                />
                <span>{measure}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Management */}
      {advisory.management?.length > 0 && (
        <div className="advisory-card">
          <div className="advisory-header">
            <div className="icon-badge bg-purple-50">
              <Wrench size={20} color="#7c3aed" />
            </div>
            <div>
              <h3>{labels.management}</h3>
              <p className="section-desc">{labels.managementDesc}</p>
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

      {/* Disclaimer */}
      <div className="disclaimer-banner">
        <Info size={22} color="#4b8b5c" />
        <div>
          <h4>{labels.importantNote}</h4>
          <p>{labels.disclaimer}</p>
        </div>
      </div>
    </div>
  );
}
