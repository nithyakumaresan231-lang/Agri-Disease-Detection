import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        background: "#f5f7f4",
        color: "#2e5b3b"
      }}>
        <div className="spinner" style={{
          width: 44,
          height: 44,
          border: "4px solid #dbe8dd",
          borderTopColor: "#2e5b3b",
          borderRadius: "50%",
          animation: "spin 1s linear infinite"
        }} />
        <p style={{ marginTop: 16, fontWeight: 500 }}>Loading Agriculture Advisory...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
