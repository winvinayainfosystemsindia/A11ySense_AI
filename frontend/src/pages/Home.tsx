import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import { Button } from '../components/common/Button';

const Home: React.FC = () => {
  return (
    <Container>
      <Box sx={{ my: 4, textAlign: 'center' }}>
        <Typography variant="h2" component="h1" gutterBottom>
          Welcome to A11ySense AI
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom>
          Autonomous AI-Driven Accessibility Auditing
        </Typography>
        <Box sx={{ mt: 4 }}>
          <Button variant="contained" color="primary" size="large">
            Get Started
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default Home;
