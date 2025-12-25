import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Stack,
} from '@mui/material'
import {
  Science as NMIcon,
  LocalPharmacy as PharmacyIcon,
} from '@mui/icons-material'
import { useAuth, ActingRole } from '../contexts/AuthContext'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()
  
  const [subject, setSubject] = useState('')
  const [actingRole, setActingRole] = useState<ActingRole>('NM_PHYSICIAN')
  const [error, setError] = useState('')

  const from = (location.state as { from?: Location })?.from?.pathname || '/'

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!subject.trim()) {
      setError('請輸入使用者識別碼')
      return
    }
    
    login(subject.trim(), actingRole)
    
    // 根據角色導向對應頁面
    if (actingRole === 'NM_PHYSICIAN') {
      navigate('/nm/worklist')
    } else if (actingRole === 'PHARMACIST') {
      navigate('/pharmacy/worklist')
    } else {
      navigate(from)
    }
  }

  const handleQuickLogin = (role: ActingRole) => {
    const demoSubject = role === 'NM_PHYSICIAN' ? 'demo-nm-physician' : 'demo-pharmacist'
    login(demoSubject, role)
    
    if (role === 'NM_PHYSICIAN') {
      navigate('/nm/worklist')
    } else {
      navigate('/pharmacy/worklist')
    }
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #0D47A1 0%, #00ACC1 100%)',
        p: 2,
      }}
    >
      <Card sx={{ maxWidth: 450, width: '100%' }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Typography variant="h4" component="h1" gutterBottom fontWeight={700}>
              NM Stewardship
            </Typography>
            <Typography variant="body2" color="text.secondary">
              核子醫學放射藥物用藥治理系統
            </Typography>
            <Alert severity="info" sx={{ mt: 2 }}>
              DEMO MODE - 展示模式
            </Alert>
          </Box>

          <form onSubmit={handleSubmit}>
            <Stack spacing={3}>
              <TextField
                fullWidth
                label="使用者識別碼"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                error={!!error}
                helperText={error}
                placeholder="例如: A12345"
              />

              <FormControl fullWidth>
                <InputLabel>操作角色</InputLabel>
                <Select
                  value={actingRole}
                  label="操作角色"
                  onChange={(e) => setActingRole(e.target.value as ActingRole)}
                >
                  <MenuItem value="NM_PHYSICIAN">核醫醫師</MenuItem>
                  <MenuItem value="PHARMACIST">藥師</MenuItem>
                </Select>
              </FormControl>

              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                sx={{ py: 1.5 }}
              >
                登入
              </Button>
            </Stack>
          </form>

          <Box sx={{ mt: 4 }}>
            <Typography variant="body2" color="text.secondary" textAlign="center" mb={2}>
              或使用快速登入
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                startIcon={<NMIcon />}
                onClick={() => handleQuickLogin('NM_PHYSICIAN')}
                fullWidth
              >
                核醫醫師
              </Button>
              <Button
                variant="outlined"
                startIcon={<PharmacyIcon />}
                onClick={() => handleQuickLogin('PHARMACIST')}
                fullWidth
              >
                藥師
              </Button>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

