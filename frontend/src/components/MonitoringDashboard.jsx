import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Grid,
  Typography,
  Box,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Alert,
  AlertTitle,
  Button,
  CircularProgress,
  Tabs,
  Tab,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  Timeline,
  Warning,
  Error,
  CheckCircle,
  Speed,
  Memory,
  Storage,
  NetworkCheck
} from '@mui/icons-material';

const MonitoringDashboard = ({ shopDomain }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [healthData, setHealthData] = useState(null);
  const [metricsData, setMetricsData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadMonitoringData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadMonitoringData, 30000);
    return () => clearInterval(interval);
  }, [shopDomain]);

  const loadMonitoringData = async () => {
    try {
      setLoading(true);
      
      // Load health check
      const healthResponse = await fetch('/api/v1/monitoring/health');
      const healthData = await healthResponse.json();
      setHealthData(healthData);
      
      // Load metrics summary (no auth required)
      const metricsResponse = await fetch('/api/v1/monitoring/metrics/summary');
      const metricsData = await metricsResponse.json();
      setMetricsData(metricsData);
      
      setError(null);
    } catch (err) {
      console.error('Failed to load monitoring data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadAdminData = async () => {
    try {
      // This would require admin authentication
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) return;

      const headers = { 'X-Admin-Token': adminToken };
      
      // Load detailed metrics
      const metricsResponse = await fetch('/api/v1/monitoring/metrics', { headers });
      const fullMetrics = await metricsResponse.json();
      setMetricsData(fullMetrics);
      
      // Load alerts
      const alertsResponse = await fetch('/api/v1/monitoring/alerts', { headers });
      const alertsData = await alertsResponse.json();
      setAlerts(alertsData.alerts || []);
      
      // Load system info
      const systemResponse = await fetch('/api/v1/monitoring/system', { headers });
      const systemData = await systemResponse.json();
      setSystemInfo(systemData);
      
    } catch (err) {
      console.error('Failed to load admin data:', err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle color="success" />;
      case 'degraded': return <Warning color="warning" />;
      case 'critical': return <Error color="error" />;
      default: return <CircularProgress size={24} />;
    }
  };

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
  };

  if (loading && !healthData) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        <AlertTitle>Monitoring Error</AlertTitle>
        Failed to load monitoring data: {error}
      </Alert>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        📊 System Monitoring
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Overview" />
          <Tab label="Performance" />
          <Tab label="Alerts" />
          <Tab label="System Info" />
        </Tabs>
      </Box>

      {/* Overview Tab */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          {/* System Status */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  {getStatusIcon(healthData?.status)}
                  <Typography variant="h6" ml={1}>
                    System Status
                  </Typography>
                </Box>
                
                <Chip 
                  label={healthData?.status?.toUpperCase() || 'UNKNOWN'}
                  color={getStatusColor(healthData?.status)}
                  variant="outlined"
                  size="large"
                />
                
                <Box mt={2}>
                  <Typography variant="body2" color="textSecondary">
                    Last Updated: {healthData?.timestamp ? new Date(healthData.timestamp).toLocaleString() : 'Unknown'}
                  </Typography>
                  
                  {healthData?.uptime_seconds && (
                    <Typography variant="body2" color="textSecondary">
                      Uptime: {formatUptime(healthData.uptime_seconds)}
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Key Metrics */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📈 Key Metrics
                </Typography>
                
                {metricsData && metricsData.monitoring !== 'disabled' ? (
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="Response Time"
                        secondary={`${metricsData.average_response_time_ms || 0}ms avg`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Memory Usage"
                        secondary={`${metricsData.memory_usage_percent || 0}%`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Total Requests"
                        secondary={metricsData.total_requests || 0}
                      />
                    </ListItem>
                  </List>
                ) : (
                  <Typography color="textSecondary">
                    Detailed monitoring disabled
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Database Status */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🗄️ Database
                </Typography>
                
                <Box display="flex" alignItems="center">
                  {healthData?.database === 'healthy' ? (
                    <CheckCircle color="success" />
                  ) : (
                    <Error color="error" />
                  )}
                  <Typography ml={1}>
                    {healthData?.database || 'Unknown'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* System Resources */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  💾 System Resources
                </Typography>
                
                <Box mb={2}>
                  <Typography variant="body2" gutterBottom>
                    Memory Usage: {healthData?.memory_usage_percent || 0}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={healthData?.memory_usage_percent || 0}
                    color={healthData?.memory_usage_percent > 80 ? 'error' : 'primary'}
                  />
                </Box>
                
                <Box>
                  <Typography variant="body2" gutterBottom>
                    CPU Usage: {healthData?.cpu_usage_percent || 0}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={healthData?.cpu_usage_percent || 0}
                    color={healthData?.cpu_usage_percent > 80 ? 'error' : 'primary'}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Performance Tab */}
      {activeTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🚀 Performance Metrics
                </Typography>
                
                {metricsData && metricsData.monitoring !== 'disabled' ? (
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Speed fontSize="large" color="primary" />
                        <Typography variant="h4">
                          {metricsData.average_response_time_ms || 0}ms
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Avg Response Time
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Error fontSize="large" color="error" />
                        <Typography variant="h4">
                          {metricsData.error_rate_percent || 0}%
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Error Rate
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <NetworkCheck fontSize="large" color="success" />
                        <Typography variant="h4">
                          {metricsData.total_requests || 0}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Total Requests
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Memory fontSize="large" color="warning" />
                        <Typography variant="h4">
                          {metricsData.memory_usage_percent || 0}%
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Memory Usage
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                ) : (
                  <Alert severity="info">
                    Performance monitoring is disabled. Enable it in your environment settings.
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Alerts Tab */}
      {activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    🚨 Recent Alerts
                  </Typography>
                  <Button 
                    onClick={loadAdminData}
                    variant="outlined"
                    size="small"
                  >
                    Load Admin Data
                  </Button>
                </Box>
                
                {alerts.length > 0 ? (
                  <List>
                    {alerts.map((alert, index) => (
                      <ListItem key={index} divider>
                        <ListItemText
                          primary={
                            <Box display="flex" alignItems="center">
                              {alert.severity === 'critical' ? 
                                <Error color="error" sx={{ mr: 1 }} /> :
                                <Warning color="warning" sx={{ mr: 1 }} />
                              }
                              {alert.message}
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="caption" display="block">
                                Type: {alert.type} | Severity: {alert.severity}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                {new Date(alert.timestamp).toLocaleString()}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Alert severity="success">
                    <AlertTitle>No Active Alerts</AlertTitle>
                    All systems are operating normally.
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* System Info Tab */}
      {activeTab === 3 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    🖥️ System Information
                  </Typography>
                  <Button 
                    onClick={loadAdminData}
                    variant="outlined"
                    size="small"
                  >
                    Load System Info
                  </Button>
                </Box>
                
                {systemInfo ? (
                  <Grid container spacing={2}>
                    {/* System Overview */}
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="subtitle1" gutterBottom>
                          System Overview
                        </Typography>
                        <TableContainer>
                          <Table size="small">
                            <TableBody>
                              <TableRow>
                                <TableCell>CPU Cores</TableCell>
                                <TableCell>{systemInfo.system?.cpu_count}</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Total Memory</TableCell>
                                <TableCell>{systemInfo.system?.memory?.total_gb} GB</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Available Memory</TableCell>
                                <TableCell>{systemInfo.system?.memory?.available_gb} GB</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Disk Space</TableCell>
                                <TableCell>{systemInfo.system?.disk?.free_gb} GB free</TableCell>
                              </TableRow>
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Paper>
                    </Grid>
                    
                    {/* Process Info */}
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="subtitle1" gutterBottom>
                          Process Information
                        </Typography>
                        <TableContainer>
                          <Table size="small">
                            <TableBody>
                              <TableRow>
                                <TableCell>Process ID</TableCell>
                                <TableCell>{systemInfo.process?.pid}</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Memory Usage</TableCell>
                                <TableCell>{systemInfo.process?.memory_mb} MB</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Threads</TableCell>
                                <TableCell>{systemInfo.process?.num_threads}</TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Started</TableCell>
                                <TableCell>
                                  {systemInfo.process?.create_time ? 
                                    new Date(systemInfo.process.create_time).toLocaleString() : 
                                    'Unknown'
                                  }
                                </TableCell>
                              </TableRow>
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Paper>
                    </Grid>
                  </Grid>
                ) : (
                  <Alert severity="info">
                    System information requires admin access. Click "Load System Info" to authenticate.
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Refresh Button */}
      <Box mt={3} display="flex" justifyContent="center">
        <Button 
          onClick={loadMonitoringData}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Refreshing...' : 'Refresh Data'}
        </Button>
      </Box>
    </Box>
  );
};

export default MonitoringDashboard;