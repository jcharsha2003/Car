import StatusBadge from './StatusBadge';

interface UnifiedVehicleViewProps {
  data: any;
}

export default function UnifiedVehicleView({ data }: UnifiedVehicleViewProps) {
  if (!data) return null;

  const { registration_number, vehicle, registration, insurance, security, ministry,
    conflicts, overall_status, integration_metadata, requires_ministry_report } = data;

  const hasMake = vehicle?.make || vehicle?.model;

  return (
    <div>
      {/* Header */}
      <div className="vehicle-view-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Registration Number</div>
            <div className="vehicle-reg-number">{registration_number}</div>
            {hasMake && (
              <div className="vehicle-make-model">{vehicle.make} {vehicle.model}</div>
            )}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10 }}>
            <StatusBadge status={overall_status} size="lg" />
            {requires_ministry_report && (
              <div style={{ fontSize: 11, color: 'var(--color-warning)', background: 'var(--color-warning-dim)', padding: '4px 10px', borderRadius: 100, border: '1px solid rgba(245,158,11,0.3)' }}>
                ⚑ Ministry report required
              </div>
            )}
          </div>
        </div>

        {/* Sources availability */}
        <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
          {Object.entries(integration_metadata?.data_availability || {}).map(([src, avail]: [string, any]) => (
            <div key={src} style={{
              padding: '3px 10px', borderRadius: 100, fontSize: 11, fontWeight: 600,
              background: avail ? 'var(--color-success-dim)' : 'rgba(100,100,100,0.1)',
              color: avail ? 'var(--color-success)' : 'var(--text-muted)',
              border: `1px solid ${avail ? 'rgba(34,197,94,0.3)' : 'var(--color-border)'}`,
            }}>
              {avail ? '●' : '○'} {src}
            </div>
          ))}
          <div style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', marginLeft: 4 }}>
            {integration_metadata?.sources_with_data}/{integration_metadata?.sources_queried} sources have data
          </div>
        </div>
      </div>

      {/* Conflicts */}
      {conflicts?.has_conflicts && (
        <div style={{ marginBottom: 20 }}>
          <div className="section-header">
            <span>⚡</span>
            <h2 style={{ color: 'var(--color-purple)' }}>Data Conflicts Detected</h2>
          </div>
          {conflicts.conflicts.map((c: any, i: number) => (
            <div key={i} className="conflict-alert">
              <div className="conflict-icon">⚡</div>
              <div className="conflict-body">
                <div className="conflict-title">
                  {c.conflict_type} — {c.attribute}
                </div>
                <div className="conflict-detail">
                  <strong>{c.source1}</strong> reports: <code style={{ background: 'rgba(168,85,247,0.1)', padding: '1px 5px', borderRadius: 3 }}>{c.value1}</code>
                  {' '}vs{' '}
                  <strong>{c.source2}</strong> reports: <code style={{ background: 'rgba(168,85,247,0.1)', padding: '1px 5px', borderRadius: 3 }}>{c.value2}</code>
                </div>
                <div style={{ fontSize: 11, marginTop: 4, color: 'var(--color-purple)' }}>
                  Resolution: {c.resolution_strategy}
                  {c.resolved_value && ` → Using value: ${c.resolved_value}`}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Main info grid */}
      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Vehicle Details */}
        <div className="source-card">
          <div className="source-card-header">
            <div className="source-card-title">
              <span>🚗</span> Vehicle Details
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Source: registration.db → vehicle_reg_no</div>
          </div>
          {vehicle ? (
            <>
              <div className="info-row"><span className="info-key">Make</span><span className="info-value">{vehicle.make || '—'}</span></div>
              <div className="info-row"><span className="info-key">Model</span><span className="info-value">{vehicle.model || '—'}</span></div>
              <div className="info-row"><span className="info-key">Class</span><span className="info-value">{vehicle.vehicle_class || '—'}</span></div>
              <div className="info-row"><span className="info-key">Registered Color</span><span className="info-value">{vehicle.registered_color || '—'}</span></div>
              <div className="info-row"><span className="info-key">Fuel Type</span><span className="info-value">{vehicle.fuel_type || '—'}</span></div>
              <div className="info-row"><span className="info-key">Seating</span><span className="info-value">{vehicle.seating_capacity || '—'}</span></div>
            </>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>⚠ No registration record found</div>
          )}
        </div>

        {/* Registration Info */}
        <div className="source-card">
          <div className="source-card-header">
            <div className="source-card-title">
              <span>📋</span> Registration Info
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Source: registration.db</div>
          </div>
          {registration ? (
            <>
              <div className="info-row"><span className="info-key">Owner</span><span className="info-value">{registration.owner_name || '—'}</span></div>
              <div className="info-row"><span className="info-key">Reg. Date</span><span className="info-value">{registration.registration_date?.split('T')[0] || '—'}</span></div>
              <div className="info-row"><span className="info-key">Status</span><span className="info-value"><StatusBadge status={registration.registration_status || 'UNKNOWN'} /></span></div>
              <div className="info-row"><span className="info-key">RTO Office</span><span className="info-value" style={{ fontSize: 11 }}>{registration.rto_office || '—'}</span></div>
              <div className="info-row"><span className="info-key">Fitness Valid</span><span className="info-value">{registration.fitness_valid_until?.split('T')[0] || '—'}</span></div>
              <div className="info-row"><span className="info-key">Tax Valid</span><span className="info-value">{registration.tax_valid_until?.split('T')[0] || '—'}</span></div>
            </>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>⚠ No registration record found</div>
          )}
        </div>

        {/* Insurance */}
        <div className="source-card">
          <div className="source-card-header">
            <div className="source-card-title">
              <span>🛡</span> Insurance
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Source: insurance.db → registration_id</div>
          </div>
          {insurance?.insurer_name ? (
            <>
              <div className="info-row"><span className="info-key">Insurer</span><span className="info-value">{insurance.insurer_name}</span></div>
              <div className="info-row"><span className="info-key">Policy No.</span><span className="info-value mono">{insurance.policy_number}</span></div>
              <div className="info-row"><span className="info-key">Coverage</span><span className="info-value">{insurance.coverage_type}</span></div>
              <div className="info-row"><span className="info-key">Valid From</span><span className="info-value">{insurance.policy_start_date?.split('T')[0]}</span></div>
              <div className="info-row"><span className="info-key">Expires</span><span className="info-value">{insurance.policy_expiry_date?.split('T')[0]}</span></div>
              <div className="info-row"><span className="info-key">Status</span><span className="info-value"><StatusBadge status={insurance.insurance_status} /></span></div>
            </>
          ) : (
            <div style={{ color: 'var(--color-danger)', fontSize: 13, fontWeight: 600 }}>
              ✗ No insurance record found in database
            </div>
          )}
        </div>

        {/* Security / Theft */}
        <div className="source-card">
          <div className="source-card-header">
            <div className="source-card-title">
              <span>🔒</span> Security / Theft
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Source: theft.db → vehicle_identifier</div>
          </div>
          {security?.case_type ? (
            <>
              <div className="info-row"><span className="info-key">Case Type</span><span className="info-value"><StatusBadge status={security.case_type} /></span></div>
              <div className="info-row"><span className="info-key">Case Status</span><span className="info-value"><StatusBadge status={security.case_status} /></span></div>
              <div className="info-row"><span className="info-key">Reported</span><span className="info-value">{security.reported_date?.split('T')[0]}</span></div>
              {security.fir_number && <div className="info-row"><span className="info-key">FIR</span><span className="info-value mono" style={{ fontSize: 11 }}>{security.fir_number}</span></div>}
              <div className="info-row"><span className="info-key">Shredding</span><span className="info-value"><StatusBadge status={security.shredding_status || 'NOT_SCRAPPED'} /></span></div>
            </>
          ) : (
            <div style={{ color: 'var(--color-success)', fontSize: 13, fontWeight: 600 }}>
              ✓ No theft or security record found
            </div>
          )}
        </div>
      </div>

      {/* Last Capture */}
      {data.last_capture?.capture_timestamp && (
        <div className="source-card" style={{ marginBottom: 20 }}>
          <div className="source-card-header">
            <div className="source-card-title">
              <span>📷</span> Last ANPR Capture
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Source: capture.db → plate_number</div>
          </div>
          <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
            <div><div className="info-key" style={{ marginBottom: 2 }}>Timestamp</div><div style={{ fontSize: 13 }}>{data.last_capture.capture_timestamp?.split('.')[0].replace('T', ' ')}</div></div>
            <div><div className="info-key" style={{ marginBottom: 2 }}>Location</div><div style={{ fontSize: 13 }}>{data.last_capture.capture_location || '—'}</div></div>
            <div><div className="info-key" style={{ marginBottom: 2 }}>Detected Type</div><div style={{ fontSize: 13 }}>{data.last_capture.detected_vehicle_type || '—'}</div></div>
            <div><div className="info-key" style={{ marginBottom: 2 }}>Detected Color</div><div style={{ fontSize: 13 }}>{data.last_capture.detected_color || '—'}</div></div>
            <div><div className="info-key" style={{ marginBottom: 2 }}>Confidence</div><div style={{ fontSize: 13 }}>{data.last_capture.detection_confidence ? `${(data.last_capture.detection_confidence * 100).toFixed(0)}%` : '—'}</div></div>
          </div>
        </div>
      )}

      {/* Ministry */}
      <div className="source-card" style={{ marginBottom: 20 }}>
        <div className="source-card-header">
          <div className="source-card-title">
            <span>⚑</span> Ministry of Transportation
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Source: ministry.db → vehicle_ref</div>
        </div>
        {ministry?.report_type ? (
          <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
            <div><div className="info-key" style={{ marginBottom: 2 }}>Report Type</div><div style={{ fontSize: 13 }}>{ministry.report_type}</div></div>
            <div><div className="info-key" style={{ marginBottom: 2 }}>Report Date</div><div style={{ fontSize: 13 }}>{ministry.report_date?.split('T')[0]}</div></div>
            <div><div className="info-key" style={{ marginBottom: 2 }}>Severity</div><div style={{ fontSize: 13 }}><StatusBadge status={ministry.severity?.toLowerCase()} /></div></div>
            <div><div className="info-key" style={{ marginBottom: 2 }}>Status</div><div style={{ fontSize: 13 }}><StatusBadge status={ministry.report_status} /></div></div>
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>No ministry report on record</div>
        )}
      </div>

      {/* Integration Metadata */}
      <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 20, marginBottom: 20 }}>
        <div className="section-header" style={{ marginBottom: 12 }}>
          <span>⎈</span>
          <h2 style={{ fontSize: 14 }}>Integration Metadata</h2>
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>
          Query decomposed into {integration_metadata?.sources_queried} sub-queries via <strong style={{ color: 'var(--color-primary)' }}>GAV schema mapping</strong>. Each source uses a different local key for the same underlying vehicle identifier:
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {Object.entries(integration_metadata?.schema_mapping_used || {}).map(([src, localKey]: [string, any]) => (
            <div key={src} className="mapping-row">
              <span className="mapping-label">{src}</span>
              <span className="mapping-source">{localKey}</span>
              <span className="mapping-arrow">↔</span>
              <span className="mapping-global">registration_number</span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>GAV mapping</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
