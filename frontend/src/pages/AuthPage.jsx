import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Eye, EyeOff, Mail, Lock, User, ArrowRight, CheckCircle } from 'lucide-react';
import { authAPI } from '../services/api';
import useAuth from '../store/useAuth';

const MotionDiv = motion.div;

function InputField({ icon, type, placeholder, value, onChange, error, showToggle, onToggle, showPassword }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        border: `1.5px solid ${error ? '#ef4444' : 'var(--border)'}`,
        borderRadius: 12,
        background: 'color-mix(in srgb, var(--bg-card) 95%, white)',
        transition: 'border-color 0.2s, box-shadow 0.2s',
      }}
        className="auth-input-wrap"
      >
        {icon && <span style={{ position: 'absolute', left: 14, color: 'var(--text-muted)', flexShrink: 0 }}>{icon}</span>}
        <input
          type={showToggle ? (showPassword ? 'text' : 'password') : type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={type === 'password' ? 'current-password' : type === 'email' ? 'email' : 'name'}
          style={{
            flex: 1,
            border: 'none',
            outline: 'none',
            background: 'transparent',
            padding: '13px 14px 13px 40px',
            fontSize: 14,
            color: 'var(--text)',
            width: '100%',
          }}
        />
        {showToggle && (
          <button
            type="button"
            onClick={onToggle}
            style={{ position: 'absolute', right: 12, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 4 }}
          >
            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
      {error && <p style={{ fontSize: 12, color: '#ef4444', marginTop: 4, paddingLeft: 4 }}>{error}</p>}
    </div>
  );
}

function PasswordStrength({ password }) {
  if (!password) return null;
  const checks = [
    { label: '8+ characters', pass: password.length >= 8 },
    { label: 'Has number', pass: /\d/.test(password) },
    { label: 'Has uppercase', pass: /[A-Z]/.test(password) },
    { label: 'Has special char', pass: /[^a-zA-Z0-9]/.test(password) },
  ];
  const score = checks.filter(c => c.pass).length;
  const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e'];
  const labels = ['Weak', 'Fair', 'Good', 'Strong'];

  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
        {[0, 1, 2, 3].map(i => (
          <div key={i} style={{
            flex: 1, height: 3, borderRadius: 99,
            background: i < score ? colors[score - 1] : 'var(--border)',
            transition: 'background 0.3s',
          }} />
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {checks.map(c => (
            <span key={c.label} style={{ fontSize: 11, color: c.pass ? '#22c55e' : 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 3 }}>
              {c.pass ? <CheckCircle size={10} /> : '○'} {c.label}
            </span>
          ))}
        </div>
        {score > 0 && <span style={{ fontSize: 11, fontWeight: 700, color: colors[score - 1] }}>{labels[score - 1]}</span>}
      </div>
    </div>
  );
}

export default function AuthPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' });
  const [errors, setErrors] = useState({});
  const [globalError, setGlobalError] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  function setField(key, val) {
    setForm(f => ({ ...f, [key]: val }));
    setErrors(e => ({ ...e, [key]: '' }));
    setGlobalError('');
  }

  function validate() {
    const errs = {};
    if (mode === 'signup' && !form.full_name.trim()) errs.full_name = 'Name is required';
    if (!form.email.includes('@')) errs.email = 'Enter a valid email address';
    if (form.password.length < 8) errs.password = 'Password must be at least 8 characters';
    if (mode === 'signup' && form.password !== form.confirm) errs.confirm = 'Passwords do not match';
    return errs;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setLoading(true);
    setGlobalError('');
    try {
      const payload = mode === 'login'
        ? { email: form.email, password: form.password }
        : { full_name: form.full_name.trim(), email: form.email, password: form.password };

      const res = await (mode === 'login' ? authAPI.login(payload) : authAPI.signup(payload));
      const { access_token, user } = res.data;

      setSuccess(true);
      login(access_token, user);
      setTimeout(() => navigate('/'), 800);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setGlobalError(typeof detail === 'string' ? detail : 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  function switchMode() {
    setMode(m => m === 'login' ? 'signup' : 'login');
    setErrors({});
    setGlobalError('');
    setForm({ full_name: '', email: '', password: '', confirm: '' });
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 20px',
      background: `
        radial-gradient(circle at 20% 20%, rgba(14,165,164,0.12), transparent 40%),
        radial-gradient(circle at 80% 80%, rgba(14,165,164,0.08), transparent 40%),
        var(--bg)
      `,
    }}>
      {/* Animated background blobs */}
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, overflow: 'hidden', zIndex: 0, pointerEvents: 'none' }}>
        <motion.div
          animate={{ scale: [1, 1.15, 1], opacity: [0.06, 0.1, 0.06] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
          style={{ position: 'absolute', top: '-15%', left: '-10%', width: 600, height: 600, borderRadius: '50%', background: 'var(--accent)' }}
        />
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.04, 0.08, 0.04] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
          style={{ position: 'absolute', bottom: '-20%', right: '-5%', width: 500, height: 500, borderRadius: '50%', background: 'var(--accent)' }}
        />
      </div>

      <MotionDiv
        key={mode}
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -16, scale: 0.97 }}
        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
        style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 440 }}
      >
        {/* Card */}
        <div style={{
          background: 'rgba(255,255,255,0.07)',
          backdropFilter: 'blur(28px)',
          WebkitBackdropFilter: 'blur(28px)',
          border: '1px solid rgba(255,255,255,0.14)',
          borderRadius: 24,
          padding: '40px 36px',
          boxShadow: '0 32px 80px rgba(0,0,0,0.18)',
        }}>
          {/* Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 32 }}>
            <div style={{
              width: 40, height: 40, borderRadius: 12,
              background: 'linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent) 60%, #0284c7))',
              display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white',
              boxShadow: '0 8px 20px rgba(14,165,164,0.35)',
            }}>
              <Zap size={20} fill="white" />
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: 18, letterSpacing: '-0.5px', color: 'var(--text)' }}>EViq</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>India EV Platform</div>
            </div>
          </div>

          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 26, fontWeight: 800, color: 'var(--text)', marginBottom: 6, letterSpacing: '-0.5px' }}>
            {mode === 'login' ? 'Welcome back' : 'Create account'}
          </h1>
          <p style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 28 }}>
            {mode === 'login' ? 'Sign in to your EViq account to continue.' : 'Join the EViq community — it\'s free.'}
          </p>

          {/* Success overlay */}
          <AnimatePresence>
            {success && (
              <MotionDiv
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                style={{ textAlign: 'center', padding: '24px 0' }}
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                  style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--accent-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}
                >
                  <CheckCircle size={32} color="var(--accent)" />
                </motion.div>
                <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--text)' }}>
                  {mode === 'login' ? 'Signed in!' : 'Account created!'}
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>Redirecting you now...</div>
              </MotionDiv>
            )}
          </AnimatePresence>

          {!success && (
            <form onSubmit={handleSubmit} noValidate>
              <AnimatePresence mode="wait">
                {mode === 'signup' && (
                  <MotionDiv
                    key="name-field"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.22 }}
                    style={{ overflow: 'hidden' }}
                  >
                    <InputField
                      icon={<User size={16} />} type="text" placeholder="Full Name"
                      value={form.full_name} onChange={e => setField('full_name', e.target.value)}
                      error={errors.full_name}
                    />
                  </MotionDiv>
                )}
              </AnimatePresence>

              <InputField
                icon={<Mail size={16} />} type="email" placeholder="Email address"
                value={form.email} onChange={e => setField('email', e.target.value)}
                error={errors.email}
              />
              <InputField
                icon={<Lock size={16} />} type="password" placeholder="Password"
                value={form.password} onChange={e => setField('password', e.target.value)}
                error={errors.password}
                showToggle onToggle={() => setShowPw(p => !p)} showPassword={showPw}
              />

              {mode === 'signup' && (
                <>
                  <PasswordStrength password={form.password} />
                  <InputField
                    icon={<Lock size={16} />} type="password" placeholder="Confirm password"
                    value={form.confirm} onChange={e => setField('confirm', e.target.value)}
                    error={errors.confirm}
                    showToggle onToggle={() => setShowPw(p => !p)} showPassword={showPw}
                  />
                </>
              )}

              {globalError && (
                <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10, padding: '10px 14px', marginBottom: 16, fontSize: 13, color: '#ef4444' }}>
                  {globalError}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '13px 20px',
                  borderRadius: 12,
                  border: 'none',
                  background: loading
                    ? 'var(--bg-muted)'
                    : 'linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent) 60%, #0284c7))',
                  color: 'white',
                  fontWeight: 700,
                  fontSize: 15,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                  transition: 'all 0.2s',
                  boxShadow: loading ? 'none' : '0 8px 24px rgba(14,165,164,0.25)',
                  marginBottom: 20,
                }}
              >
                {loading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    style={{ width: 18, height: 18, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%' }}
                  />
                ) : (
                  <>{mode === 'login' ? 'Sign In' : 'Create Account'} <ArrowRight size={16} /></>
                )}
              </button>
            </form>
          )}

          {/* Switch mode */}
          {!success && (
            <div style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-muted)', borderTop: '1px solid var(--border)', paddingTop: 20 }}>
              {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
              <button
                onClick={switchMode}
                style={{ background: 'none', border: 'none', color: 'var(--accent)', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}
              >
                {mode === 'login' ? 'Sign up free' : 'Sign in'}
              </button>
            </div>
          )}
        </div>

        {/* Back to home */}
        <div style={{ textAlign: 'center', marginTop: 20 }}>
          <Link to="/" style={{ fontSize: 13, color: 'var(--text-muted)', textDecoration: 'none' }}>
            ← Back to EViq
          </Link>
        </div>
      </MotionDiv>

      <style>{`
        .auth-input-wrap:focus-within {
          border-color: var(--accent) !important;
          box-shadow: 0 0 0 3px rgba(14,165,164,0.12);
        }
      `}</style>
    </div>
  );
}
