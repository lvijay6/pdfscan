import React, { useRef, useState } from 'react';
import Webcam from 'react-webcam';
import {
  Box, Button, Typography, Select, MenuItem,
  FormControl, InputLabel, Chip, CircularProgress, Paper, IconButton
} from '@mui/material';
import { Camera, Upload, CheckCircle2, Layers } from 'lucide-react';
import axios from 'axios';

const SCAN_TYPES = [
  'Invoice', 'GST Bill', 'Receipt', 'ID Card',
  'Passport', 'PAN Card', 'Aadhaar Card', 'Contract', 'Any hard-copy document'
];

interface CameraScannerProps {
  sessionId: string | null;
  onScanComplete: (sessionId: string, totalPages: number) => void;
}

export const CameraScanner: React.FC<CameraScannerProps> = ({ sessionId: initialSessionId, onScanComplete }) => {
  const webcamRef = useRef<Webcam>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [docType, setDocType] = useState('Invoice');
  const [loading, setLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(initialSessionId);
  const [capturedPages, setCapturedPages] = useState<number>(0);
  const [previewThumb, setPreviewThumb] = useState<string | null>(null);

  const processImageBytes = async (blob: Blob) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', blob, 'scan.png');
      if (currentSessionId) {
        formData.append('session_id', currentSessionId);
      }

      const res = await axios.post('http://localhost:8000/api/v1/scan/process-page', formData);
      const sid = res.data.session_id;
      setCurrentSessionId(sid);
      setCapturedPages(res.data.total_pages);
      setPreviewThumb(res.data.page.image_b64);
    } catch (err) {
      console.error('Failed to process image scan', err);
    } finally {
      setLoading(false);
    }
  };

  const captureCamera = () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        fetch(imageSrc)
          .then((res) => res.blob())
          .then((blob) => processImageBytes(blob));
      }
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processImageBytes(e.target.files[0]);
    }
  };

  const finishScanning = () => {
    if (currentSessionId) {
      onScanComplete(currentSessionId, capturedPages);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', mt: 3, p: 2 }}>
      <Paper elevation={4} sx={{ p: 3, borderRadius: 3, bgcolor: '#0f172a', color: 'white' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1, fontWeight: 'bold' }}>
            <Camera /> Live Document Scanner
          </Typography>

          <FormControl size="small" sx={{ minWidth: 160, bgcolor: 'white', borderRadius: 1 }}>
            <InputLabel id="doc-type-label">Document Type</InputLabel>
            <Select
              labelId="doc-type-label"
              value={docType}
              label="Document Type"
              onChange={(e) => setDocType(e.target.value)}
            >
              {SCAN_TYPES.map((t) => (
                <MenuItem key={t} value={t}>{t}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        <Box sx={{ position: 'relative', width: '100%', height: 420, borderRadius: 2, overflow: 'hidden', bgcolor: 'black', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/png"
            videoConstraints={{ facingMode: 'environment' }}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />

          <Box
            sx={{
              position: 'absolute',
              top: '10%',
              left: '10%',
              right: '10%',
              bottom: '10%',
              border: '3px dashed #38bdf8',
              borderRadius: 2,
              boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.4)',
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Chip
              label={`Align ${docType} inside frame`}
              color="info"
              sx={{ bgcolor: 'rgba(56, 189, 248, 0.8)', color: 'black', fontWeight: 'bold' }}
            />
          </Box>

          {loading && (
            <Box sx={{ position: 'absolute', inset: 0, bgcolor: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
              <CircularProgress color="info" />
              <Typography variant="body1" color="white">Auto-Detecting Edges & Deskewing...</Typography>
            </Box>
          )}
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
          <Button
            variant="outlined"
            color="info"
            onClick={() => fileInputRef.current?.click()}
            startIcon={<Upload />}
          >
            Upload Image
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            hidden
            accept="image/*"
            onChange={handleFileUpload}
          />

          <IconButton
            onClick={captureCamera}
            disabled={loading}
            sx={{
              bgcolor: '#38bdf8',
              color: 'black',
              p: 2,
              '&:hover': { bgcolor: '#0284c7' }
            }}
          >
            <Camera size={32} />
          </IconButton>

          {capturedPages > 0 ? (
            <Button
              variant="contained"
              color="success"
              onClick={finishScanning}
              startIcon={<CheckCircle2 />}
            >
              Review {capturedPages} Page(s)
            </Button>
          ) : (
            <Box sx={{ width: 140 }} />
          )}
        </Box>

        {previewThumb && (
          <Box sx={{ mt: 3, p: 2, bgcolor: '#1e293b', borderRadius: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Layers size={20} />
            <Typography variant="body2">Scanned Pages: <strong>{capturedPages}</strong></Typography>
            <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
              <img src={previewThumb} alt="Scan preview" style={{ width: 48, height: 60, borderRadius: 4, objectFit: 'cover', border: '2px solid #38bdf8' }} />
            </Box>
          </Box>
        )}
      </Paper>
    </Box>
  );
};
