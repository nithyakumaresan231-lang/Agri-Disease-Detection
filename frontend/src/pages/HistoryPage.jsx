import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Search,
  Filter,
  ArrowUpDown,
  ExternalLink,
  Trash2,
  Camera,
  Calendar,
  Layers,
  Leaf,
  AlertCircle
} from "lucide-react";
import { historyAPI, API_BASE_URL } from "../services/api";

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Filters and sorting
  const [search, setSearch] = useState("");
  const [cropFilter, setCropFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState("desc");

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await historyAPI.getAll({
        search: search.trim() || undefined,
        crop: cropFilter !== "all" ? cropFilter : undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        sort: sortOrder
      });
      setHistory(data);
    } catch (err) {
      console.error("Failed to load history:", err);
      setError("Failed to load detection records.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [cropFilter, statusFilter, sortOrder]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadHistory();
  };

  const handleDelete = async (id, e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this diagnostic record from your history?")) {
      return;
    }

    try {
      await historyAPI.delete(id);
      setHistory((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      alert("Could not delete the record: " + err.message);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  };

  return (
    <div className="history-view">
      <div className="view-header-row">
        <div>
          <h2>Detection History</h2>
          <p>Review and audit previous foliar scans, diagnoses, and crop advisories.</p>
        </div>

        <Link to="/detect" className="btn-action-primary">
          <Camera size={16} />
          <span>New Analysis</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="filter-panel">
        <form className="search-form" onSubmit={handleSearchSubmit}>
          <div className="search-input-box">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              placeholder="Search by crop, disease name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-search-submit">
            Search
          </button>
        </form>

        <div className="filter-controls">
          <div className="filter-select-group">
            <Filter size={15} className="filter-icon" />
            <select
              value={cropFilter}
              onChange={(e) => setCropFilter(e.target.value)}
              aria-label="Filter by Crop"
            >
              <option value="all">All Crops</option>
              <option value="Tomato">Tomato</option>
              <option value="Potato">Potato</option>
              <option value="Pepper">Bell Pepper</option>
            </select>
          </div>

          <div className="filter-select-group">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              aria-label="Filter by Status"
            >
              <option value="all">All Statuses</option>
              <option value="Healthy">Healthy</option>
              <option value="Disease Detected">Disease Detected</option>
            </select>
          </div>

          <div className="filter-select-group">
            <ArrowUpDown size={15} className="filter-icon" />
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              aria-label="Sort Order"
            >
              <option value="desc">Newest First</option>
              <option value="asc">Oldest First</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="alert-banner alert-error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* History Table or Empty State */}
      {loading ? (
        <div className="loading-placeholder">
          <div className="spinner" />
          <p>Retrieving diagnostic records...</p>
        </div>
      ) : history.length === 0 ? (
        <div className="empty-state-card">
          <Leaf size={48} color="#7fa586" />
          <h3>No analyses yet</h3>
          <p>Start your first disease detection by capturing or uploading a crop leaf image.</p>
          <Link to="/detect" className="btn-empty-action">
            <Camera size={18} />
            <span>Detect Crop Disease</span>
          </Link>
        </div>
      ) : (
        <div className="table-card">
          <div className="table-responsive">
            <table className="history-table">
              <thead>
                <tr>
                  <th>Sample</th>
                  <th>Date</th>
                  <th>Crop</th>
                  <th>Condition / Disease</th>
                  <th>Confidence</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => {
                  const isHealthy = item.status?.toLowerCase() === "healthy";
                  return (
                    <tr key={item.id}>
                      <td>
                        <div className="table-thumb-box">
                          {item.image_url ? (
                            <img
                              src={`${API_BASE_URL}${item.image_url}`}
                              alt={item.crop}
                              className="table-thumb"
                              onError={(e) => {
                                e.target.style.display = "none";
                              }}
                            />
                          ) : (
                            <Layers size={18} color="#718076" />
                          )}
                        </div>
                      </td>
                      <td className="text-muted">{formatDate(item.created_at)}</td>
                      <td>
                        <strong>{item.crop}</strong>
                      </td>
                      <td className="fw-medium">{item.disease}</td>
                      <td>
                        <div className="confidence-pill">
                          <div
                            className="confidence-mini-bar"
                            style={{ width: `${item.confidence}%` }}
                          />
                          <span>{item.confidence.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td>
                        <span
                          className={`status-badge ${
                            isHealthy ? "badge-healthy" : "badge-detected"
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td>
                        <div className="table-actions-cell">
                          <Link
                            to={`/analysis/${item.id}`}
                            className="btn-table-view"
                            title="Open full analysis"
                          >
                            <span>View</span>
                            <ExternalLink size={13} />
                          </Link>

                          <button
                            type="button"
                            className="btn-table-del"
                            onClick={(e) => handleDelete(item.id, e)}
                            title="Delete record"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
