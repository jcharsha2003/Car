import { useState, useRef } from 'react';
import { api } from '../api';
import UnifiedVehicleView from '../components/UnifiedVehicleView';

const PIPELINE_STEPS = [
  { key: 'image_loaded',         label: 'Image Loaded',                icon: '📷' },
  { key: 'vehicle_detected',     label: 'Vehicle Detection (YOLOv8)',   icon: '🚗' },
  { key: 'color_detected',       label: 'Color Detection (HSV)',        icon: '🎨' },
  { key: 'plate_region_detected',label: 'Plate Region Detection',       icon: '🔲' },
  { key: 'ocr_run',              label: 'OCR — License Plate Only',     icon: '📖' },
  { key: 'normalized',           label: 'Plate Normalized',             icon: '✓'  },
];

export default function ScanVehicle() {
  const [scanResult, setScanResult] = useState<any>(null);
  const [vehicleData, setVehicleData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const processFile = async (file: File) => {
    setLoading(true);
    setError('');
    setScanResult(null);
    setVehicleData(null);
    setPreviewUrl(URL.createObjectURL(file));
    try {
      const scan = await api.scanVehicle(file);
      setScanResult(scan);
      if (scan.plate) {
        // Automatically look up the detected plate number in all 5 databases
        const vehicle = await api.getVehicle(scan.plate);
        setVehicleData(vehicle);
      }
    } catch (e) {
      setError('Scan failed. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file?.type.startsWith('image/')) processFile(file);
  };

  const reset = () => {
    setScanResult(null);
    setVehicleData(null);
    setPreviewUrl(null);
    setError('');
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Scan <span>Vehicle</span></h1>
        <p className="page-subtitle">
          Upload a vehicle image → YOLOv8 detects vehicle → License plate extracted (OCR) → Global car details fetched from all 5 databases
        </p>
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Upload Zone */}
        <div>
          <div
            className={`upload-zone${dragging ? ' dragging' : ''}`}
            onClick={() => fileRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            {previewUrl ? (
              <div style={{ position: 'relative' }}>
                <img
                  src={previewUrl}
                  alt="Uploaded vehicle"
                  style={{ maxWidth: '100%', maxHeight: 220, borderRadius: 8, objectFit: 'contain' }}
                />
                <button
                  onClick={e => { e.stopPropagation(); reset(); }}
                  style={{
                    position: 'absolute', top: -8, right: -8,
                    background: 'var(--color-danger)',
                    border: 'none', borderRadius: '50%',
                    width: 24, height: 24,
                    color: '#fff', fontSize: 12, cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}
                  title="Clear"
                >✕</button>
              </div>
            ) : (
              <>
                <div className="upload-zone-icon">📤</div>
                <h3>Upload Vehicle Image</h3>
                <p>Drag &amp; drop or click to select<br />JPG, PNG, WebP supported</p>
                <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
                  The ANPR pipeline will extract ONLY the license plate number
                </p>
              </>
            )}
            <input
              type="file"
              ref={fileRef}
              style={{ display: 'none' }}
              accept="image/*"
              onChange={e => e.target.files?.[0] && processFile(e.target.files[0])}
            />
          </div>

          {/* Tip — direct to SQL Query page for manual search */}
          <div style={{
            marginTop: 12,
            padding: '10px 14px',
            background: 'var(--color-surface)',
            borderRadius: 10,
            border: '1px solid var(--color-border)',
            fontSize: 12,
            color: 'var(--text-muted)',
          }}>
            💡 Want to search by plate number or run SQL queries?
            Use the <a href="/query" style={{ color: 'var(--color-primary)' }}>SQL Query</a> page.
          </div>
        </div>

        {/* ANPR Pipeline Status */}
        <div>
          <div className="card-title" style={{ marginBottom: 12 }}>ANPR Pipeline</div>
          <div className="pipeline">
            {PIPELINE_STEPS.map(step => {
              const isDone = scanResult?.pipeline_stages?.[step.key] === true;
              const isActive = loading;
              return (
                <div key={step.key} className={`pipeline-step${isDone ? ' done' : isActive ? ' active' : ''}`}>
                  <div className="pipeline-dot">{isDone ? '✓' : step.icon}</div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{step.label}</div>
                    {step.key === 'ocr_run' && scanResult?.raw_ocr && (
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                        Extracted: <code style={{ color: 'var(--color-primary)' }}>{scanResult.raw_ocr}</code>
                        {' '}({(scanResult.ocr_confidence * 100).toFixed(0)}% confidence)
                      </div>
                    )}
                    {step.key === 'normalized' && scanResult?.plate && (
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                        <code style={{ color: 'var(--color-success)', fontSize: 13 }}>{scanResult.plate}</code>
                        {' '}{scanResult.is_valid_format ? '✓ Valid Indian plate format' : '⚠ Non-standard format'}
                      </div>
                    )}
                    {step.key === 'vehicle_detected' && scanResult?.vehicle_type && (
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                        {scanResult.vehicle_type} · Confidence: {(scanResult.detection_confidence * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {scanResult?.detected_color && (
            <div style={{ marginTop: 12, padding: '8px 14px', background: 'var(--color-surface-2)', borderRadius: 8, fontSize: 12 }}>
              <span style={{ color: 'var(--text-muted)' }}>Detected color: </span>
              <strong>{scanResult.detected_color}</strong>
            </div>
          )}

          {scanResult?.error && (
            <div style={{ marginTop: 12, color: 'var(--color-warning)', fontSize: 12, background: 'var(--color-warning-dim)', padding: '8px 12px', borderRadius: 8 }}>
              ⚠ {scanResult.error}
            </div>
          )}

          {scanResult && !scanResult.plate && !scanResult.error && (
            <div style={{
              marginTop: 12,
              padding: '10px 14px',
              background: 'rgba(251,191,36,0.1)',
              borderRadius: 8,
              fontSize: 12,
              color: 'var(--color-warning)',
              border: '1px solid rgba(251,191,36,0.2)',
            }}>
              ⚠ Could not extract a license plate from this image. Try a clearer photo where the plate is visible.
            </div>
          )}
        </div>
      </div>

      {error && (
        <div style={{
          color: 'var(--color-danger)',
          background: 'var(--color-danger-dim)',
          border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: 12,
          padding: '14px 18px',
          marginBottom: 20,
        }}>
          {error}
        </div>
      )}

      {loading && (
        <div className="loading-center"><div className="spinner" /><span>Processing image…</span></div>
      )}

      {/* Global vehicle view — populated from all 5 databases */}
      {vehicleData && !loading && <UnifiedVehicleView data={vehicleData} />}
    </div>
  );
}
