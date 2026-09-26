import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Leaf,
  Eye,
  EyeOff,
  Lock,
  Mail,
  User,
  Phone,
  MapPin,
  AlertCircle,
  ArrowRight
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirm_password: "",
    phone: "",
    location: ""
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Front-end validations
    if (!formData.name.trim()) {
      setError("Please enter your full name.");
      return;
    }

    if (!formData.email.trim()) {
      setError("Please enter a valid email address.");
      return;
    }

    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (formData.password !== formData.confirm_password) {
      setError("Passwords do not match. Please verify.");
      return;
    }

    setSubmitting(true);
    try {
      await register({
        name: formData.name.trim(),
        email: formData.email.trim(),
        password: formData.password,
        confirm_password: formData.confirm_password,
        phone: formData.phone.trim() || undefined,
        location: formData.location.trim() || undefined
      });

      // Redirect to login with success message
      navigate("/login", {
        state: { message: "Account created successfully! You can now log in." }
      });
    } catch (err) {
      setError(err.message || "Failed to create account. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container auth-container-wide">
        <div className="auth-header">
          <Link to="/" className="auth-brand">
            <div className="auth-logo-icon">
              <Leaf size={26} color="#ffffff" />
            </div>
            <span>AgriAdvisory</span>
          </Link>
          <h2>Create Farmer Account</h2>
          <p>Join the smart agricultural advisory network to detect plant diseases early.</p>
        </div>

        {error && (
          <div className="alert-banner alert-error">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-grid-2">
            <div className="form-group">
              <label htmlFor="name">Full Name *</label>
              <div className="input-with-icon">
                <User size={18} className="input-icon" />
                <input
                  id="name"
                  name="name"
                  type="text"
                  placeholder="e.g. Ramesh Kumar"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address *</label>
              <div className="input-with-icon">
                <Mail size={18} className="input-icon" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="farmer@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label htmlFor="password">Password * (min 6 characters)</label>
              <div className="input-with-icon">
                <Lock size={18} className="input-icon" />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Create strong password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                />
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="confirm_password">Confirm Password *</label>
              <div className="input-with-icon">
                <Lock size={18} className="input-icon" />
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Confirm password"
                  value={formData.confirm_password}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label htmlFor="phone">Phone Number (Optional)</label>
              <div className="input-with-icon">
                <Phone size={18} className="input-icon" />
                <input
                  id="phone"
                  name="phone"
                  type="tel"
                  placeholder="+91 9876543210"
                  value={formData.phone}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="location">Farm / Region Location (Optional)</label>
              <div className="input-with-icon">
                <MapPin size={18} className="input-icon" />
                <input
                  id="location"
                  name="location"
                  type="text"
                  placeholder="e.g. Coimbatore, Tamil Nadu"
                  value={formData.location}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={submitting}
          >
            {submitting ? (
              <span>Creating Account...</span>
            ) : (
              <>
                <span>Complete Registration</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{" "}
            <Link to="/login" className="auth-link">
              Sign In Instead
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
