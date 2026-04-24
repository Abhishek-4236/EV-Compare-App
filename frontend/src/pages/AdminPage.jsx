import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { adminAPI } from '../services/api';
import { Upload, Database, Settings, ShieldCheck, CheckCircle, AlertCircle, FileText, Activity } from 'lucide-react';
import useAuth from '../store/useAuth';

const MotionDiv = motion.div;

export default function AdminPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);
  const [stats, setStats] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchStats();
    }
  }, [user]);

  const fetchStats = async () => {
    try {
      const { data } = await adminAPI.getStats();
      setStats(data);
    } catch (err) {
      console.error("Failed to fetch stats", err);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.xlsx')) {
      setFile(selectedFile);
      setMessage(null);
    } else {
      setMessage({ type: 'error', text: 'Please select a valid .xlsx Excel file.' });
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setMessage(null);
    try {
      const { data } = await adminAPI.uploadDataset(file);
      setMessage({ type: 'success', text: data.message });
      setFile(null);
      fetchStats();
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Upload failed.' });
    } finally {
      setUploading(false);
    }
  };

  if (user?.role !== 'admin') {
    return (
      <div style={{ paddingTop: 120, textAlign: 'center' }}>
        <div style={{ color: '#ef4444', marginBottom: 20 }}><AlertCircle size={64} /></div>
        <h2 style={{ fontSize: 32, marginBottom: 16 }}>Unauthorized Access</h2>
        <p style={{ color: 'var(--text-muted)' }}>You do not have administrative privileges to access this area.</p>
      </div>
    );
  }

  return (
    <div style={{ paddingTop: 100, paddingBottom: 100, minHeight: '100vh', background: 'var(--bg)' }}>
      <div className="ev-container" style={{ maxWidth: 1000 }}>
        
        <header style={{ marginBottom: 40 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <span style={{ 
              background: 'var(--accent-soft)', color: 'var(--accent)', 
              padding: '6px 12px', borderRadius: 99, 
              fontSize: 12, fontWeight: 700, textTransform: 'uppercase' 
            }}><ShieldCheck size={14} style={{ verticalAlign: '-2px', marginRight: 4 }} /> Admin Control</span>
          </div>
          <h1 style={{ fontSize: 42, fontFamily: 'Space Grotesk', letterSpacing: '-1.5px' }}>Platform Infrastructure</h1>
        </header>

        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 30 }} className="admin-grid">
          
          <aside>
            <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 24, border: '1px solid var(--border)', position: 'sticky', top: 100 }}>
              <h3 style={{ fontSize: 16, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}><Activity size={18} color="var(--accent)" /> System Pulse</h3>
              
              <div style={{ paddingBottom: 16, borderBottom: '1px solid var(--border)', marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Total Vehicles</div>
                <div style={{ fontSize: 28, fontWeight: 800 }}>{stats?.total_vehicles || '-'}</div>
              </div>
              
              <div style={{ paddingBottom: 16, borderBottom: '1px solid var(--border)', marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>RAG DB Status</div>
                <div style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, fontSize: 14 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }}></div> Online
                </div>
              </div>

              <div style={{ fontSize: 12, color: 'var(--text-muted)', background: 'var(--bg-muted)', padding: 12, borderRadius: 12, marginTop: 24 }}>
                <strong>Note:</strong> Uploading a new dataset will wipe existing vehicle data and re-calculate AI embeddings natively.
              </div>
            </div>
          </aside>

          <main>
            <MotionDiv 
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              style={{ background: 'var(--bg-card)', padding: 40, borderRadius: 32, border: '1px solid var(--border)' }}
            >
              <h2 style={{ fontSize: 24, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
                <Database size={24} color="var(--accent)" /> Update Master Dataset
              </h2>
              <p style={{ color: 'var(--text-muted)', marginBottom: 32 }}>
                Update the vehicle knowledge base. Upload an `.xlsx` file containing the latest India EV specifications.
              </p>

              <div 
                className={`upload-zone ${file ? 'has-file' : ''}`}
                style={{ 
                  border: '2px dashed var(--border)', borderRadius: 24, padding: 48, 
                  textAlign: 'center', transition: '0.2s', position: 'relative'
                }}
              >
                <input 
                  type="file" 
                  accept=".xlsx" 
                  onChange={handleFileChange} 
                  style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }}
                />
                
                <div style={{ color: 'var(--accent)', marginBottom: 16 }}><Upload size={48} /></div>
                <h4 style={{ fontSize: 18, marginBottom: 8 }}>{file ? file.name : 'Drag & drop Excel file'}</h4>
                <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Only .xlsx format supported. Min size 10KB.</p>
              </div>

              <AnimatePresence>
                {message && (
                  <MotionDiv 
                    initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                    style={{ 
                      marginTop: 20, padding: 16, borderRadius: 12, 
                      background: message.type === 'success' ? '#10b98115' : '#ef444415',
                      color: message.type === 'success' ? '#10b981' : '#ef4444',
                      display: 'flex', gap: 10, alignItems: 'center', fontSize: 14, fontWeight: 600
                    }}
                  >
                    {message.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
                    {message.text}
                  </MotionDiv>
                )}
              </AnimatePresence>

              <button 
                onClick={handleUpload}
                disabled={!file || uploading}
                className="ev-btn ev-btn-primary"
                style={{ 
                  width: '100%', marginTop: 32, padding: 16, borderRadius: 16, 
                  justifyContent: 'center', display: 'flex', alignItems: 'center', gap: 10,
                  opacity: (!file || uploading) ? 0.5 : 1,
                  cursor: (!file || uploading) ? 'not-allowed' : 'pointer'
                }}
              >
                {uploading ? (
                  <>Processing Dataset...</>
                ) : (
                  <><Database size={18} /> Run Data Import Pipeline</>
                )}
              </button>
            </MotionDiv>

            <div style={{ marginTop: 30, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
               <div style={{ padding: 24, background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 24 }}>
                  <Settings size={20} color="var(--text-muted)" style={{ marginBottom: 14 }} />
                  <h4 style={{ fontSize: 16, marginBottom: 6 }}>Model Config</h4>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>Gemini 3 Flash enabled with 1.5M Context.</p>
               </div>
               <div style={{ padding: 24, background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 24 }}>
                  <FileText size={20} color="var(--text-muted)" style={{ marginBottom: 14 }} />
                  <h4 style={{ fontSize: 16, marginBottom: 6 }}>Export Logs</h4>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>Download detailed execution logs for analysis.</p>
               </div>
            </div>
          </main>

        </div>

      </div>

      <style>{`
        .upload-zone:hover { border-color: var(--accent); background: var(--bg-muted); }
        .upload-zone.has-file { border-color: var(--accent); background: var(--accent-soft); }
        
        @media (max-width: 800px) {
          .admin-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}
