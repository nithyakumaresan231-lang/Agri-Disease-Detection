import React from "react";
import { Link } from "react-router-dom";
import {
  Leaf,
  Camera,
  Search,
  ShieldCheck,
  Cpu,
  ArrowRight,
  CheckCircle2,
  Activity,
  ChevronRight,
  BookOpen
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function LandingPage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="landing-page">
      {/* Navigation Header */}
      <header className="landing-nav">
        <div className="landing-brand">
          <div className="landing-logo">
            <Leaf size={24} color="#2e5b3b" />
          </div>
          <div>
            <span className="brand-name">Agriculture Advisory System</span>
            <span className="brand-sub">Crop Disease Detection & Advisory</span>
          </div>
        </div>

        <nav className="landing-links">
          <a href="#about" className="landing-nav-link">About</a>
          <a href="#workflow" className="landing-nav-link">How It Works</a>
          <a href="#crops" className="landing-nav-link">Supported Crops</a>

          {isAuthenticated ? (
            <Link to="/dashboard" className="cta-primary-sm">
              Dashboard
            </Link>
          ) : (
            <div className="auth-btns-group">
              <Link to="/login" className="cta-secondary-sm">
                Login
              </Link>
              <Link to="/register" className="cta-primary-sm">
                Register
              </Link>
            </div>
          )}
        </nav>
      </header>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="hero-content">
          <div className="hero-pill">
            <Leaf size={14} />
            <span>AI-POWERED PRECISION AGRICULTURE</span>
          </div>

          <h1 className="hero-heading">
            Smart Crop Disease Detection &amp; <span>Agricultural Advisory</span>
          </h1>

          <p className="hero-description">
            Empowering farmers and agronomists to protect crop yield. Instantly identify plant
            diseases by capturing or uploading leaf images and receive verified agronomic
            preventive measures before infections spread.
          </p>

          <div className="hero-cta-group">
            <Link to={isAuthenticated ? "/detect" : "/register"} className="btn-hero-primary">
              <span>Get Started</span>
              <ArrowRight size={18} />
            </Link>
            {!isAuthenticated && (
              <Link to="/login" className="btn-hero-secondary">
                <span>Sign In to Account</span>
              </Link>
            )}
          </div>

          <div className="hero-stats-bar">
            <div className="stat-item">
              <strong>94%+</strong>
              <span>Target Accuracy</span>
            </div>
            <div className="stat-separator" />
            <div className="stat-item">
              <strong>8 Classes</strong>
              <span>Key Solanaceae Crops</span>
            </div>
            <div className="stat-separator" />
            <div className="stat-item">
              <strong>Phase 2 Ready</strong>
              <span>Soil &amp; Weather Sensors</span>
            </div>
          </div>
        </div>
      </section>

      {/* System Workflow Section */}
      <section id="workflow" className="workflow-section">
        <div className="section-intro">
          <span className="section-tag">PRECISION PROCESS</span>
          <h2>Visual Disease Detection Workflow</h2>
          <p>
            Seamless end-to-end guidance from real-time field photography to actionable crop protection.
          </p>
        </div>

        <div className="workflow-grid">
          <div className="workflow-step-card">
            <div className="step-num">01</div>
            <div className="step-icon-box bg-green-50">
              <Camera size={28} color="#2e5b3b" />
            </div>
            <h3>Camera / Upload</h3>
            <p>
              Snap a clear photo of the symptomatic leaf directly from your smartphone or webcam, or drag &amp; drop an existing image file.
            </p>
          </div>

          <div className="workflow-connector">
            <ChevronRight size={26} color="#a0b8a6" />
          </div>

          <div className="workflow-step-card">
            <div className="step-num">02</div>
            <div className="step-icon-box bg-emerald-50">
              <Leaf size={28} color="#059669" />
            </div>
            <h3>Leaf Preprocessing</h3>
            <p>
              Standardizes resolution to 224×224 RGB, isolates leaf foliage, and validates image clarity for model assessment.
            </p>
          </div>

          <div className="workflow-connector">
            <ChevronRight size={26} color="#a0b8a6" />
          </div>

          <div className="workflow-step-card">
            <div className="step-num">03</div>
            <div className="step-icon-box bg-blue-50">
              <Search size={28} color="#2563eb" />
            </div>
            <h3>Disease Detection</h3>
            <p>
              High-confidence multi-class classification identifies pathogenic foliar conditions such as Early Blight, Late Blight, or Bacterial Spot.
            </p>
          </div>

          <div className="workflow-connector">
            <ChevronRight size={26} color="#a0b8a6" />
          </div>

          <div className="workflow-step-card">
            <div className="step-num">04</div>
            <div className="step-icon-box bg-amber-50">
              <ShieldCheck size={28} color="#d97706" />
            </div>
            <h3>Advisory &amp; Prevention</h3>
            <p>
              Receive structured preventive recommendations, symptom checklists, and integrated field management guidance saved to your history.
            </p>
          </div>
        </div>
      </section>

      {/* Supported Crops Showcase */}
      <section id="crops" className="crops-section">
        <div className="section-intro">
          <span className="section-tag">SPECIES COVERAGE</span>
          <h2>Target Solanaceous Crops</h2>
          <p>Trained and calibrated for economically vital vegetable varieties.</p>
        </div>

        <div className="crops-grid">
          <div className="crop-card">
            <div className="crop-badge">Tomato</div>
            <h3>Solanum lycopersicum</h3>
            <p>Diagnoses Early Blight (Alternaria solani), Late Blight (Phytophthora infestans), and confirms healthy leaves.</p>
            <ul className="crop-features">
              <li><CheckCircle2 size={16} color="#2e5b3b" /> Target-spot concentric ring detection</li>
              <li><CheckCircle2 size={16} color="#2e5b3b" /> Water-soaked lesion analysis</li>
            </ul>
          </div>

          <div className="crop-card">
            <div className="crop-badge">Potato</div>
            <h3>Solanum tuberosum</h3>
            <p>Monitors foliar dieback, tuber rot risk warnings, and distinguishes healthy growth from aggressive blight.</p>
            <ul className="crop-features">
              <li><CheckCircle2 size={16} color="#2e5b3b" /> Stem lesion early notification</li>
              <li><CheckCircle2 size={16} color="#2e5b3b" /> Tuber protection protocols</li>
            </ul>
          </div>

          <div className="crop-card">
            <div className="crop-badge">Bell Pepper</div>
            <h3>Capsicum annuum</h3>
            <p>Detects Bacterial Leaf Spot (Xanthomonas campestris) and verifies leaf canopy integrity.</p>
            <ul className="crop-features">
              <li><CheckCircle2 size={16} color="#2e5b3b" /> Shot-hole lesion profiling</li>
              <li><CheckCircle2 size={16} color="#2e5b3b" /> Fruit sunscald prevention guidelines</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Architecture & Future Sensors */}
      <section id="about" className="about-sensors-section">
        <div className="sensors-preview-card">
          <div className="sensors-info">
            <div className="sensor-tag">
              <Cpu size={15} />
              <span>PHASE 2 HARDWARE READY</span>
            </div>
            <h2>Environmental Sensor Fusion</h2>
            <p>
              Crop disease outbreaks correlate heavily with ambient humidity, canopy micro-temperatures,
              and prolonged soil saturation. Our architecture includes ready hooks to fuse real-time IoT
              sensor streams directly into the diagnostic engine.
            </p>
            <div className="sensor-specs">
              <div className="sensor-spec-box">
                <span className="spec-label">Temperature</span>
                <span className="spec-status">Ready for Sensor Bus</span>
              </div>
              <div className="sensor-spec-box">
                <span className="spec-label">Relative Humidity</span>
                <span className="spec-status">Blight Risk Thresholds</span>
              </div>
              <div className="sensor-spec-box">
                <span className="spec-label">Soil Moisture</span>
                <span className="spec-status">Irrigation Monitoring</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-left">
            <div className="brand-badge-footer">
              <Leaf size={18} color="#4b8b5c" />
              <strong>Agriculture Advisory System</strong>
            </div>
            <p>Empowering sustainable farming and early plant disease intervention.</p>
          </div>
          <div className="footer-right">
            <Link to="/login">Sign In</Link>
            <Link to="/register">Create Account</Link>
            <Link to="/detect">Disease Detection</Link>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2026 Agriculture Advisory System. Built for Modern Agricultural Precision.</p>
        </div>
      </footer>
    </div>
  );
}
