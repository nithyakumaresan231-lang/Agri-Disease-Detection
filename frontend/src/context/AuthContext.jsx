import React, { createContext, useContext, useState, useEffect } from "react";
import { authAPI } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem("agri_token"));
  const [loading, setLoading] = useState(true);

  // Restore authenticated session on mount
  useEffect(() => {
    async function initAuth() {
      const storedToken = localStorage.getItem("agri_token");
      if (storedToken) {
        try {
          const currentUser = await authAPI.getMe();
          setUser(currentUser);
          setToken(storedToken);
        } catch (err) {
          console.warn("Session expired or invalid token. Logging out.", err);
          localStorage.removeItem("agri_token");
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    }

    initAuth();
  }, []);

  const login = async (email, password) => {
    const data = await authAPI.login({ email, password });
    localStorage.setItem("agri_token", data.access_token);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const register = async (userData) => {
    return await authAPI.register(userData);
  };

  const logout = () => {
    localStorage.removeItem("agri_token");
    setToken(null);
    setUser(null);
  };

  const updateUser = (updatedFields) => {
    setUser((prev) => (prev ? { ...prev, ...updatedFields } : null));
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token && !!user,
    login,
    register,
    logout,
    updateUser
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
