import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#fff',
    },
  },
  typography: {
    fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
    h1: {
      fontSize: '3.5rem',
      fontWeight: 500,
      letterSpacing: '-0.03em',
    },
    h2: {
      fontSize: '1.5rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: `
        :root {
          font-synthesis: none;
          text-rendering: optimizeLegibility;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
        body {
          margin: 0;
          min-width: 320px;
          min-height: 100vh;
        }
        #root {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }
      `,
    },
  },
});
