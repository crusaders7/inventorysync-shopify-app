import React, { useState, useEffect } from 'react';
import { Badge, Banner, BlockStack, Button, ButtonGroup, Card, DataTable, InlineStack, InlineStack Page, Layout, List, Loading, Modal, Page, ProgressBar, Select, Text, TextContainer, TextField, Tooltip } from '@shopify/polaris';
import {
  LocationMajor,
  TransferWithinShopifyMajor,
  AnalyticsMajor,
  ExportIcon,
  RefreshMajor,
  AlertMajor
} from '@shopify/polaris-icons';

const MultiLocationManager = ({ shop, showToast }) => {
  const [locations, setLocations] = useState([]);
  const [transferSuggestions, setTransferSuggestions] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [locationPerformance, setLocationPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [showLocationDetail, setShowLocationDetail] = useState(false);
  const [showCreateTransfer, setShowCreateTransfer] = useState(false);
  const [selectedTransfer, setSelectedTransfer] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);

  useEffect(() => {
    loadLocationData();
  }, []);

  const loadLocationData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchLocations(),
        fetchTransferSuggestions(),
        fetchHeatmapData()
      ]);
    } catch (error) {
      console.error('Failed to load location data:', error);
      showToast('Failed to load location data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/locations/?shop=${encodeURIComponent(shop)}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setLocations(data.locations || []);
      } else {
        throw new Error('Failed to fetch locations');
      }
    } catch (error) {
      console.error('Failed to fetch locations:', error);
      throw error;
    }
  };

  const fetchTransferSuggestions = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/locations/transfers/suggestions?shop=${encodeURIComponent(shop)}&limit=10`
      );
      
      if (response.ok) {
        const data = await response.json();
        setTransferSuggestions(data.suggestions || []);
      }
    } catch (error) {
      console.error('Failed to fetch transfer suggestions:', error);
    }
  };

  const fetchHeatmapData = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/locations/heatmap?shop=${encodeURIComponent(shop)}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setHeatmapData(data);
      }
    } catch (error) {
      console.error('Failed to fetch heatmap data:', error);
    }
  };

  const handleSyncLocations = async () => {
    setSyncing(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/locations/sync?shop=${encodeURIComponent(shop)}`,
        { method: 'POST' }
      );
      
      if (response.ok) {
        const data = await response.json();
        showToast(`Sync completed: ${data.locations_synced} locations processed`, 'success');
        await loadLocationData(); // Refresh data
      } else {
        throw new Error('Sync failed');
      }
    } catch (error) {
      console.error('Failed to sync locations:', error);
      showToast('Failed to sync locations', 'error');
    } finally {
      setSyncing(false);
    }
  };

  const handleLocationDetail = async (locationId) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/locations/${locationId}/performance?shop=${encodeURIComponent(shop)}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setLocationPerformance(data);
        setSelectedLocation(locations.find(l => l.id === locationId));
        setShowLocationDetail(true);
      } else {
        throw new Error('Failed to fetch location performance');
      }
    } catch (error) {
      console.error('Failed to fetch location performance:', error);
      showToast('Failed to load location details', 'error');
    }
  };

  const handleCreateTransfer = async (transferData) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/locations/transfers/create?shop=${encodeURIComponent(shop)}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(transferData)
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        showToast('Transfer order created successfully', 'success');
        setShowCreateTransfer(false);
        await fetchTransferSuggestions(); // Refresh suggestions
      } else {
        throw new Error('Failed to create transfer');
      }
    } catch (error) {
      console.error('Failed to create transfer:', error);
      showToast('Failed to create transfer order', 'error');
    }
  };

  const getLocationTypeBadge = (type) => {
    const badges = {
      'retail': <Badge status="success">Retail Store</Badge>,
      'warehouse': <Badge status="info">Warehouse</Badge>,
      'fulfillment': <Badge status="warning">Fulfillment</Badge>,
      'popup': <Badge>Pop-up Store</Badge>
    };
    return badges[type] || <Badge>{type}</Badge>;
  };

  const getPriorityBadge = (priority) => {
    const badges = {
      'critical': <Badge status="critical">Critical</Badge>,
      'high': <Badge status="warning">High</Badge>,
      'medium': <Badge status="attention">Medium</Badge>,
      'low': <Badge>Low</Badge>
    };
    return badges[priority] || <Badge>{priority}</Badge>;
  };

  const getUtilizationColor = (utilization) => {
    if (utilization < 0.3) return 'critical';
    if (utilization < 0.6) return 'warning';
    if (utilization < 0.8) return 'success';
    return 'warning'; // Over-utilized
  };

  const locationRows = locations.map((location) => [
    location.name,
    getLocationTypeBadge(location.type),
    location.is_primary ? <Badge status="success">Primary</Badge> : <Badge>Secondary</Badge>,
    location.is_active ? <Badge status="success">Active</Badge> : <Badge status="critical">Inactive</Badge>,
    location.inventory_tracked ? '✅' : '❌',
    <Button
      size="slim"
      onClick={() => handleLocationDetail(location.id)}
    >
      View Details
    </Button>
  ]);

  const transferRows = transferSuggestions.map((transfer) => [
    transfer.product_title,
    transfer.from_location_name,
    transfer.to_location_name,
    transfer.quantity.toString(),
    getPriorityBadge(transfer.priority),
    transfer.reason,
    <ButtonGroup>
      <Button
        size="slim"
        onClick={() => {
          setSelectedTransfer(transfer);
          setShowCreateTransfer(true);
        }}
      >
        Create Transfer
      </Button>
      <Button size="slim" outline>
        Dismiss
      </Button>
    </ButtonGroup>
  ]);

  if (loading) {
    return (
      <Page title="Multi-Location Management">
        <Layout>
          <Layout.Section>
            <Card>
              <div style={{ padding: '60px', textAlign: 'center' }}>
                <Loading />
                <Text>Loading location data...</Text>
              </div>
            </Card>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  return (
    <Page
      title="Multi-Location Management"
      subtitle="Sync and optimize inventory across all your locations"
      primaryAction={{
        content: syncing ? 'Syncing...' : 'Sync All Locations',
        onAction: handleSyncLocations,
        loading: syncing,
        icon: RefreshMajor
      }}
    >
      <Layout>
        {/* Overview Cards */}
        {heatmapData && (
          <Layout.Section>
            <Layout.Section secondary>
              <BlockStack gap="200">
                <Card>
                  <div style={{ padding: '16px' }}>
                    <BlockStack gap="100">
                      <Text variant="headingLg">
                        ${(heatmapData.metrics?.total_value || 0).toLocaleString()}
                      </Text>
                      <Text variant="bodySm" color="subdued">
                        Total Inventory Value
                      </Text>
                    </BlockStack>
                  </div>
                </Card>
                
                <Card>
                  <div style={{ padding: '16px' }}>
                    <BlockStack gap="100">
                      <Text variant="headingLg">
                        {(heatmapData.metrics?.average_utilization * 100 || 0).toFixed(1)}%
                      </Text>
                      <Text variant="bodySm" color="subdued">
                        Avg Utilization
                      </Text>
                    </BlockStack>
                  </div>
                </Card>

                <Card>
                  <div style={{ padding: '16px' }}>
                    <BlockStack gap="100">
                      <Text variant="headingLg">
                        {transferSuggestions.length}
                      </Text>
                      <Text variant="bodySm" color="subdued">
                        Transfer Suggestions
                      </Text>
                    </BlockStack>
                  </div>
                </Card>
              </BlockStack>
            </Layout.Section>

            <Layout.Section>
              <Card sectioned title="Location Utilization Heatmap">
                <BlockStack gap="200">
                  {heatmapData.locations?.map((location) => (
                    <div key={location.id} style={{ 
                      padding: '12px', 
                      backgroundColor: '#f6f6f7', 
                      borderRadius: '4px' 
                    }}>
                      <InlineStack gap="400">
                        <BlockStack gap="100">
                          <Text variant="bodySm" fontWeight="semibold">
                            {location.name}
                          </Text>
                          <Text variant="captionMd" color="subdued">
                            {location.product_count} products • ${location.inventory_value.toLocaleString()}
                          </Text>
                        </BlockStack>
                        <div style={{ width: '200px' }}>
                          <ProgressBar 
                            progress={location.utilization * 100}
                            size="small"
                            color={getUtilizationColor(location.utilization)}
                          />
                          <Text variant="captionMd">
                            {(location.utilization * 100).toFixed(1)}% utilized
                          </Text>
                        </div>
                      </BlockStack>
                    </div>
                  ))}
                </BlockStack>
              </Card>
            </Layout.Section>
          </Layout.Section>
        )}

        {/* Locations Table */}
        <Layout.Section>
          <Card title="Locations Overview">
            <DataTable
              columnContentTypes={['text', 'text', 'text', 'text', 'text', 'text']}
              headings={[
                'Location Name',
                'Type',
                'Role',
                'Status',
                'Inventory Tracked',
                'Actions'
              ]}
              rows={locationRows}
            />
            {locations.length === 0 && (
              <div style={{ padding: '40px', textAlign: 'center' }}>
                <Text color="subdued">
                  No locations found. Sync with Shopify to import your locations.
                </Text>
              </div>
            )}
          </Card>
        </Layout.Section>

        {/* Transfer Suggestions */}
        {transferSuggestions.length > 0 && (
          <Layout.Section>
            <Card title="Smart Transfer Suggestions">
              <DataTable
                columnContentTypes={['text', 'text', 'text', 'numeric', 'text', 'text', 'text']}
                headings={[
                  'Product',
                  'From Location',
                  'To Location',
                  'Quantity',
                  'Priority',
                  'Reason',
                  'Actions'
                ]}
                rows={transferRows}
              />
            </Card>
          </Layout.Section>
        )}

        {transferSuggestions.length === 0 && locations.length > 1 && (
          <Layout.Section>
            <Banner status="info">
              <p>
                No transfer suggestions at this time. Your inventory is well-balanced across locations!
              </p>
            </Banner>
          </Layout.Section>
        )}

        {locations.length < 2 && (
          <Layout.Section>
            <Banner status="warning">
              <p>
                Multi-location features require at least 2 active locations. 
                Make sure your Shopify store has multiple locations configured.
              </p>
            </Banner>
          </Layout.Section>
        )}
      </Layout>

      {/* Location Detail Modal */}
      <Modal
        open={showLocationDetail}
        onClose={() => setShowLocationDetail(false)}
        title={selectedLocation?.name || 'Location Details'}
        large
      >
        {locationPerformance && (
          <Modal.Section>
            <Layout>
              <Layout.Section oneThird>
                <Card sectioned title="Inventory Summary">
                  <BlockStack gap="200">
                    <div>
                      <Text variant="headingMd">{locationPerformance.inventory?.total_products || 0}</Text>
                      <Text variant="bodySm" color="subdued">Total Products</Text>
                    </div>
                    <div>
                      <Text variant="bodyLg">${(locationPerformance.inventory?.total_value || 0).toLocaleString()}</Text>
                      <Text variant="bodySm" color="subdued">Inventory Value</Text>
                    </div>
                    <div>
                      <Text variant="bodyLg" color="critical">{locationPerformance.inventory?.low_stock_items || 0}</Text>
                      <Text variant="bodySm" color="subdued">Low Stock Items</Text>
                    </div>
                  </BlockStack>
                </Card>
              </Layout.Section>

              <Layout.Section>
                <Card sectioned title="Performance Metrics">
                  <BlockStack gap="200">
                    <div>
                      <Text variant="bodySm">Sales Velocity</Text>
                      <Text variant="bodyLg">{locationPerformance.performance?.sales_velocity || 0} units/day</Text>
                    </div>
                    <div>
                      <Text variant="bodySm">Turnover Rate</Text>
                      <Text variant="bodyLg">{locationPerformance.performance?.turnover_rate || 0}x per year</Text>
                    </div>
                    <div>
                      <Text variant="bodySm">Efficiency Score</Text>
                      <ProgressBar 
                        progress={locationPerformance.performance?.efficiency_score * 100 || 0}
                        size="small"
                      />
                    </div>
                  </BlockStack>
                </Card>
              </Layout.Section>
            </Layout>

            {locationPerformance.recommendations && locationPerformance.recommendations.length > 0 && (
              <Card sectioned title="Recommendations">
                <List>
                  {locationPerformance.recommendations.map((rec, index) => (
                    <List.Item key={index}>
                      <Badge status={rec.priority === 'high' ? 'critical' : 'info'}>
                        {rec.type}
                      </Badge>
                      {rec.message}
                    </List.Item>
                  ))}
                </List>
              </Card>
            )}
          </Modal.Section>
        )}
      </Modal>

      {/* Create Transfer Modal */}
      <Modal
        open={showCreateTransfer}
        onClose={() => setShowCreateTransfer(false)}
        title="Create Transfer Order"
        primaryAction={{
          content: 'Create Transfer',
          onAction: () => selectedTransfer && handleCreateTransfer(selectedTransfer)
        }}
        secondaryActions={[
          {
            content: 'Cancel',
            onAction: () => setShowCreateTransfer(false)
          }
        ]}
      >
        {selectedTransfer && (
          <Modal.Section>
            <BlockStack gap="500">
              <TextContainer>
                <Text variant="headingMd">Transfer Details</Text>
                <p>
                  Transfer <strong>{selectedTransfer.quantity} units</strong> of{' '}
                  <strong>{selectedTransfer.product_title}</strong> from{' '}
                  <strong>{selectedTransfer.from_location_name}</strong> to{' '}
                  <strong>{selectedTransfer.to_location_name}</strong>
                </p>
              </TextContainer>

              <Banner status="info">
                <p><strong>Reason:</strong> {selectedTransfer.reason}</p>
                <p><strong>Priority:</strong> {selectedTransfer.priority}</p>
                <p><strong>Benefit Score:</strong> {(selectedTransfer.benefit_score * 100).toFixed(1)}%</p>
              </Banner>

              <Banner status="warning">
                <p>
                  This will create a transfer order in your system. Make sure to process 
                  the physical transfer of inventory between locations.
                </p>
              </Banner>
            </BlockStack>
          </Modal.Section>
        )}
      </Modal>
    </Page>
  );
};

export default MultiLocationManager;