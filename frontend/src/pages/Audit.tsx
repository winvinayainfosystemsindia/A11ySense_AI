import React, { useState } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  TextField, 
  Paper, 
  CircularProgress,
  Alert,
  Stack
} from '@mui/material';
import { Button } from '../components/common/Button';
import { auditService } from '../service/endpoints/audit';

const Audit: React.FC = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);

  const handleStartAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setTaskId(null);

    try {
      const result = await auditService.startAudit({ url });
      setTaskId(result.task_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start audit. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 8 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          Accessibility Auditor
        </Typography>
        <Typography variant="h6" align="center" color="text.secondary" sx={{ mb: 4 }}>
          Enter a URL to perform an autonomous AI-driven accessibility audit using OpenClaw.
        </Typography>

        <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
          <form onSubmit={handleStartAudit}>
            <Stack spacing={3}>
              <TextField
                fullWidth
                label="Website URL"
                variant="outlined"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
                required
                type="url"
              />
              <Button 
                type="submit" 
                variant="contained" 
                size="large" 
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : null}
              >
                {loading ? 'Starting Audit...' : 'Start Audit'}
              </Button>
            </Stack>
          </form>
        </Paper>

        <Box sx={{ mt: 4 }}>
          {error && <Alert severity="error">{error}</Alert>}
          {taskId && (
            <Alert severity="success">
              Audit started successfully! Task ID: <strong>{taskId}</strong>
              <br />
              The audit is running in the background. You can check the Allure report once it's finished.
            </Alert>
          )}
        </Box>
      </Box>
    </Container>
  );
};

export default Audit;
