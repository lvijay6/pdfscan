import React, { useState } from 'react';
import { Box, AppBar, Toolbar, Typography, Button, Container, Tabs, Tab, Avatar } from '@mui/material';
import { Camera, Crop, Folder, LogOut, ShieldCheck } from 'lucide-react';
import { AuthView } from './components/Auth';
import { CameraScanner } from './components/CameraScanner';
import { ScanEditor } from './components/ScanEditor';
import { DocumentLibrary } from './components/DocumentLibrary';

export const App: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [activeTab, setActiveTab] = useState<'scanner' | 'editor' | 'library'>('scanner');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const handleLoginSuccess = (userData: any, authToken: string) => {
    setUser(userData);
    setToken(authToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setToken(null);
  };

  const handleScanComplete = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setActiveTab('editor');
  };

  const handleSaveSuccess = () => {
    setCurrentSessionId(null);
    setActiveTab('library');
  };

  if (!token || !user) {
    return <AuthView onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: '#f8fafc' }}>
      <AppBar position="static" sx={{ bgcolor: '#0f172a' }}>
        <Toolbar>
          <ShieldCheck size={32} style={{ marginRight: 12, color: '#38bdf8' }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            Modern PDF Scanner Enterprise
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Avatar sx={{ width: 32, height: 32, bgcolor: '#38bdf8', color: 'black', fontSize: '0.9rem', fontWeight: 'bold' }}>
                {user.name ? user.name[0].toUpperCase() : 'U'}
              </Avatar>
              <Typography variant="body2" sx={{ color: 'white', display: { xs: 'none', sm: 'block' } }}>
                {user.name}
              </Typography>
            </Box>
            <Button color="inherit" size="small" onClick={handleLogout} startIcon={<LogOut size={16} />}>
              Logout
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Box sx={{ bgcolor: '#1e293b', borderBottom: '1px solid #334155' }}>
        <Container maxWidth="lg">
          <Tabs
            value={activeTab}
            onChange={(_, v) => setActiveTab(v)}
            textColor="inherit"
            indicatorColor="secondary"
            sx={{ '& .MuiTab-root': { color: '#94a3b8', '&.Mui-selected': { color: '#38bdf8', fontWeight: 'bold' } } }}
          >
            <Tab value="scanner" label="Camera Scanner" icon={<Camera size={18} />} iconPosition="start" />
            <Tab
              value="editor"
              label="Page Studio"
              icon={<Crop size={18} />}
              iconPosition="start"
              disabled={!currentSessionId}
            />
            <Tab value="library" label="Document Vault" icon={<Folder size={18} />} iconPosition="start" />
          </Tabs>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: 3 }}>
        {activeTab === 'scanner' && (
          <CameraScanner
            sessionId={currentSessionId}
            onScanComplete={handleScanComplete}
          />
        )}

        {activeTab === 'editor' && currentSessionId && (
          <ScanEditor
            sessionId={currentSessionId}
            userId={user.id}
            onSaveSuccess={handleSaveSuccess}
            onBackToScanner={() => setActiveTab('scanner')}
          />
        )}

        {activeTab === 'library' && (
          <DocumentLibrary userId={user.id} />
        )}
      </Container>
    </Box>
  );
};

export default App;
