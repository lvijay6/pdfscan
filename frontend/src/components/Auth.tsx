import React, { useState } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button,
  Tab, Tabs, Alert, Dialog, DialogTitle, DialogContent,
  DialogActions, Divider, CircularProgress
} from '@mui/material';
import { ShieldCheck, QrCode, LogIn, UserPlus } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1/auth';

interface AuthProps {
  onLoginSuccess: (user: any, token: string) => void;
}

export const AuthView: React.FC<AuthProps> = ({ onLoginSuccess }) => {
  const [tab, setTab] = useState(0);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [mobile, setMobile] = useState('');

  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaCode, setMfaCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [mfaModalOpen, setMfaModalOpen] = useState(false);
  const [qrCodeB64, setQrCodeB64] = useState<string | null>(null);
  const [mfaSecret, setMfaSecret] = useState<string | null>(null);
  const [setupCode, setSetupCode] = useState('');
  const [mfaSuccessMsg, setMfaSuccessMsg] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/login`, { email, password });
      if (res.data.mfa_required) {
        setMfaRequired(true);
      } else {
        localStorage.setItem('token', res.data.access_token);
        onLoginSuccess(res.data.user, res.data.access_token);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleMfaVerify = async () => {
    setError(null);
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/mfa/verify`, { email, code: mfaCode });
      localStorage.setItem('token', res.data.access_token);
      onLoginSuccess(res.data.user, res.data.access_token);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'MFA Verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/signup`, { name, email, mobile, password });
      localStorage.setItem('token', res.data.access_token);
      onLoginSuccess(res.data.user, res.data.access_token);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSocialLogin = async (provider: string) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/social-login`, {
        provider,
        token: `${provider}_demo_token`,
        email: email || `user_${Date.now()}@gmail.com`,
        name: name || `${provider.toUpperCase()} User`
      });
      localStorage.setItem('token', res.data.access_token);
      onLoginSuccess(res.data.user, res.data.access_token);
    } catch (err: any) {
      setError('Social login failed');
    } finally {
      setLoading(false);
    }
  };

  const startMfaSetup = async () => {
    if (!email) {
      setError('Please enter your email to setup MFA');
      return;
    }
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/mfa/setup?email=${encodeURIComponent(email)}`);
      setQrCodeB64(res.data.qr_code);
      setMfaSecret(res.data.secret);
      setMfaModalOpen(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to setup MFA');
    } finally {
      setLoading(false);
    }
  };

  const confirmEnableMfa = async () => {
    try {
      await axios.post(`${API_BASE}/mfa/enable`, { email, code: setupCode });
      setMfaSuccessMsg('MFA successfully enabled for your account!');
      setMfaModalOpen(false);
    } catch (err: any) {
      setError('Invalid verification code');
    }
  };

  return (
    <Box sx={{ maxWidth: 460, mx: 'auto', mt: 6, p: 2 }}>
      <Card elevation={6} sx={{ borderRadius: 3 }}>
        <Box sx={{ p: 3, textAlign: 'center', bgcolor: 'primary.main', color: 'white' }}>
          <ShieldCheck size={48} style={{ marginBottom: 8 }} />
          <Typography variant="h5" sx={{ fontWeight: 'bold' }}>PDF Scanner Portal</Typography>
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            Enterprise Document Digitization & OCR Security
          </Typography>
        </Box>

        <Tabs value={tab} onChange={(_, v) => { setTab(v); setError(null); }} centered>
          <Tab label="Login" icon={<LogIn size={18} />} iconPosition="start" />
          <Tab label="Signup" icon={<UserPlus size={18} />} iconPosition="start" />
        </Tabs>

        <CardContent sx={{ p: 3 }}>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {mfaSuccessMsg && <Alert severity="success" sx={{ mb: 2 }}>{mfaSuccessMsg}</Alert>}

          {tab === 0 ? (
            !mfaRequired ? (
              <form onSubmit={handleLogin}>
                <TextField
                  fullWidth label="Email Address" margin="normal"
                  value={email} onChange={(e) => setEmail(e.target.value)}
                  required type="email"
                />
                <TextField
                  fullWidth label="Password" margin="normal"
                  value={password} onChange={(e) => setPassword(e.target.value)}
                  required type="password"
                />

                <Button
                  fullWidth variant="contained" type="submit" size="large"
                  disabled={loading} sx={{ mt: 2, mb: 2, py: 1.2 }}
                >
                  {loading ? <CircularProgress size={24} /> : 'Login'}
                </Button>

                <Divider sx={{ my: 2 }}>OR SOCIAL LOGIN</Divider>

                <Button
                  fullWidth variant="outlined" color="inherit"
                  onClick={() => handleSocialLogin('google')}
                  sx={{ mb: 1.5 }}
                >
                  Sign in with Google
                </Button>

                <Box sx={{ textAlign: 'center', mt: 2 }}>
                  <Button size="small" onClick={startMfaSetup} startIcon={<QrCode size={16} />}>
                    Setup Authenticator App (MFA)
                  </Button>
                </Box>
              </form>
            ) : (
              <Box>
                <Alert severity="info" sx={{ mb: 2 }}>
                  MFA Protection Enabled. Enter Google/Microsoft Authenticator 6-digit TOTP Code or SMS OTP.
                </Alert>
                <TextField
                  fullWidth label="6-Digit MFA / OTP Code" margin="normal"
                  value={mfaCode} onChange={(e) => setMfaCode(e.target.value)}
                  placeholder="123456" autoFocus
                />
                <Button
                  fullWidth variant="contained" size="large" color="success"
                  onClick={handleMfaVerify} sx={{ mt: 2 }} disabled={loading}
                >
                  Verify MFA & Login
                </Button>
                <Button fullWidth size="small" sx={{ mt: 1 }} onClick={() => setMfaRequired(false)}>
                  Back to Login
                </Button>
              </Box>
            )
          ) : (
            <form onSubmit={handleSignup}>
              <TextField
                fullWidth label="Full Name" margin="normal"
                value={name} onChange={(e) => setName(e.target.value)}
                required
              />
              <TextField
                fullWidth label="Email Address" margin="normal"
                value={email} onChange={(e) => setEmail(e.target.value)}
                required type="email"
              />
              <TextField
                fullWidth label="Mobile Number" margin="normal"
                value={mobile} onChange={(e) => setMobile(e.target.value)}
              />
              <TextField
                fullWidth label="Password" margin="normal"
                value={password} onChange={(e) => setPassword(e.target.value)}
                required type="password"
              />
              <Button
                fullWidth variant="contained" type="submit" size="large"
                disabled={loading} sx={{ mt: 2, py: 1.2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Create Account'}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>

      <Dialog open={mfaModalOpen} onClose={() => setMfaModalOpen(false)}>
        <DialogTitle sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
          <QrCode /> Setup TOTP Authenticator (Google/Microsoft)
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Scan this QR code with Google Authenticator or Microsoft Authenticator app on your phone:
          </Typography>
          {qrCodeB64 && (
            <Box sx={{ textAlign: 'center', my: 2 }}>
              <img src={qrCodeB64} alt="MFA QR Code" style={{ width: 180, height: 180 }} />
            </Box>
          )}
          <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', mb: 2 }}>
            Secret Key: <strong>{mfaSecret}</strong>
          </Typography>
          <TextField
            fullWidth label="Enter Code from App" margin="normal"
            value={setupCode} onChange={(e) => setSetupCode(e.target.value)}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setMfaModalOpen(false)}>Cancel</Button>
          <Button variant="contained" color="primary" onClick={confirmEnableMfa}>
            Enable MFA
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
