import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  Camera,
  X,
  AlertCircle,
  Cpu,
  RefreshCw,
  CheckCircle2,
  FileText,
  Thermometer,
  Droplets,
  Wind
} from "lucide-react";
import { predictionAPI } from "../services/api";

export default function DetectionPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [fileSize, setFileSize] = useState("");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Webcam state
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const videoRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  // Clean up media stream on unmount
  useEffect(() => {
    return () => {
      stopCameraStream();
    };
  }, []);

  const stopCameraStream = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const startCamera = async () => {
    setError("");
    setCameraError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video:true
      });
      mediaStreamRef.current = stream;
      setIsCameraActive(true);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Camera access error:", err);
      setCameraError(
        "Camera permission denied or camera not found. Please verify browser permissions or use file upload."
      );
    }
  };

  // Sync video element when camera is activated
  useEffect(() => {
    if (isCameraActive && videoRef.current && mediaStreamRef.current) {
      videoRef.current.srcObject = mediaStreamRef.current;
    }
  }, [isCameraActive]);

  const capturePhoto = () => {
    if (!videoRef.current) return;

    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], `webcam_leaf_${Date.now()}.jpg`, {
        type: "image/jpeg"
      });
      processFile(file);
      stopCameraStream();
    }, "image/jpeg", 0.95);
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const processFile = (file) => {
    if (!file) return;

    const validTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
    if (!validTypes.includes(file.type.toLowerCase())) {
      setError("Please upload a valid JPG, JPEG or PNG image.");
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setError("File size exceeds 15MB limit. Please upload a smaller image.");
      return;
    }

    setError("");
    setSelectedFile(file);
    setFileSize(formatBytes(file.size));
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  };

  const handleFileInput = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setFileSize("");
    setError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handlePredict = async () => {
    if (!selectedFile) {
      setError("Please upload or capture a crop leaf image before requesting detection.");
      return;
    }

    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const result = await predictionAPI.predict(formData);
      // Navigate straight to analysis detail result view
      navigate(`/analysis/${result.id}`, { state: { result } });
    } catch (err) {
      console.error("Prediction error:", err);
      setError(
        err.message || "Unable to connect to the prediction service. Please check your connection."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="detection-view">
      <div className="detection-header">
        <h2>Crop Disease Detection</h2>
        <p>Upload or capture a clear image of a crop leaf to identify foliar pathogens.</p>
      </div>

      {error && (
        <div className="alert-banner alert-error">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Main Detection Card */}
      <div className="detection-card">
        <div className="card-top-bar">
          <h3>Leaf Image Input</h3>
          <span className="status-indicator">
            <span className="status-dot" />
            {isCameraActive ? "Webcam Active" : "Diagnostic Ready"}
          </span>
        </div>

        {/* WEBCAM ACTIVE MODAL / PANEL */}
        {isCameraActive ? (
          <div className="webcam-container">
            <div className="video-wrapper">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="webcam-video"
              />
            </div>

            <div className="webcam-actions">
              <button
                type="button"
                className="btn-capture"
                onClick={capturePhoto}
              >
                <Camera size={20} />
                <span>Capture Image</span>
              </button>
              <button
                type="button"
                className="btn-cancel-cam"
                onClick={stopCameraStream}
              >
                Cancel
              </button>
            </div>
          </div>
        ) : !previewUrl ? (
          /* METHOD A & B INPUT CONTAINER */
          <div
            className={`drop-zone ${dragging ? "dragging" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="upload-icon-box">
              <Upload size={32} color="#2e5b3b" />
            </div>

            <h3>Drag &amp; drop your crop image here</h3>
            <p>or browse from your computer</p>

            <div className="input-methods-row" onClick={(e) => e.stopPropagation()}>
              <button
                type="button"
                className="btn-input-secondary"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload size={17} />
                <span>Upload Image</span>
              </button>

              <button
                type="button"
                className="btn-input-camera"
                onClick={startCamera}
              >
                <Camera size={17} />
                <span>Open Camera</span>
              </button>
            </div>

            {cameraError && (
              <p className="camera-error-text">{cameraError}</p>
            )}

            <small className="file-hints">
              Supported Formats: JPG, JPEG, PNG (Max 15MB)
            </small>
          </div>
        ) : (
          /* PREVIEW SELECTED / CAPTURED IMAGE */
          <div className="preview-container">
            <div className="preview-image-box">
              <img
                src={previewUrl}
                alt="Selected crop leaf preview"
                className="preview-img"
              />
              <button
                type="button"
                className="btn-remove-preview"
                onClick={clearSelection}
                title="Remove image"
                disabled={loading}
              >
                <X size={18} />
              </button>
            </div>

            <div className="preview-meta">
              <div className="meta-row">
                <FileText size={18} color="#2e5b3b" />
                <div>
                  <strong>{selectedFile?.name || "leaf_sample.jpg"}</strong>
                  <p>{fileSize} • Image ready for diagnostic evaluation</p>
                </div>
              </div>

              <div className="preview-actions">
                <button
                  type="button"
                  className="btn-predict"
                  onClick={handlePredict}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <RefreshCw size={18} className="spinner-icon" />
                      <span>Analyzing leaf image...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={18} />
                      <span>Detect Disease</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  className="btn-reselect"
                  onClick={clearSelection}
                  disabled={loading}
                >
                  Change Image
                </button>
              </div>
            </div>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/jpg,image/webp"
          style={{ display: "none" }}
          onChange={handleFileInput}
        />
      </div>

      {/* OPTIONAL SENSOR SECTION (PHASE 2) */}
      <div className="sensors-card">
        <div className="sensors-header">
          <div>
            <span className="phase2-tag">PHASE 2</span>
            <h3>Environmental Sensors</h3>
            <p className="sensor-subtitle">
              Microclimate telemetry fusion for multi-factor pathogen forecasting.
            </p>
          </div>
          <span className="integration-badge">
            <Cpu size={14} />
            <span>Sensor integration — Coming in Phase 2</span>
          </span>
        </div>

        <div className="sensors-grid">
          <div className="sensor-item">
            <div className="sensor-item-top">
              <span className="sensor-name">Temperature</span>
              <Thermometer size={18} color="#d97706" />
            </div>
            <strong className="sensor-val">-- °C</strong>
            <small className="sensor-hint">Canopy ambient reading</small>
          </div>

          <div className="sensor-item">
            <div className="sensor-item-top">
              <span className="sensor-name">Humidity</span>
              <Droplets size={18} color="#2563eb" />
            </div>
            <strong className="sensor-val">-- %</strong>
            <small className="sensor-hint">Relative leaf wetness proxy</small>
          </div>

          <div className="sensor-item">
            <div className="sensor-item-top">
              <span className="sensor-name">Soil Moisture</span>
              <Wind size={18} color="#16a34a" />
            </div>
            <strong className="sensor-val">-- %</strong>
            <small className="sensor-hint">Root-zone volumetric water</small>
          </div>
        </div>
      </div>
    </div>
  );
}
