import React, { useEffect, useState } from 'react';
import {
  Box, Paper, Typography, Button, IconButton, Slider,
  Select, MenuItem, FormControl, InputLabel, TextField,
  Dialog, DialogTitle, DialogContent, DialogActions, Chip
} from '@mui/material';
import { RotateCw, Crop, Sun, Sparkles, Trash2, Save, MoveLeft, MoveRight } from 'lucide-react';
import axios from 'axios';

interface ScanEditorProps {
  sessionId: string;
  userId: string;
  onSaveSuccess: (docId: string) => void;
  onBackToScanner: () => void;
}

export const ScanEditor: React.FC<ScanEditorProps> = ({ sessionId, userId, onSaveSuccess, onBackToScanner }) => {
  const [pages, setPages] = useState<any[]>([]);
  const [activePageIndex, setActivePageIndex] = useState(0);
  const [docName, setDocName] = useState('Scanned Document');

  const [rotation, setRotation] = useState(0);
  const [brightness, setBrightness] = useState(1.0);
  const [contrast, setContrast] = useState(1.0);
  const [filterName, setFilterName] = useState('original');
  const [loading, setLoading] = useState(false);

  const [saveModalOpen, setSaveModalOpen] = useState(false);

  useEffect(() => {
    fetchSessionPreview(sessionId);
  }, [sessionId]);

  const fetchSessionPreview = async (sid: string) => {
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/scan/preview/${sid}`);
      setPages(res.data.pages);
      if (res.data.pages[activePageIndex]) {
        const p = res.data.pages[activePageIndex];
        setRotation(p.rotation || 0);
        setBrightness(p.brightness || 1.0);
        setContrast(p.contrast || 1.0);
        setFilterName(p.filter_name || 'original');
      }
    } catch (err) {
      console.error('Failed to load scan preview session', err);
    }
  };

  const applyEdits = async () => {
    setLoading(true);
    try {
      const res = await axios.post('http://localhost:8000/api/v1/scan/edit-page', {
        session_id: sessionId,
        page_index: activePageIndex,
        rotation,
        brightness,
        contrast,
        filter_name: filterName
      });
      const updatedPages = [...pages];
      updatedPages[activePageIndex] = res.data.page;
      setPages(updatedPages);
    } catch (err) {
      console.error('Error applying page edits', err);
    } finally {
      setLoading(false);
    }
  };

  const rotateClockwise = () => {
    const newRot = (rotation + 90) % 360;
    setRotation(newRot);
  };

  const handleDeletePage = async () => {
    try {
      await axios.delete(`http://localhost:8000/api/v1/scan/page/${sessionId}/${activePageIndex}`);
      const newPages = pages.filter((_, idx) => idx !== activePageIndex);
      setPages(newPages);
      if (newPages.length === 0) {
        onBackToScanner();
      } else {
        setActivePageIndex(Math.max(0, activePageIndex - 1));
      }
    } catch (err) {
      console.error('Delete page failed', err);
    }
  };

  const handleReorder = async (direction: 'left' | 'right') => {
    const newIndex = direction === 'left' ? activePageIndex - 1 : activePageIndex + 1;
    if (newIndex < 0 || newIndex >= pages.length) return;

    const newOrder = pages.map((_, i) => i);
    const temp = newOrder[activePageIndex];
    newOrder[activePageIndex] = newOrder[newIndex];
    newOrder[newIndex] = temp;

    try {
      await axios.post('http://localhost:8000/api/v1/scan/reorder', {
        session_id: sessionId,
        new_order: newOrder
      });
      fetchSessionPreview(sessionId);
      setActivePageIndex(newIndex);
    } catch (err) {
      console.error('Reorder failed', err);
    }
  };

  const handleSaveDocument = async () => {
    try {
      const res = await axios.post('http://localhost:8000/api/v1/documents/save', {
        user_id: userId,
        session_id: sessionId,
        name: docName,
        document_type: pages[0]?.doc_type || 'General'
      });
      setSaveModalOpen(false);
      onSaveSuccess(res.data.document_id);
    } catch (err) {
      console.error('Failed to save document', err);
    }
  };

  const activePage = pages[activePageIndex];

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto', mt: 3, p: 2 }}>
      <Paper elevation={4} sx={{ p: 3, borderRadius: 3, bgcolor: '#0f172a', color: 'white' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
            <Crop /> Scan Studio & Page Adjustments
          </Typography>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button variant="outlined" color="inherit" onClick={onBackToScanner}>
              Add More Pages
            </Button>
            <Button variant="contained" color="success" onClick={() => setSaveModalOpen(true)} startIcon={<Save />}>
              Save Document
            </Button>
          </Box>
        </Box>

        {activePage && (
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mt: 2 }}>
            <Box sx={{ flex: '1 1 450px', bgcolor: 'black', borderRadius: 2, p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 450 }}>
              <img
                src={activePage.image_b64}
                alt="Page scan preview"
                style={{
                  maxWidth: '100%',
                  maxHeight: 420,
                  objectFit: 'contain',
                  borderRadius: 4
                }}
              />
              <Typography variant="caption" sx={{ mt: 1, color: '#94a3b8' }}>
                Page {activePageIndex + 1} of {pages.length} ({activePage.doc_type})
              </Typography>
            </Box>

            <Paper elevation={2} sx={{ flex: '1 1 300px', p: 3, borderRadius: 2, bgcolor: '#1e293b', color: 'white' }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
                Image Filters & Tone
              </Typography>

              <FormControl fullWidth size="small" sx={{ mb: 3, bgcolor: 'white', borderRadius: 1 }}>
                <InputLabel id="filter-label">Preset Filter</InputLabel>
                <Select
                  labelId="filter-label"
                  value={filterName}
                  label="Preset Filter"
                  onChange={(e) => setFilterName(e.target.value)}
                >
                  <MenuItem value="original">Original Color</MenuItem>
                  <MenuItem value="magic">Magic Enhance (Clean BG)</MenuItem>
                  <MenuItem value="bw">B&W Document Threshold</MenuItem>
                  <MenuItem value="grayscale">Grayscale</MenuItem>
                </Select>
              </FormControl>

              <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Sun size={18} /> Brightness ({brightness.toFixed(1)})
              </Typography>
              <Slider
                value={brightness}
                min={0.5} max={2.0} step={0.1}
                onChange={(_, v) => setBrightness(v as number)}
                sx={{ mb: 2, color: '#38bdf8' }}
              />

              <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Sparkles size={18} /> Contrast ({contrast.toFixed(1)})
              </Typography>
              <Slider
                value={contrast}
                min={0.5} max={2.0} step={0.1}
                onChange={(_, v) => setContrast(v as number)}
                sx={{ mb: 3, color: '#38bdf8' }}
              />

              <Button
                fullWidth variant="contained" color="info"
                onClick={applyEdits} disabled={loading}
                sx={{ mb: 3 }}
              >
                Apply Adjustments
              </Button>

              <Box sx={{ borderTop: '1px solid #334155', pt: 2, display: 'flex', justifyContent: 'space-between' }}>
                <IconButton color="primary" onClick={rotateClockwise} title="Rotate 90 Deg">
                  <RotateCw />
                </IconButton>

                <IconButton color="warning" onClick={() => handleReorder('left')} disabled={activePageIndex === 0}>
                  <MoveLeft />
                </IconButton>

                <IconButton color="warning" onClick={() => handleReorder('right')} disabled={activePageIndex === pages.length - 1}>
                  <MoveRight />
                </IconButton>

                <IconButton color="error" onClick={handleDeletePage} title="Delete Page">
                  <Trash2 />
                </IconButton>
              </Box>
            </Paper>
          </Box>
        )}

        <Box sx={{ display: 'flex', gap: 2, overflowX: 'auto', mt: 3, pt: 2, borderTop: '1px solid #334155' }}>
          {pages.map((p, idx) => (
            <Box
              key={p.page_id || idx}
              onClick={() => {
                setActivePageIndex(idx);
                setRotation(p.rotation || 0);
                setBrightness(p.brightness || 1.0);
                setContrast(p.contrast || 1.0);
                setFilterName(p.filter_name || 'original');
              }}
              sx={{
                cursor: 'pointer',
                p: 0.5,
                borderRadius: 2,
                border: activePageIndex === idx ? '3px solid #38bdf8' : '2px solid transparent',
                opacity: activePageIndex === idx ? 1 : 0.6
              }}
            >
              <img src={p.image_b64} alt={`Thumb ${idx}`} style={{ width: 64, height: 80, objectFit: 'cover', borderRadius: 4 }} />
              <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', color: 'white' }}>
                Pg {idx + 1}
              </Typography>
            </Box>
          ))}
        </Box>
      </Paper>

      <Dialog open={saveModalOpen} onClose={() => setSaveModalOpen(false)}>
        <DialogTitle sx={{ fontWeight: 'bold' }}>Save Document to Library</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth label="Document Name" margin="normal"
            value={docName} onChange={(e) => setDocName(e.target.value)}
          />
          <Chip label={`Document Type: ${pages[0]?.doc_type || 'General'}`} color="primary" sx={{ mt: 1 }} />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setSaveModalOpen(false)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleSaveDocument}>
            Save & Store
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
