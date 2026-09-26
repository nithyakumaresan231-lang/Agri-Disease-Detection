import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Leaf, Eye, EyeOff, Lock, Mail, AlertCircle, ArrowRight } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Registration success message state passed via route state
  const successMessage = location.state?.message;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError("Please provide both your email and password.");
      return;
    }

    setSubmitting(true);
    try {
      await login(email.trim(), password);
      // Navigate to intended destination or dashboard
      const target = location.state?.from?.pathname || "/dashboard";
      navigate(target, { replace: true });
    } catch (err) {
      setError(err.message || "Failed to sign in. Please check your credentials.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <Link to="/" className="auth-brand">
            <div className="auth-logo-icon">
              <Leaf size={26} color="#ffffff" />
            </div>
            <span>AgriAdvisory</span>
          </Link>
          <h2>Welcome Back</h2>
          <p>Sign in to monitor your crops and access your disease detection records.</p>
        </div>

        {successMessage && (
          <div className="alert-banner alert-success">
            {successMessage}
          </div>
        )}

        {error && (
          <div className="alert-banner alert-error">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <div className="input-with-icon">
              <Mail size={18} className="input-icon" />
              <input
                id="email"
                type="email"
                placeholder="farmer@agri.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
          </div>

          <div className="form-group">
            <div className="label-row">
              <label htmlFor="password">Password</label>
            </div>
            <div className="input-with-icon">
              <Lock size={18} className="input-icon" />
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={submitting}
          >
            {submitting ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <span>Sign In to Dashboard</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account yet?{" "}
            <Link to="/register" className="auth-link">
              Create an Account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
