import React, { useState, useEffect } from "react";
import {
  User,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Save,
  CheckCircle2,
  AlertCircle,
  Activity,
  ShieldCheck
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { profileAPI } from "../services/api";

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    location: ""
  });
  const [stats, setStats] = useState({
    total_analyses: 0,
    diseases_detected: 0,
    healthy_results: 0
  });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || "",
        phone: user.phone || "",
        location: user.location || ""
      });
    }

    async function loadStats() {
      try {
        const statsData = await profileAPI.getStats();
        setStats(statsData);
      } catch (err) {
        console.error("Failed to load user stats:", err);
      }
    }
    loadStats();
  }, [user]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess("");
    setError("");

    try {
      const updated = await profileAPI.updateProfile(formData);
      updateUser(updated);
      setSuccess("Profile information updated successfully.");
    } catch (err) {
      setError(err.message || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "long",
      year: "numeric"
    });
  };

  return (
    <div className="profile-view">
      <div className="profile-header">
        <h2>Farmer Profile</h2>
        <p>Manage your personal credentials, farm contact details, and account preferences.</p>
      </div>

      <div className="profile-layout-grid">
        {/* Left: Summary Card */}
        <div className="profile-card profile-summary-card">
          <div className="profile-avatar-large">
            {user?.name ? user.name.charAt(0).toUpperCase() : "U"}
          </div>

          <h3>{user?.name || "Farmer"}</h3>
          <span className="profile-role-badge">Agricultural Producer</span>

          <div className="profile-meta-list">
            <div className="meta-item">
              <Mail size={16} className="text-muted" />
              <span>{user?.email}</span>
            </div>

            <div className="meta-item">
              <MapPin size={16} className="text-muted" />
              <span>{user?.location || "Location not set"}</span>
            </div>

            <div className="meta-item">
              <Calendar size={16} className="text-muted" />
              <span>Member since {formatDate(user?.created_at)}</span>
            </div>
          </div>

          <div className="profile-stats-box">
            <h4>Diagnostic Summary</h4>
            <div className="stat-row">
              <span>Total Scans</span>
              <strong>{stats.total_analyses}</strong>
            </div>
            <div className="stat-row">
              <span>Diseases Flagged</span>
              <strong className="text-amber">{stats.diseases_detected}</strong>
            </div>
            <div className="stat-row">
              <span>Confirmed Healthy</span>
              <strong className="text-green">{stats.healthy_results}</strong>
            </div>
          </div>
        </div>

        {/* Right: Edit Form Card */}
        <div className="profile-card profile-form-card">
          <div className="card-header-line">
            <h3>Edit Account Details</h3>
            <span className="card-sub-hint">Keep your profile current for localized advisories</span>
          </div>

          {success && (
            <div className="alert-banner alert-success">
              <CheckCircle2 size={18} />
              <span>{success}</span>
            </div>
          )}

          {error && (
            <div className="alert-banner alert-error">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSave} className="profile-form">
            <div className="form-group">
              <label htmlFor="prof-name">Full Name</label>
              <div className="input-with-icon">
                <User size={18} className="input-icon" />
                <input
                  id="prof-name"
                  name="name"
                  type="text"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="prof-email">Email Address (Registered)</label>
              <div className="input-with-icon">
                <Mail size={18} className="input-icon" />
                <input
                  id="prof-email"
                  type="email"
                  value={user?.email || ""}
                  disabled
                  className="input-disabled"
                />
              </div>
              <small className="field-hint">Email address cannot be changed directly.</small>
            </div>

            <div className="form-group">
              <label htmlFor="prof-phone">Phone Number</label>
              <div className="input-with-icon">
                <Phone size={18} className="input-icon" />
                <input
                  id="prof-phone"
                  name="phone"
                  type="tel"
                  placeholder="+91 9876543210"
                  value={formData.phone}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="prof-location">Farm / Region Location</label>
              <div className="input-with-icon">
                <MapPin size={18} className="input-icon" />
                <input
                  id="prof-location"
                  name="location"
                  type="text"
                  placeholder="e.g. Coimbatore, Tamil Nadu"
                  value={formData.location}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="form-actions-right">
              <button
                type="submit"
                className="btn-save-profile"
                disabled={saving}
              >
                <Save size={16} />
                <span>{saving ? "Saving Changes..." : "Save Profile"}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
