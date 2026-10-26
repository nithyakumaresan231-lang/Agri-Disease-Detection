import React, { useState, useEffect, useRef } from "react";
import {
  Cpu,
  Thermometer,
  Droplets,
  Sun,
  Zap,
  Activity,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Radio,
  FileText,
  Info,
  Server,
  Layers,
  ChevronDown
} from "lucide-react";
import { sensorAPI } from "../services/api";

export default function SensorMonitoringPage() {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [useDemoMode, setUseDemoMode] = useState(false);
  const [lastFetchTime, setLastFetchTime] = useState(null);
  const [error, setError] = useState(null);

  const timerRef = useRef(null);

  const fetchTelemetry = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    setError(null);

    try {
      if (useDemoMode) {
        const sampleRes = await sensorAPI.getSample();
        setData(sampleRes);
        setStatus({
          server_url: "sensor_data.csv (Historical Sample)",
          is_reachable: true,
          has_data: true,
          is_stale: false,
          device_id: sampleRes.reading?.device_id || "PH-1",
          device_online: sampleRes.reading?.device_online,
          last_reading_time: sampleRes.reading?.timestamp,
          message: "Sample dataset loaded"
        });
      } else {
        const [latestRes, statusRes] = await Promise.all([
          sensorAPI.getLatest(),
          sensorAPI.getStatus()
        ]);
        setData(latestRes);
        setStatus(statusRes);
      }
      setLastFetchTime(new Date());
    } catch (err) {
      console.error("Telemetry fetch error:", err);
      setError(err.message || "Failed to communicate with sensor backend.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, [useDemoMode]);

  // Auto-refresh interval (10 seconds)
  useEffect(() => {
    if (!autoRefresh) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    timerRef.current = setInterval(() => {
      fetchTelemetry(false);
    }, 10000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [autoRefresh, useDemoMode]);

  const reading = data?.reading;
  const isOnline = data?.status === "connected";
  const isStale = data?.status === "stale" || reading?.is_stale;
  const isDemo = data?.is_demo || useDemoMode;

  const formatTimestamp = (ts) => {
    if (!ts) return "No timestamp";
    return ts;
  };

  return (
    <div className="sensor-monitoring-view">
      {/* Header */}
      <div className="sensor-page-header">
        <div>
          <div className="header-badge-row">
            <span className="telemetry-pill">
              <Cpu size={14} />
              <span>IOT TELEMETRY HUB</span>
            </span>
            {isDemo ? (
              <span className="status-pill-demo">
                <FileText size={12} />
                <span>DEMO MODE (SAMPLE DATA)</span>
              </span>
            ) : isOnline ? (
              <span className="status-pill-online">
                <Radio size={12} className="pulse-icon" />
                <span>LIVE SENSOR GATEWAY</span>
              </span>
            ) : isStale ? (
              <span className="status-pill-stale">
                <AlertTriangle size={12} />
                <span>DATA STALE (&gt;15m)</span>
              </span>
            ) : (
              <span className="status-pill-offline">
                <AlertTriangle size={12} />
                <span>SENSOR SERVER OFFLINE</span>
              </span>
            )}
          </div>
          <h2>Polyhouse Sensor Monitoring</h2>
          <p className="sensor-page-subtitle">
            Environmental microclimate and irrigation nutrient telemetry from IoT sensor nodes.
          </p>
        </div>

        {/* Action Controls */}
        <div className="sensor-actions-bar">
          <button
            type="button"
            className="btn-sensor-refresh"
            onClick={() => fetchTelemetry(true)}
            disabled={refreshing}
            title="Refresh sensor telemetry"
          >
            <RefreshCw size={15} className={refreshing ? "spin-icon" : ""} />
            <span>{refreshing ? "Updating..." : "Refresh"}</span>
          </button>

          <label className="toggle-label" title="Automatically poll every 10 seconds">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            <span>Auto-refresh (10s)</span>
          </label>

          <button
            type="button"
            className={`btn-demo-toggle ${isDemo ? "active" : ""}`}
            onClick={() => setUseDemoMode(!useDemoMode)}
          >
            {isDemo ? "Switch to Live Server" : "View Sample Data"}
          </button>
        </div>
      </div>

      {/* Demo Warning Banner */}
      {isDemo && (
        <div className="sensor-banner banner-demo">
          <Info size={18} />
          <div>
            <strong>SAMPLE / HISTORICAL DATA DEMONSTRATION</strong>
            <p>
              Displaying historical measurements from <code>sensor_data.csv</code>. This allows inspecting
              the interface structure without active greenhouse hardware. To read live measurements, toggle back to Live Server.
            </p>
          </div>
        </div>
      )}

      {/* Offline Alert Banner */}
      {!isDemo && !isOnline && !loading && (
        <div className="sensor-banner banner-offline">
          <AlertTriangle size={20} color="#b45309" />
          <div className="banner-content">
            <strong>Sensor Cloud Server Unreachable</strong>
            <p>
              The sensor backend at <code>{status?.server_url || "http://192.168.100.131:5000"}</code> is not responding.
              If the physical gateway or cloud server (<code>server.py</code>) is stopped, start it or click
              <strong> "View Sample Data"</strong> above to preview the dashboard with historical telemetry.
            </p>
          </div>
        </div>
      )}

      {/* Stale Data Alert Banner */}
      {!isDemo && isOnline && isStale && (
        <div className="sensor-banner banner-stale">
          <Clock size={18} color="#b45309" />
          <div>
            <strong>Telemetry Out of Date</strong>
            <p>
              The latest reading was received at <code>{reading?.timestamp}</code>. New telemetry packets
              have not been posted in over 15 minutes.
            </p>
          </div>
        </div>
      )}

      {/* Meta Bar */}
      <div className="telemetry-meta-bar">
        <div className="meta-block">
          <span className="meta-title">Device Node</span>
          <strong>{reading?.device_id || status?.device_id || "PH-1"}</strong>
        </div>
        <div className="meta-separator" />
        <div className="meta-block">
          <span className="meta-title">Gateway Link</span>
          <span className={reading?.device_online ? "text-green" : "text-muted"}>
            {reading?.device_online ? "Online & Transmitting" : "Device Link Inactive"}
          </span>
        </div>
        <div className="meta-separator" />
        <div className="meta-block">
          <span className="meta-title">Packet Timestamp</span>
          <strong>{formatTimestamp(reading?.timestamp)}</strong>
        </div>
        <div className="meta-separator" />
        <div className="meta-block">
          <span className="meta-title">Last Poll</span>
          <span>{lastFetchTime ? lastFetchTime.toLocaleTimeString() : "--"}</span>
        </div>
      </div>

      {loading ? (
        <div className="sensor-loading-state">
          <div className="spinner" />
          <p>Connecting to IoT sensor telemetry stream...</p>
        </div>
      ) : (
        <div className="telemetry-grid">
          {/* 1. ATMOSPHERIC / CANOPY ENVIRONMENT */}
          <div className="sensor-subsystem-card">
            <div className="subsystem-header">
              <div className="subsystem-icon bg-amber-light">
                <Thermometer size={20} color="#b45309" />
              </div>
              <div>
                <h3>Canopy Temperature</h3>
                <span className="subsystem-tag">Atmospheric Microclimate</span>
              </div>
            </div>

            <div className="primary-metric-display">
              <span className="metric-main-value">
                {reading?.temp_avg != null ? reading.temp_avg : "--"}
              </span>
              <span className="metric-main-unit">Average</span>
            </div>

            <div className="sensor-dual-subreadings">
              <div className="subreading-box">
                <span className="sub-label">Sensor 1 (T1)</span>
                <strong>{reading?.temperature1 != null ? reading.temperature1 : "--"}</strong>
              </div>
              <div className="subreading-box">
                <span className="sub-label">Sensor 2 (T2)</span>
                <strong>{reading?.temperature2 != null ? reading.temperature2 : "--"}</strong>
              </div>
            </div>
            <small className="subsystem-footnote">Measured across dual canopy temperature probes.</small>
          </div>

          {/* 2. RELATIVE HUMIDITY */}
          <div className="sensor-subsystem-card">
            <div className="subsystem-header">
              <div className="subsystem-icon bg-blue-light">
                <Droplets size={20} color="#2563eb" />
              </div>
              <div>
                <h3>Relative Humidity</h3>
                <span className="subsystem-tag">Foliar Wetness Proxy</span>
              </div>
            </div>

            <div className="primary-metric-display">
              <span className="metric-main-value">
                {reading?.humidity_avg != null ? `${reading.humidity_avg}%` : "-- %"}
              </span>
              <span className="metric-main-unit">Average RH</span>
            </div>

            <div className="sensor-dual-subreadings">
              <div className="subreading-box">
                <span className="sub-label">Sensor 1 (RH1)</span>
                <strong>{reading?.humidity1 != null ? `${reading.humidity1}%` : "--"}</strong>
              </div>
              <div className="subreading-box">
                <span className="sub-label">Sensor 2 (RH2)</span>
                <strong>{reading?.humidity2 != null ? `${reading.humidity2}%` : "--"}</strong>
              </div>
            </div>
            <small className="subsystem-footnote">Dual relative humidity sensors for condensation risk.</small>
          </div>

          {/* 3. WATER & NUTRIENT SOLUTION (FERTIGATION / HYDROPONICS) */}
          <div className="sensor-subsystem-card wide-card">
            <div className="subsystem-header">
              <div className="subsystem-icon bg-green-light">
                <Zap size={20} color="#15803d" />
              </div>
              <div>
                <h3>Irrigation &amp; Nutrient Solution</h3>
                <span className="subsystem-tag">Water Chemistry (Fertigation Tank)</span>
              </div>
            </div>

            <div className="nutrient-metrics-row">
              <div className="nutrient-item">
                <span className="nutrient-label">pH Level</span>
                <strong className="nutrient-value">{reading?.ph != null ? reading.ph : "--"}</strong>
                <small className="nutrient-status">
                  {reading?.ph != null
                    ? reading.ph < 6.0
                      ? "Acidic"
                      : reading.ph > 7.5
                      ? "Alkaline"
                      : "Optimal (6.0 - 7.5)"
                    : "No reading"}
                </small>
              </div>

              <div className="nutrient-item">
                <span className="nutrient-label">TDS (Total Dissolved)</span>
                <strong className="nutrient-value">{reading?.tds != null ? reading.tds : "--"}</strong>
                <small className="nutrient-status">Dissolved mineral solids</small>
              </div>

              <div className="nutrient-item">
                <span className="nutrient-label">EC (Conductivity)</span>
                <strong className="nutrient-value">{reading?.ec != null ? reading.ec : "--"}</strong>
                <small className="nutrient-status">Electrical conductivity</small>
              </div>

              <div className="nutrient-item">
                <span className="nutrient-label">Salinity</span>
                <strong className="nutrient-value">{reading?.salinity != null ? reading.salinity : "--"}</strong>
                <small className="nutrient-status">Saline concentration index</small>
              </div>
            </div>
            <small className="subsystem-footnote">
              Water solution quality monitoring. Note: These sensors measure irrigation liquid, not dry soil.
            </small>
          </div>

          {/* 4. SOLAR ILLUMINATION / LDR SENSORS */}
          <div className="sensor-subsystem-card">
            <div className="subsystem-header">
              <div className="subsystem-icon bg-amber-light">
                <Sun size={20} color="#d97706" />
              </div>
              <div>
                <h3>Ambient Illumination</h3>
                <span className="subsystem-tag">Solar Radiation Intensity</span>
              </div>
            </div>

            <div className="primary-metric-display">
              <span className="metric-main-value">
                {reading?.ldr1 != null ? Math.round(reading.ldr1) : "--"}
              </span>
              <span className="metric-main-unit">LDR1 Reading</span>
            </div>

            <div className="sensor-dual-subreadings">
              <div className="subreading-box">
                <span className="sub-label">Light Sensor 1</span>
                <strong>{reading?.ldr1 != null ? reading.ldr1 : "--"}</strong>
              </div>
              <div className="subreading-box">
                <span className="sub-label">Light Sensor 2</span>
                <strong>{reading?.ldr2 != null ? reading.ldr2 : "--"}</strong>
              </div>
            </div>
            <small className="subsystem-footnote">Photocell intensity for greenhouse shading adjustment.</small>
          </div>

          {/* 5. HARDWARE ARCHITECTURE & ISOLATION NOTE */}
          <div className="sensor-subsystem-card">
            <div className="subsystem-header">
              <div className="subsystem-icon bg-purple-light">
                <Layers size={20} color="#7c3aed" />
              </div>
              <div>
                <h3>System Architecture</h3>
                <span className="subsystem-tag">Independent Module</span>
              </div>
            </div>

            <div className="architecture-notes">
              <div className="arch-step">
                <span className="arch-dot" />
                <span>Physical Sensors &rarr; Gateway Device</span>
              </div>
              <div className="arch-step">
                <span className="arch-dot" />
                <span>Gateway Telemetry &rarr; Sensor Server (:5000)</span>
              </div>
              <div className="arch-step">
                <span className="arch-dot" />
                <span>FastAPI Service &rarr; Telemetry Cache</span>
              </div>
              <div className="arch-step">
                <span className="arch-dot" />
                <span>React Dashboard &rarr; Non-blocking Display</span>
              </div>
            </div>
            <small className="subsystem-footnote">
              Operates independently from Plant Disease Detection and ML models.
            </small>
          </div>
        </div>
      )}

      {/* Raw Payload Inspector (collapsible for diagnostics) */}
      {data?.raw_payload && (
        <details className="raw-payload-inspector">
          <summary>
            <span>View Raw Telemetry Payload</span>
            <ChevronDown size={14} />
          </summary>
          <pre>{JSON.stringify(data.raw_payload, null, 2)}</pre>
        </details>
      )}
    </div>
  );
}
