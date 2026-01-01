import React, { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  AppBar,
  Box,
  Chip,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
  Divider,
  Avatar,
} from '@mui/material'
import {
  Menu as MenuIcon,
  LocalPharmacy as PharmacyIcon,
  Science as NMIcon,
  Assessment as AnalyticsIcon,
  AccountCircle,
  SwapHoriz as SwitchIcon,
  Logout as LogoutIcon,
  People as UsersIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
} from '@mui/icons-material'
import { useAuth, ActingRole } from '../contexts/AuthContext'
import { HelpPage } from '../pages/HelpPage'

const DRAWER_WIDTH = 240

const roleLabels: Record<ActingRole, string> = {
  NM_PHYSICIAN: '核醫醫師',
  PHARMACIST: '藥師',
  ADMIN: '管理員',
}

const roleColors: Record<ActingRole, 'primary' | 'secondary' | 'default'> = {
  NM_PHYSICIAN: 'primary',
  PHARMACIST: 'secondary',
  ADMIN: 'default',
}

export function AppShell() {
  const navigate = useNavigate()
  const location = useLocation()
  const { subject, actingRole, isDemo, setActingRole, logout } = useAuth()
  
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [roleMenuAnchor, setRoleMenuAnchor] = useState<null | HTMLElement>(null)
  const [helpDialogOpen, setHelpDialogOpen] = useState(false)
  
  // 確保從後端取得最新的模式設定
  const [actualIsDemo, setActualIsDemo] = useState(isDemo)
  
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const config = await fetch('/api/config').then(r => r.json())
        setActualIsDemo(config.isDemo)
      } catch {
        setActualIsDemo(isDemo)
      }
    }
    loadConfig()
  }, [isDemo])

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen)
  }

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleUserMenuClose = () => {
    setAnchorEl(null)
  }

  const handleRoleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setRoleMenuAnchor(event.currentTarget)
  }

  const handleRoleMenuClose = () => {
    setRoleMenuAnchor(null)
  }

  const handleRoleSwitch = (role: ActingRole) => {
    setActingRole(role)
    handleRoleMenuClose()
    // 切換到對應的工作清單
    if (role === 'NM_PHYSICIAN') {
      navigate('/nm/worklist')
    } else if (role === 'PHARMACIST') {
      navigate('/pharmacy/worklist')
    }
  }

  const handleLogout = () => {
    handleUserMenuClose()
    logout()
    navigate('/login')
  }

  const menuItems = [
    {
      text: '核醫工作清單',
      icon: <NMIcon />,
      path: '/nm/worklist',
      roles: ['NM_PHYSICIAN', 'ADMIN'] as ActingRole[],
    },
    {
      text: '藥師工作清單',
      icon: <PharmacyIcon />,
      path: '/pharmacy/worklist',
      roles: ['PHARMACIST', 'ADMIN'] as ActingRole[],
    },
    {
      text: '分析儀表板',
      icon: <AnalyticsIcon />,
      path: '/analytics',
      roles: ['NM_PHYSICIAN', 'PHARMACIST', 'ADMIN'] as ActingRole[],
    },
    {
      text: '使用者管理',
      icon: <UsersIcon />,
      path: '/admin/users',
      roles: ['ADMIN'] as ActingRole[],
    },
    {
      text: '系統設定',
      icon: <SettingsIcon />,
      path: '/settings',
      roles: ['ADMIN'] as ActingRole[],
    },
  ]

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap sx={{ fontWeight: 700 }}>
          NM Stewardship
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems
          .filter(item => item.roles.includes(actingRole))
          .map((item) => (
            <ListItem key={item.path} disablePadding>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => {
                  navigate(item.path)
                  setDrawerOpen(false)
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
      </List>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { xs: '100%', sm: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { xs: 0, sm: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            核子醫學用藥治理系統
          </Typography>

          {/* Demo Mode Badge */}
          {actualIsDemo && (
            <Chip
              label="DEMO MODE"
              size="small"
              sx={{
                mr: 2,
                bgcolor: 'warning.main',
                color: 'warning.contrastText',
                fontWeight: 600,
              }}
            />
          )}

          {/* Role Badge */}
          <Chip
            label={roleLabels[actingRole]}
            color={roleColors[actingRole]}
            size="small"
            onClick={handleRoleMenuOpen}
            icon={<SwitchIcon />}
            sx={{ 
              mr: 2, 
              cursor: 'pointer',
              ...(actingRole === 'ADMIN' && {
                color: 'white',
                '& .MuiChip-label': {
                  color: 'white',
                },
                '& .MuiChip-icon': {
                  color: 'white',
                },
              }),
            }}
          />

          {/* Help Icon */}
          <IconButton
            size="large"
            edge="end"
            color="inherit"
            onClick={() => setHelpDialogOpen(true)}
            sx={{ mr: 1 }}
            title="操作說明"
          >
            <HelpIcon />
          </IconButton>

          {/* User Menu */}
          <IconButton
            size="large"
            edge="end"
            color="inherit"
            onClick={handleUserMenuOpen}
          >
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
              {subject.charAt(0).toUpperCase()}
            </Avatar>
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Role Switch Menu */}
      <Menu
        anchorEl={roleMenuAnchor}
        open={Boolean(roleMenuAnchor)}
        onClose={handleRoleMenuClose}
      >
        <MenuItem
          onClick={() => handleRoleSwitch('NM_PHYSICIAN')}
          selected={actingRole === 'NM_PHYSICIAN'}
        >
          <ListItemIcon><NMIcon /></ListItemIcon>
          核醫醫師
        </MenuItem>
        <MenuItem
          onClick={() => handleRoleSwitch('PHARMACIST')}
          selected={actingRole === 'PHARMACIST'}
        >
          <ListItemIcon><PharmacyIcon /></ListItemIcon>
          藥師
        </MenuItem>
      </Menu>

      {/* User Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleUserMenuClose}
      >
        <MenuItem disabled>
          <AccountCircle sx={{ mr: 1 }} />
          {subject}
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>
          <LogoutIcon sx={{ mr: 1 }} />
          登出
        </MenuItem>
      </Menu>

      {/* Drawer */}
      <Box
        component="nav"
        sx={{ width: { sm: DRAWER_WIDTH }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={drawerOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 3 },
          width: { xs: '100%', sm: `calc(100% - ${DRAWER_WIDTH}px)` },
          maxWidth: '100%',
          mt: { xs: 7, sm: 8 },
          minHeight: '100vh',
          bgcolor: 'background.default',
          boxSizing: 'border-box',
          overflowX: 'hidden',
        }}
      >
        <Outlet />
      </Box>

      {/* Help Dialog */}
      <HelpPage open={helpDialogOpen} onClose={() => setHelpDialogOpen(false)} />
    </Box>
  )
}

