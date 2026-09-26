import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Settings,
  Shield,
  Bell,
  Palette,
  LogOut,
  Database,
  ExternalLink,
  CheckCircle2
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { API_BASE_URL } from "../services/api";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [advisoryAlerts, setAdvisoryAlerts] = useState(true);
  const [themePreference, setThemePreference] = useState("light");
  const [savedNotice, setSavedNotice] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleSavePref = (e) => {
    e.preventDefault();
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  return (
    <div className="settings-view">
      <div className="settings-header">
        <h2>System Settings</h2>
        <p>Configure diagnostic options, system preferences, and authentication sessions.</p>
      </div>

      <div className="settings-container-grid">
        {/* Account & Security */}
        <div className="settings-card">
          <div className="card-header-icon">
            <Shield size={20} color="#2e5b3b" />
            <div>
              <h3>Security &amp; Account</h3>
              <p>Current active session credentials</p>
            </div>
          </div>

          <div className="setting-item-row">
            <div>
              <strong>Authenticated User</strong>
              <p className="setting-subtext">{user?.name} ({user?.email})</p>
            </div>
            <span className="badge-active">Active</span>
          </div>

          <div className="setting-item-row">
            <div>
              <strong>Session Security</strong>
              <p className="setting-subtext">JWT token authentication with encrypted hash storage</p>
            </div>
            <button
              type="button"
              className="btn-settings-logout"
              onClick={handleLogout}
            >
              <LogOut size={16} />
              <span>Log Out</span>
            </button>
          </div>
        </div>

        {/* Advisory Notifications & Preferences */}
        <div className="settings-card">
          <div className="card-header-icon">
            <Bell size={20} color="#2e5b3b" />
            <div>
              <h3>Advisory Preferences</h3>
              <p>Configure agronomic alerts and display themes</p>
            </div>
          </div>

          {savedNotice && (
            <div className="alert-banner alert-success">
              <CheckCircle2 size={16} />
              <span>Preferences saved successfully.</span>
            </div>
          )}

          <form onSubmit={handleSavePref} className="settings-pref-form">
            <div className="setting-item-row">
              <div>
                <strong>High-Risk Pathogen Warnings</strong>
                <p className="setting-subtext">Highlight urgent field containment alerts</p>
              </div>
              <input
                type="checkbox"
                checked={advisoryAlerts}
                onChange={(e) => setAdvisoryAlerts(e.target.checked)}
                className="toggle-checkbox"
              />
            </div>

            <div className="setting-item-row">
              <div>
                <strong>Application Theme</strong>
                <p className="setting-subtext">Choose your visual color theme</p>
              </div>
              <select
                value={themePreference}
                onChange={(e) => setThemePreference(e.target.value)}
                className="settings-select"
              >
                <option value="light">Agricultural Green (Light)</option>
                <option value="system">System Default</option>
              </select>
            </div>

            <div className="form-actions-right">
              <button type="submit" className="btn-save-pref">
                Save Preferences
              </button>
            </div>
          </form>
        </div>

        {/* Backend & Model Integration Info */}
        <div className="settings-card">
          <div className="card-header-icon">
            <Database size={20} color="#2e5b3b" />
            <div>
              <h3>API &amp; Engine Environment</h3>
              <p>Current architecture configuration</p>
            </div>
          </div>

          <div className="setting-item-row">
            <div>
              <strong>Backend Endpoint</strong>
              <p className="setting-subtext">{API_BASE_URL}</p>
            </div>
            <a
              href={`${API_BASE_URL}/docs`}
              target="_blank"
              rel="noreferrer"
              className="docs-link"
            >
              <span>Swagger Docs</span>
              <ExternalLink size={14} />
            </a>
          </div>

          <div className="setting-item-row">
            <div>
              <strong>Diagnostic Pipeline</strong>
              <p className="setting-subtext">Mock Prediction Service (ML drop-in ready)</p>
            </div>
            <span className="badge-pipeline">Phase 1 Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
