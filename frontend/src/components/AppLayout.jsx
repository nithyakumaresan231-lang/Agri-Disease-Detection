import React, { useState } from "react";
import { NavLink, Outlet, useNavigate, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Camera,
  History,
  User,
  Settings,
  LogOut,
  Menu,
  X,
  Leaf,
  ChevronRight
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function AppLayout() {
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { label: "Disease Detection", path: "/detect", icon: Camera },
    { label: "History", path: "/history", icon: History },
    { label: "Profile", path: "/profile", icon: User },
    { label: "Settings", path: "/settings", icon: Settings },
  ];

  // Helper to format current page title
  const getPageTitle = () => {
    const pathname = location.pathname;
    if (pathname.startsWith("/detect")) return "Disease Detection";
    if (pathname.startsWith("/analysis")) return "Analysis Result";
    if (pathname.startsWith("/history")) return "Detection History";
    if (pathname.startsWith("/profile")) return "User Profile";
    if (pathname.startsWith("/settings")) return "Settings";
    return "Dashboard";
  };

  return (
    <div className="layout-root">
      {/* Mobile backdrop */}
      {mobileMenuOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${mobileMenuOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <div className="brand-badge">
            <div className="brand-logo-icon">
              <Leaf size={22} color="#ffffff" />
            </div>
            <div>
              <h2 className="brand-title">AgriAdvisory</h2>
              <span className="brand-tag">Smart Crop Health</span>
            </div>
          </div>
          <button
            className="mobile-close-btn"
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <span className="nav-group-label">MAIN NAVIGATION</span>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `nav-item ${isActive ? "active" : ""}`
                }
                onClick={() => setMobileMenuOpen(false)}
              >
                <Icon size={19} className="nav-icon" />
                <span>{item.label}</span>
                <ChevronRight size={15} className="nav-arrow" />
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="user-mini-card">
            <div className="user-avatar">
              {user?.name ? user.name.charAt(0).toUpperCase() : "U"}
            </div>
            <div className="user-info-text">
              <strong className="user-name">{user?.name || "Farmer"}</strong>
              <small className="user-email">{user?.email}</small>
            </div>
          </div>

          <button className="logout-btn" onClick={handleLogout}>
            <LogOut size={17} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-viewport">
        {/* Top bar */}
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="hamburger-btn"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu size={22} />
            </button>
            <h1 className="page-header-title">{getPageTitle()}</h1>
          </div>

          <div className="topbar-right">
            <NavLink to="/detect" className="quick-detect-btn">
              <Camera size={16} />
              <span>New Detection</span>
            </NavLink>

            <NavLink to="/profile" className="profile-pill">
              <div className="pill-avatar">
                {user?.name ? user.name.charAt(0).toUpperCase() : "U"}
              </div>
              <span className="pill-name">{user?.name || "My Account"}</span>
            </NavLink>
          </div>
        </header>

        {/* Dynamic page content */}
        <main className="content-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
