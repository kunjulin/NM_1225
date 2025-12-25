import { createTheme } from '@mui/material/styles'

// 核子醫學主題 - 深藍/青色科技風格
export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#0D47A1', // 深藍色
      light: '#5472D3',
      dark: '#002171',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#00ACC1', // 青色
      light: '#5DDEF4',
      dark: '#007C91',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#D32F2F',
      light: '#EF5350',
      dark: '#C62828',
    },
    warning: {
      main: '#ED6C02',
      light: '#FF9800',
      dark: '#E65100',
    },
    success: {
      main: '#2E7D32',
      light: '#4CAF50',
      dark: '#1B5E20',
    },
    background: {
      default: '#F5F7FA',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1A1A2E',
      secondary: '#4A4A68',
    },
  },
  typography: {
    fontFamily: '"Noto Sans TC", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
    },
    body1: {
      fontSize: '1rem',
    },
    body2: {
      fontSize: '0.875rem',
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          borderRadius: 12,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 600,
          backgroundColor: '#F5F7FA',
        },
      },
    },
  },
})

// 嚴重度顏色映射
export const severityColors = {
  PASS: '#2E7D32',
  INFO: '#0288D1',
  WARN: '#ED6C02',
  FAIL: '#D32F2F',
}

// 狀態顏色映射
export const statusColors = {
  NM_PENDING: '#9E9E9E',
  NM_DRAFTED: '#1976D2',
  PHARM_READY: '#7B1FA2',
  PHARM_IN_PROGRESS: '#F57C00',
  RETURNED: '#D32F2F',
  APPROVED: '#388E3C',
  SYNCING: '#00ACC1',
  SYNCED: '#2E7D32',
  SYNC_FAILED: '#C62828',
}

