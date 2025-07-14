import React, { useState, useEffect } from 'react';
import { Badge, Button, Card, DataTable, InlineStack, Layout, Page, Text } from '@shopify/polaris';

function Alerts({ showToast }) {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchAlerts();
  }, [filter]);

  const fetchAlerts = async () => {
    try {
      const status = filter === 'all' ? '' : filter;
      const url = `http://localhost:8000/api/v1/alerts/?status=${status}`;
      const response = await fetch(url);
      const data = await response.json();
      
      const formattedAlerts = data.alerts.map(alert => [
        alert.title || alert.type,
        alert.product,
        alert.message,
        getSeverityBadge(alert.severity),
        formatDate(alert.created_at),
        <Button 
          size="slim" 
          onClick={() => handleResolve(alert.id)}
          disabled={alert.status === 'resolved'}
        >
          {alert.status === 'resolved' ? 'Resolved' : 'Resolve'}
        </Button>
      ]);

      setAlerts(formattedAlerts);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      showToast('Failed to load alerts');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else {
      return 'Just now';
    }
  };

  const getSeverityBadge = (severity) => {
    const statusMap = {
      critical: 'critical',
      warning: 'warning',
      info: 'info'
    };
    return <Badge status={statusMap[severity]}>{severity}</Badge>;
  };

  const handleResolve = async (alertId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/alerts/${alertId}/resolve`, {
        method: 'PUT'
      });
      
      if (response.ok) {
        showToast('Alert marked as resolved');
        fetchAlerts(); // Refresh the alerts list
      } else {
        showToast('Failed to resolve alert');
      }
    } catch (error) {
      console.error('Failed to resolve alert:', error);
      showToast('Failed to resolve alert');
    }
  };

  return (
    <Page 
      title="Inventory Alerts"
      breadcrumbs={[{content: 'Dashboard', url: '/'}]}
      primaryAction={{
        content: 'Configure Alerts',
        onAction: () => showToast('Alert configuration coming soon!')
      }}
    >
      <Layout>
        <Layout.Section>
          <Card>
            <div style={{padding: '20px', borderBottom: '1px solid #e1e3e5'}}>
              <InlineStack gap="200" align="center">
                <Button 
                  pressed={filter === 'all'} 
                  onClick={() => setFilter('all')}
                  outline={filter !== 'all'}
                >
                  All Alerts
                </Button>
                <Button 
                  pressed={filter === 'active'} 
                  onClick={() => setFilter('active')}
                  outline={filter !== 'active'}
                >
                  Active
                </Button>
                <Button 
                  pressed={filter === 'resolved'} 
                  onClick={() => setFilter('resolved')}
                  outline={filter !== 'resolved'}
                >
                  Resolved
                </Button>
              </InlineStack>
            </div>
            
            <div style={{padding: '20px'}}>
              {alerts.length > 0 ? (
                <DataTable
                  columnContentTypes={['text', 'text', 'text', 'text', 'text', 'text']}
                  headings={['Type', 'Product', 'Message', 'Severity', 'Created', 'Action']}
                  rows={alerts}
                />
              ) : (
                <div style={{textAlign: 'center', padding: '40px'}}>
                  <Text variant="bodyMd" color="subdued">
                    No alerts found for the selected filter.
                  </Text>
                </div>
              )}
            </div>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}

export default Alerts;