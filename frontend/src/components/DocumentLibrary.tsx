import React, { useEffect, useState } from 'react';
import {
  Box, Paper, Typography, TextField, Button, Card,
  CardContent, CardActions, Chip, Dialog, DialogTitle,
  DialogContent, DialogActions, Select, MenuItem, FormControl,
  InputLabel, Checkbox, FormControlLabel, CircularProgress, IconButton
} from '@mui/material';
import { Search, FileText, Download, Lock, Eye, Trash2, FileCheck } from 'lucide-react';
import axios from 'axios';

interface DocumentLibraryProps {
  userId: string;
}

export const DocumentLibrary: React.FC<DocumentLibraryProps> = ({ userId }) => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('All');
  const [loading, setLoading] = useState(false);

  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);

  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [exportDocId, setExportDocId] = useState<string | null>(null);
  const [exportFormat, setExportFormat] = useState('searchable_pdf');
  const [password, setPassword] = useState('');
  const [compress, setCompress] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, [userId, filterType]);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/documents/list/${userId}`, {
        params: {
          search,
          document_type: filterType
        }
      });
      setDocuments(res.data.documents);
    } catch (err) {
      console.error('Failed to fetch documents', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDocuments();
  };

  const viewDocumentDetail = async (docId: string) => {
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/documents/detail/${docId}`);
      setSelectedDoc(res.data);
      setDetailModalOpen(true);
    } catch (err) {
      console.error('Failed to open document detail', err);
    }
  };

  const openExportModal = (docId: string) => {
    setExportDocId(docId);
    setExportModalOpen(true);
  };

  const handleExportDownload = async () => {
    if (!exportDocId) return;
    try {
      const res = await axios.post(
        `http://localhost:8000/api/v1/documents/export/${exportDocId}`,
        {
          format: exportFormat,
          password: password || undefined,
          compress
        },
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `document_export.${exportFormat === 'searchable_pdf' ? 'pdf' : exportFormat}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setExportModalOpen(false);
    } catch (err) {
      console.error('Export failed', err);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    try {
      await axios.delete(`http://localhost:8000/api/v1/documents/delete/${docId}`);
      setDocuments(documents.filter((d) => d.id !== docId));
    } catch (err) {
      console.error('Delete failed', err);
    }
  };

  return (
    <Box sx={{ maxWidth: 1100, mx: 'auto', mt: 3, p: 2 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 3, bgcolor: '#0f172a', color: 'white', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <FileCheck /> Permanent Document Vault & Full-Text Search
        </Typography>

        <form onSubmit={handleSearchSubmit}>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              placeholder="Search OCR Text (e.g., Invoice #, GSTIN, Aadhaar, Amount)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              sx={{ flex: '1 1 300px', bgcolor: 'white', borderRadius: 1 }}
              size="small"
            />

            <FormControl size="small" sx={{ minWidth: 160, bgcolor: 'white', borderRadius: 1 }}>
              <InputLabel id="filter-type-label">Filter Category</InputLabel>
              <Select
                labelId="filter-type-label"
                value={filterType}
                label="Filter Category"
                onChange={(e) => setFilterType(e.target.value)}
              >
                <MenuItem value="All">All Documents</MenuItem>
                <MenuItem value="Invoice">Invoice</MenuItem>
                <MenuItem value="GST Bill">GST Bill</MenuItem>
                <MenuItem value="Receipt">Receipt</MenuItem>
                <MenuItem value="ID Card">ID Card</MenuItem>
                <MenuItem value="Passport">Passport</MenuItem>
                <MenuItem value="PAN Card">PAN Card</MenuItem>
                <MenuItem value="Aadhaar Card">Aadhaar Card</MenuItem>
                <MenuItem value="Contract">Contract</MenuItem>
              </Select>
            </FormControl>

            <Button variant="contained" color="info" type="submit" startIcon={<Search />}>
              Search OCR
            </Button>
          </Box>
        </form>
      </Paper>

      {loading ? (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      ) : documents.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
          <FileText size={48} style={{ opacity: 0.5, marginBottom: 8 }} />
          <Typography variant="h6">No Documents Found</Typography>
          <Typography variant="body2" color="text.secondary">
            Scan documents using camera or upload images to build your document library.
          </Typography>
        </Paper>
      ) : (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          {documents.map((doc) => (
            <Box sx={{ flex: '1 1 300px', maxWidth: 350 }} key={doc.id}>
              <Card elevation={3} sx={{ borderRadius: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>
                      {doc.name}
                    </Typography>
                    {doc.is_password_protected && <Lock size={18} color="#eab308" />}
                  </Box>

                  <Chip label={doc.document_type} color="primary" size="small" sx={{ mb: 1.5 }} />

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {doc.page_count} Page(s) • {new Date(doc.created_at).toLocaleDateString()}
                  </Typography>

                  <Box sx={{ bgcolor: '#f8fafc', p: 1.5, borderRadius: 1, border: '1px solid #e2e8f0', minHeight: 60 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      "{doc.ocr_preview || 'No OCR text extracted'}"
                    </Typography>
                  </Box>
                </CardContent>

                <CardActions sx={{ px: 2, pb: 2, justifyContent: 'space-between' }}>
                  <Button size="small" startIcon={<Eye size={16} />} onClick={() => viewDocumentDetail(doc.id)}>
                    View
                  </Button>
                  <Button size="small" color="success" startIcon={<Download size={16} />} onClick={() => openExportModal(doc.id)}>
                    Export
                  </Button>
                  <IconButton size="small" color="error" onClick={() => handleDelete(doc.id)}>
                    <Trash2 size={16} />
                  </IconButton>
                </CardActions>
              </Card>
            </Box>
          ))}
        </Box>
      )}

      <Dialog open={detailModalOpen} onClose={() => setDetailModalOpen(false)} maxWidth="md" fullWidth>
        {selectedDoc && (
          <>
            <DialogTitle sx={{ fontWeight: 'bold', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>{selectedDoc.name}</span>
              <Chip label={selectedDoc.document_type} color="info" />
            </DialogTitle>
            <DialogContent dividers>
              {selectedDoc.pages.map((p: any) => (
                <Box key={p.id} sx={{ mb: 3, p: 2, border: '1px solid #e2e8f0', borderRadius: 2 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                    Page {p.page_no}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <img src={p.image_b64} alt={`Page ${p.page_no}`} style={{ maxWidth: 220, borderRadius: 4, objectFit: 'contain' }} />
                    <Box sx={{ flex: 1, minWidth: 240, bgcolor: '#f1f5f9', p: 1.5, borderRadius: 1 }}>
                      <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>
                        Extracted OCR Text:
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                        {p.ocr_text || 'No text recognized.'}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              ))}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailModalOpen(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      <Dialog open={exportModalOpen} onClose={() => setExportModalOpen(false)}>
        <DialogTitle sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
          <Download /> Export Document Options
        </DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel id="export-fmt-label">Output Format</InputLabel>
            <Select
              labelId="export-fmt-label"
              value={exportFormat}
              label="Output Format"
              onChange={(e) => setExportFormat(e.target.value)}
            >
              <MenuItem value="searchable_pdf">Searchable PDF (OCR Text Layer)</MenuItem>
              <MenuItem value="pdf">Standard PDF</MenuItem>
              <MenuItem value="jpg">Image (JPG)</MenuItem>
              <MenuItem value="png">Image (PNG)</MenuItem>
              <MenuItem value="webp">Image (WEBP)</MenuItem>
            </Select>
          </FormControl>

          {exportFormat.includes('pdf') && (
            <>
              <TextField
                fullWidth
                label="PDF Password Protection (Optional)"
                margin="normal"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Set password to encrypt PDF"
              />
              <FormControlLabel
                control={<Checkbox checked={compress} onChange={(e) => setCompress(e.target.checked)} />}
                label="Enable PDF Compression"
              />
            </>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setExportModalOpen(false)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleExportDownload}>
            Download File
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
