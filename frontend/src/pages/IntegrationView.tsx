import { useEffect, useState } from 'react';
import { api } from '../api';

const SOURCE_COLORS: Record<string, string> = {
  capture:      '#6366f1',
  insurance:    '#22c55e',
  registration: '#f59e0b',
  theft:        '#ef4444',
  ministry:     '#a855f7',
};

export default function IntegrationView() {
  const [schema, setSchema] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'mapping' | 'matching' | 'mediator'>('mapping');

  useEffect(() => {
    api.getIntegrationSchema().then(setSchema).catch(() => setSchema(null)).finally(() => setLoading(false));
  }, []);

  const keyCorrespondences = schema?.key_correspondences || [];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Integration <span>View</span></h1>
        <p className="page-subtitle">GAV schema mapping · Schema matching · Mediator architecture — aligned with IIA-1, IIA-2, IIA-3 lecture content</p>
      </div>

      {/* Architecture Diagram */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="section-header">
          <span>⎈</span>
          <h2>Mediation / Federated Architecture (IIA-1)</h2>
        </div>

        {/* Visual diagram */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0, padding: '8px 0' }}>
          {/* Global Query */}
          <div style={{ background: 'var(--color-primary-glow)', border: '2px solid var(--color-primary)', borderRadius: 12, padding: '12px 32px', fontWeight: 700, color: 'var(--color-primary)', fontSize: 14 }}>
            Global Query: SELECT * WHERE registration_number = 'UP32AB1234'
          </div>
          <div style={{ height: 20, width: 2, background: 'var(--color-primary)', margin: '0 auto' }} />

          {/* Mediator */}
          <div style={{ background: 'var(--color-surface-2)', border: '2px solid var(--color-border)', borderRadius: 16, padding: '18px 40px', textAlign: 'center', width: 'fit-content' }}>
            <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 4 }}>⎈ MEDIATOR</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Schema Mapper (GAV) · Entity Resolver · Conflict Detector</div>
          </div>
          <div style={{ height: 16, width: 2, background: 'var(--color-border)', margin: '0 auto' }} />

          {/* Decomposed sub-queries */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
            {Object.entries({
              capture:      'plate_number',
              insurance:    'registration_id',
              registration: 'vehicle_reg_no',
              theft:        'vehicle_identifier',
              ministry:     'vehicle_ref',
            }).map(([src, key]) => (
              <div key={src} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                <div style={{ height: 16, width: 2, background: SOURCE_COLORS[src] }} />
                <div style={{
                  background: `${SOURCE_COLORS[src]}18`,
                  border: `2px solid ${SOURCE_COLORS[src]}55`,
                  borderRadius: 10, padding: '10px 14px', textAlign: 'center', minWidth: 130,
                }}>
                  <div style={{ fontWeight: 700, color: SOURCE_COLORS[src], fontSize: 12, marginBottom: 3 }}>{src}.db</div>
                  <code style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'JetBrains Mono, monospace' }}>WHERE {key}</code>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>= 'UP32AB1234'</div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ height: 16, width: 2, background: 'var(--color-border)', margin: '0 auto' }} />
          {/* Result Integration */}
          <div style={{ background: 'var(--color-success-dim)', border: '2px solid rgba(34,197,94,0.4)', borderRadius: 12, padding: '12px 32px', fontWeight: 700, color: 'var(--color-success)', fontSize: 14 }}>
            ✓ Unified Vehicle View — registration_number + vehicle + insurance + security + ministry
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {(['mapping', 'matching', 'mediator'] as const).map(tab => (
          <button key={tab} className={`tab${activeTab === tab ? ' active' : ''}`} onClick={() => setActiveTab(tab)}>
            {tab === 'mapping' ? 'GAV Schema Mapping' : tab === 'matching' ? 'Schema Matching Results' : 'Query Decomposition'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-center"><div className="spinner" /></div>
      ) : activeTab === 'mapping' ? (
        <div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
              <strong style={{ color: 'var(--color-primary)' }}>Global-As-View (GAV)</strong>: The global schema attribute <code style={{ color: 'var(--color-success)' }}>registration_number</code> is defined as a view over source-local attributes. Each source reports its local key; the mediator maps them to the global concept. (IIA-3, slides 18-24)
            </div>
          </div>
          <div className="mapping-container">
            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto auto', gap: '0 16px', alignItems: 'center', marginBottom: 12, padding: '0 0 10px', borderBottom: '1px solid var(--color-border)' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Source DB</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Local Attribute</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}></div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Global Attribute</div>
            </div>
            {Object.entries(schema?.all_source_keys || {}).map(([src, localKey]: [string, any]) => (
              <div key={src} style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto auto', gap: '0 16px', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--color-border)' }}>
                <div style={{ fontWeight: 700, color: SOURCE_COLORS[src], fontSize: 13 }}>{src}.db</div>
                <div>
                  <code style={{ color: SOURCE_COLORS[src], fontFamily: 'JetBrains Mono, monospace', fontSize: 13, fontWeight: 700, background: `${SOURCE_COLORS[src]}15`, padding: '3px 10px', borderRadius: 5 }}>
                    {localKey}
                  </code>
                </div>
                <span style={{ color: 'var(--text-muted)', fontSize: 18 }}>↔</span>
                <code style={{ color: 'var(--color-success)', fontFamily: 'JetBrains Mono, monospace', fontSize: 13, fontWeight: 700, background: 'var(--color-success-dim)', padding: '3px 10px', borderRadius: 5 }}>
                  registration_number
                </code>
              </div>
            ))}
          </div>

          {/* Secondary mappings */}
          <div style={{ marginTop: 20 }}>
            <div className="card-title" style={{ marginBottom: 10 }}>All GAV Mappings</div>
            <div className="table-wrapper">
              <table className="table">
                <thead><tr><th>Global Attribute</th><th>Source</th><th>Local Attribute</th><th>Mapping Type</th></tr></thead>
                <tbody>
                  {(schema?.gav_mapping || []).map((m: any, i: number) => (
                    <tr key={i}>
                      <td><code style={{ color: 'var(--color-success)', fontSize: 12 }}>{m.global_attribute}</code></td>
                      <td><span style={{ color: SOURCE_COLORS[m.source] || 'var(--text-primary)', fontWeight: 600 }}>{m.source}</span></td>
                      <td><code style={{ color: SOURCE_COLORS[m.source] || 'var(--text-primary)', fontSize: 12 }}>{m.local_attribute}</code></td>
                      <td><span style={{ fontSize: 11, color: 'var(--color-primary)', background: 'var(--color-primary-glow)', padding: '2px 8px', borderRadius: 100 }}>{m.mapping_type}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : activeTab === 'matching' ? (
        <div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            <strong style={{ color: 'var(--color-primary)' }}>Schema Matching</strong>: Automatic discovery of correspondences between source schemas using linguistic similarity (edit distance + Jaccard + cosine bigrams). (IIA-3, slides 9-17)
          </div>
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="card-title" style={{ marginBottom: 12 }}>Key Identifier Correspondences</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
              Pairwise similarity scores between the vehicle identifier attributes across all sources. Demonstrates that despite different names, the system can automatically discover they represent the same concept.
            </div>
            <div className="table-wrapper">
              <table className="table">
                <thead><tr><th>Source 1</th><th>Attribute 1</th><th>Source 2</th><th>Attribute 2</th><th>Similarity</th><th>Match Type</th></tr></thead>
                <tbody>
                  {keyCorrespondences.map((c: any, i: number) => (
                    <tr key={i}>
                      <td style={{ color: SOURCE_COLORS[c.source1] || 'var(--text-primary)' }}>{c.source1}</td>
                      <td><code style={{ color: SOURCE_COLORS[c.source1], fontSize: 12 }}>{c.attr1}</code></td>
                      <td style={{ color: SOURCE_COLORS[c.source2] || 'var(--text-primary)' }}>{c.source2}</td>
                      <td><code style={{ color: SOURCE_COLORS[c.source2], fontSize: 12 }}>{c.attr2}</code></td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ flex: 1, height: 6, background: 'var(--color-border)', borderRadius: 3, maxWidth: 80, overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${c.similarity * 100}%`, background: c.similarity > 0.7 ? 'var(--color-success)' : c.similarity > 0.5 ? 'var(--color-warning)' : 'var(--color-danger)', borderRadius: 3 }} />
                          </div>
                          <span style={{ fontSize: 12, fontWeight: 600 }}>{(c.similarity * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${c.match_type === 'EXACT' ? 'insured' : c.match_type === 'HIGH' ? 'active' : c.match_type === 'MEDIUM' ? 'pending' : 'unknown'}`}>
                          {c.match_type}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ marginTop: 14, fontSize: 12, color: 'var(--text-muted)', background: 'var(--color-surface-2)', padding: '10px 14px', borderRadius: 8 }}>
              <strong>Hybrid Similarity Formula (IIA-3 slide 16):</strong> W_sim = 0.4 × L_sim (edit distance) + 0.3 × J_sim (Jaccard tokens) + 0.3 × C_sim (cosine bigrams)
            </div>
          </div>
        </div>
      ) : (
        <div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            <strong style={{ color: 'var(--color-primary)' }}>Query Decomposition & Federation</strong>: When a global query arrives at the mediator, it is decomposed into source-specific sub-queries using the GAV mapping. Each wrapper executes its own query independently. (IIA-1, slides 19-22)
          </div>
          <div className="card">
            <div style={{ fontWeight: 700, marginBottom: 14, color: 'var(--text-primary)' }}>
              Example: Global query for vehicle "UP32AB1234"
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ background: 'var(--color-primary-glow)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>GLOBAL QUERY (Mediator input)</div>
                <code style={{ color: 'var(--color-primary)', fontSize: 13 }}>SELECT * FROM global_vehicle WHERE registration_number = 'UP32AB1234'</code>
              </div>
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 20 }}>↓ Decompose via GAV mapping</div>
              {Object.entries({
                capture:      { key: 'plate_number',       table: 'vehicle_capture' },
                insurance:    { key: 'registration_id',    table: 'insurance_records' },
                registration: { key: 'vehicle_reg_no',     table: 'vehicle_registration' },
                theft:        { key: 'vehicle_identifier', table: 'vehicle_security_records' },
                ministry:     { key: 'vehicle_ref',        table: 'transport_reports' },
              }).map(([src, info]) => (
                <div key={src} style={{ background: `${SOURCE_COLORS[src]}12`, border: `1px solid ${SOURCE_COLORS[src]}33`, borderRadius: 8, padding: '10px 14px' }}>
                  <div style={{ fontSize: 11, color: SOURCE_COLORS[src], fontWeight: 700, marginBottom: 4, textTransform: 'uppercase' }}>{src}.db → Wrapper</div>
                  <code style={{ color: '#94a3b8', fontSize: 12 }}>
                    SELECT * FROM <span style={{ color: SOURCE_COLORS[src] }}>{info.table}</span> WHERE <span style={{ color: SOURCE_COLORS[src] }}>{info.key}</span> = 'UP32AB1234'
                  </code>
                </div>
              ))}
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 20 }}>↓ Merge + Conflict Check</div>
              <div style={{ background: 'var(--color-success-dim)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ fontSize: 11, color: 'var(--color-success)', fontWeight: 700, marginBottom: 4 }}>UNIFIED VEHICLE VIEW (output)</div>
                <code style={{ color: '#94a3b8', fontSize: 12 }}>{'{ registration_number, vehicle, registration, insurance, security, ministry, conflicts, overall_status }'}</code>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
