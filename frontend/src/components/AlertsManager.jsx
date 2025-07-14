/**
 * AlertsManager - Enhanced alerts management with custom templates
 * Advanced notification system with filtering, analytics, and template support
 */

import React, { useState, useEffect } from 'react';
import { Badge, Banner, BlockStack, Button, ButtonGroup, Card, Checkbox, ChoiceList, DataTable, EmptyState, Filters, Form, FormLayout, Frame, InlineStack, Layout, Modal, Page, Pagination, ProgressBar, Select, Spinner, Tabs, Text, TextField, Toast } from '@shopify/polaris';
import {
  ViewMajor,
  RefreshMajor,
  CirclePlusMajor
} from '@shopify/polaris-icons';

const AlertsManager = ({ shopDomain }) => {
  // State management
  const [alerts, setAlerts] = useState([]);
  const [alertTemplates, setAlertTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [editingAlert, setEditingAlert] = useState(null);
  const [toast, setToast] = useState(null);
  
  // Filters and pagination
  const [filters, setFilters] = useState({
    status: [],
    severity: [],
    alert_type: [],
    search: ''
  });
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
    total_count: 0,
    has_more: false
  });
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Analytics data
  const [analytics, setAnalytics] = useState(null);

  // Form states
  const [newAlert, setNewAlert] = useState({
    alert_type: 'manual',
    severity: 'medium',
    title: '',
    message: '',
    product_sku: '',
    location_name: '',
    current_stock: '',
    recommended_action: '',
    notification_channels: [],
    auto_resolve_hours: ''
  });

  const [newTemplate, setNewTemplate] = useState({
    template_name: '',
    description: '',
    alert_type: 'custom',
    title_template: '',
    message_template: '',
    severity: 'medium',
    trigger_conditions: {},
    notification_channels: [],
    auto_resolve_hours: ''
  });

  // Constants
  const ALERT_TYPES = [
    { label: 'Low Stock', value: 'low_stock' },
    { label: 'Overstock', value: 'overstock' },
    { label: 'Reorder', value: 'reorder' },
    { label: 'Compliance', value: 'compliance' },
    { label: 'Workflow', value: 'workflow' },
    { label: 'Custom', value: 'custom' },
    { label: 'Manual', value: 'manual' }
  ];

  const SEVERITY_LEVELS = [
    { label: 'Low', value: 'low' },
    { label: 'Medium', value: 'medium' },
    { label: 'High', value: 'high' },
    { label: 'Critical', value: 'critical' }
  ];

  const STATUS_OPTIONS = [
    { label: 'Active', value: 'active' },
    { label: 'Acknowledged', value: 'acknowledged' },
    { label: 'Resolved', value: 'resolved' }
  ];

  const NOTIFICATION_CHANNELS = [
    { label: 'Email', value: 'email' },
    { label: 'Webhook', value: 'webhook' },
    { label: 'SMS', value: 'sms' }
  ];

  // Load data on component mount
  useEffect(() => {
    loadAlerts();
    loadAnalytics();
  }, [filters, pagination.offset, sortBy, sortOrder]);

  // API Functions
  const loadAlerts = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams({
        limit: pagination.limit,
        offset: pagination.offset,
        sort_by: sortBy,
        sort_order: sortOrder
      });

      if (filters.status.length > 0) params.append('status', filters.status[0]);
      if (filters.severity.length > 0) params.append('severity', filters.severity[0]);
      if (filters.alert_type.length > 0) params.append('alert_type', filters.alert_type[0]);

      const response = await fetch(`/api/v1/alerts/${shopDomain}?${params}`);
      const data = await response.json();

      if (response.ok) {
        setAlerts(data.alerts);
        setPagination(prev => ({
          ...prev,
          total_count: data.total_count,
          has_more: data.has_more
        }));
      } else {
        throw new Error(data.error || 'Failed to load alerts');
      }
    } catch (error) {
      console.error('Error loading alerts:', error);
      setToast({ content: 'Failed to load alerts', error: true });
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch(`/api/v1/alerts/analytics/${shopDomain}`);
      const data = await response.json();

      if (response.ok) {
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const createAlert = async () => {
    try {
      const response = await fetch(`/api/v1/alerts/${shopDomain}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newAlert,
          current_stock: newAlert.current_stock ? parseInt(newAlert.current_stock) : null,
          auto_resolve_hours: newAlert.auto_resolve_hours ? parseInt(newAlert.auto_resolve_hours) : null
        })
      });

      const data = await response.json();

      if (response.ok) {
        setToast({ content: 'Alert created successfully', error: false });
        setShowCreateModal(false);
        resetNewAlert();
        loadAlerts();
      } else {
        throw new Error(data.error || 'Failed to create alert');
      }
    } catch (error) {
      console.error('Error creating alert:', error);
      setToast({ content: error.message, error: true });
    }
  };

  const updateAlert = async (alertId, updates) => {
    try {
      const response = await fetch(`/api/v1/alerts/${alertId}?shop_domain=${shopDomain}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });

      const data = await response.json();

      if (response.ok) {
        setToast({ content: 'Alert updated successfully', error: false });
        loadAlerts();
      } else {
        throw new Error(data.error || 'Failed to update alert');
      }
    } catch (error) {
      console.error('Error updating alert:', error);
      setToast({ content: error.message, error: true });
    }
  };

  // Helper functions
  const resetNewAlert = () => {
    setNewAlert({
      alert_type: 'manual',
      severity: 'medium',
      title: '',
      message: '',
      product_sku: '',
      location_name: '',
      current_stock: '',
      recommended_action: '',
      notification_channels: [],
      auto_resolve_hours: ''
    });
  };

  const getSeverityBadge = (severity) => {
    const statusMap = {
      low: 'info',
      medium: 'attention',
      high: 'warning',
      critical: 'critical'
    };
    return <Badge status={statusMap[severity] || 'info'}>{severity.toUpperCase()}</Badge>;
  };

  const getStatusBadge = (alert) => {
    if (alert.is_resolved) {
      return <Badge status="success">Resolved</Badge>;
    } else if (alert.is_acknowledged) {
      return <Badge status="info">Acknowledged</Badge>;
    } else {
      return <Badge status="attention">Active</Badge>;
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  // DataTable columns
  const alertsTableColumns = [
    {
      id: 'severity',
      label: 'Severity',
      sortable: true
    },
    {
      id: 'title',
      label: 'Title',
      sortable: true
    },
    {
      id: 'alert_type',
      label: 'Type',
      sortable: true
    },
    {
      id: 'status',
      label: 'Status'
    },
    {
      id: 'created_at',
      label: 'Created',
      sortable: true
    },
    {
      id: 'actions',
      label: 'Actions'
    }
  ];

  const alertsTableRows = alerts.map(alert => [
    getSeverityBadge(alert.severity),
    alert.title,
    ALERT_TYPES.find(type => type.value === alert.alert_type)?.label || alert.alert_type,
    getStatusBadge(alert),
    formatDate(alert.created_at),
    (
      <ButtonGroup>
        {!alert.is_acknowledged && (
          <Button
            size="slim"
            onClick={() => updateAlert(alert.id, { is_acknowledged: true, acknowledged_by: 'admin' })}
          >
            Acknowledge
          </Button>
        )}
        {!alert.is_resolved && (
          <Button
            size="slim"
            onClick={() => updateAlert(alert.id, { is_resolved: true, resolved_by: 'admin' })}
          >
            Resolve
          </Button>
        )}
        <Button
          size="slim"
            icon={ViewMajor}
          onClick={() => setEditingAlert(alert)}
        >
          View
        </Button>
      </ButtonGroup>
    )
  ]);

  // Filter components
  const filterControl = (
    <Filters
      queryValue={filters.search}
      filters={[
        {
          key: 'status',
          label: 'Status',
          filter: (
            <ChoiceList
              title="Status"
              titleHidden
              choices={STATUS_OPTIONS}
              selected={filters.status}
              onChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
              allowMultiple={false}
            />
          ),
          shortcut: true
        },
        {
          key: 'severity',
          label: 'Severity',
          filter: (
            <ChoiceList
              title="Severity"
              titleHidden
              choices={SEVERITY_LEVELS}
              selected={filters.severity}
              onChange={(value) => setFilters(prev => ({ ...prev, severity: value }))}
              allowMultiple={false}
            />
          )
        },
        {
          key: 'alert_type',
          label: 'Type',
          filter: (
            <ChoiceList
              title="Alert Type"
              titleHidden
              choices={ALERT_TYPES}
              selected={filters.alert_type}
              onChange={(value) => setFilters(prev => ({ ...prev, alert_type: value }))}
              allowMultiple={false}
            />
          )
        }
      ]}
      appliedFilters={[
        ...filters.status.map(status => ({
          key: 'status',
          label: `Status: ${STATUS_OPTIONS.find(opt => opt.value === status)?.label}`,
          onRemove: () => setFilters(prev => ({ ...prev, status: [] }))
        })),
        ...filters.severity.map(severity => ({
          key: 'severity',
          label: `Severity: ${SEVERITY_LEVELS.find(opt => opt.value === severity)?.label}`,
          onRemove: () => setFilters(prev => ({ ...prev, severity: [] }))
        })),
        ...filters.alert_type.map(type => ({
          key: 'alert_type',
          label: `Type: ${ALERT_TYPES.find(opt => opt.value === type)?.label}`,
          onRemove: () => setFilters(prev => ({ ...prev, alert_type: [] }))
        }))
      ]}
      onQueryChange={(value) => setFilters(prev => ({ ...prev, search: value }))}
      onQueryClear={() => setFilters(prev => ({ ...prev, search: '' }))}
      onClearAll={() => setFilters({ status: [], severity: [], alert_type: [], search: '' })}
    />
  );

  // Tabs
  const tabs = [
    {
      id: 'alerts',
      content: 'Active Alerts',
      accessibilityLabel: 'Active alerts',
      panelID: 'alerts-panel'
    },
    {
      id: 'analytics',
      content: 'Analytics',
      accessibilityLabel: 'Alert analytics',
      panelID: 'analytics-panel'
    },
    {
      id: 'templates',
      content: 'Templates',
      accessibilityLabel: 'Alert templates',
      panelID: 'templates-panel'
    }
  ];

  // Analytics panel
  const analyticsPanel = analytics && (
    <Layout>
      <Layout.Section oneHalf>
        <Card sectioned>
          <Text variant="headingMd" as="h2">Alert Summary (Last 30 Days)</Text>
          <div style={{ marginTop: '1rem' }}>
            <InlineStack distribution="fillEvenly">
              <BlockStack spacing="tight">
                <Text variant="headingXl" as="p">{analytics.summary.total_alerts}</Text>
                <Text variant="bodySm" as="p" color="subdued">Total Alerts</Text>
              </BlockStack>
              <BlockStack spacing="tight">
                <Text variant="headingXl" as="p">{analytics.summary.active_alerts}</Text>
                <Text variant="bodySm" as="p" color="subdued">Active</Text>
              </BlockStack>
              <BlockStack spacing="tight">
                <Text variant="headingXl" as="p">{analytics.summary.resolved_alerts}</Text>
                <Text variant="bodySm" as="p" color="subdued">Resolved</Text>
              </BlockStack>
              <BlockStack spacing="tight">
                <Text variant="headingXl" as="p">{analytics.summary.resolution_rate.toFixed(1)}%</Text>
                <Text variant="bodySm" as="p" color="subdued">Resolution Rate</Text>
              </BlockStack>
            </InlineStack>
          </div>
        </Card>
      </Layout.Section>

      <Layout.Section oneHalf>
        <Card sectioned>
          <Text variant="headingMd" as="h2">Alerts by Severity</Text>
          <div style={{ marginTop: '1rem' }}>
            {analytics.breakdown.by_severity.map(item => (
              <div key={item.severity} style={{ marginBottom: '0.5rem' }}>
                <InlineStack distribution="equalSpacing">
                  <span>{item.severity.toUpperCase()}</span>
                  <span>{item.count}</span>
                </InlineStack>
                <ProgressBar 
                  progress={(item.count / analytics.summary.total_alerts) * 100} 
                  size="small" 
                />
              </div>
            ))}
          </div>
        </Card>
      </Layout.Section>

      <Layout.Section>
        <Card sectioned>
          <Text variant="headingMd" as="h2">Alerts by Type</Text>
          <DataTable
            columnContentTypes={['text', 'numeric']}
            headings={['Type', 'Count']}
            rows={analytics.breakdown.by_type.map(item => [
              ALERT_TYPES.find(type => type.value === item.alert_type)?.label || item.alert_type,
              item.count
            ])}
          />
        </Card>
      </Layout.Section>
    </Layout>
  );

  return (
    <Frame>
      <Page
        title="Alerts Management"
        primaryAction={{
          content: 'Create Alert',
          icon: CirclePlusMajor,
          onAction: () => setShowCreateModal(true)
        }}
        secondaryActions={[
          {
            content: 'Refresh',
            icon: RefreshMajor,
            onAction: loadAlerts
          },
          {
            content: 'Create Template',
            onAction: () => setShowTemplateModal(true)
          }
        ]}
      >
        <Tabs tabs={tabs} selected={selectedTab} onSelect={setSelectedTab}>
          {selectedTab === 0 && (
            <Layout>
              <Layout.Section>
                <Card>
                  <div style={{ padding: '1rem' }}>
                    {filterControl}
                  </div>
                  
                  {loading ? (
                    <div style={{ padding: '2rem', textAlign: 'center' }}>
                      <Spinner size="large" />
                    </div>
                  ) : alerts.length > 0 ? (
                    <>
                      <DataTable
                        columnContentTypes={['text', 'text', 'text', 'text', 'text', 'text']}
                        headings={alertsTableColumns.map(col => col.label)}
                        rows={alertsTableRows}
                        sortable={alertsTableColumns.map(col => col.sortable)}
                        defaultSortDirection="descending"
                        initialSortColumnIndex={4}
                        onSort={(headingIndex, direction) => {
                          const column = alertsTableColumns[headingIndex];
                          if (column.sortable) {
                            setSortBy(column.id);
                            setSortOrder(direction);
                          }
                        }}
                      />
                      
                      <div style={{ padding: '1rem', borderTop: '1px solid #e1e3e5' }}>
                        <InlineStack distribution="center">
                          <Pagination
                            hasPrevious={pagination.offset > 0}
                            hasNext={pagination.has_more}
                            onPrevious={() => setPagination(prev => ({ 
                              ...prev, 
                              offset: Math.max(0, prev.offset - prev.limit) 
                            }))}
                            onNext={() => setPagination(prev => ({ 
                              ...prev, 
                              offset: prev.offset + prev.limit 
                            }))}
                          />
                        </InlineStack>
                      </div>
                    </>
                  ) : (
                    <EmptyState
                      heading="No alerts found"
                      image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
                      action={{
                        content: 'Create Alert',
                        onAction: () => setShowCreateModal(true)
                      }}
                    >
                      <p>Create your first alert or adjust your filters to see results.</p>
                    </EmptyState>
                  )}
                </Card>
              </Layout.Section>
            </Layout>
          )}

          {selectedTab === 1 && analyticsPanel}

          {selectedTab === 2 && (
            <Layout>
              <Layout.Section>
                <Card sectioned>
                  <Text variant="headingMd" as="h2">Alert Templates</Text>
                  <p>Create reusable alert templates for common scenarios.</p>
                  <div style={{ marginTop: '1rem' }}>
                    <Button primary onClick={() => setShowTemplateModal(true)}>
                      Create Template
                    </Button>
                  </div>
                </Card>
              </Layout.Section>
            </Layout>
          )}
        </Tabs>

        {/* Create Alert Modal */}
        <Modal
          open={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create New Alert"
          primaryAction={{
            content: 'Create Alert',
            onAction: createAlert
          }}
          secondaryActions={[{
            content: 'Cancel',
            onAction: () => setShowCreateModal(false)
          }]}
        >
          <Modal.Section>
            <Form onSubmit={createAlert}>
              <FormLayout>
                <FormLayout.Group>
                  <Select
                    label="Alert Type"
                    options={ALERT_TYPES}
                    value={newAlert.alert_type}
                    onChange={(value) => setNewAlert(prev => ({ ...prev, alert_type: value }))}
                  />
                  <Select
                    label="Severity"
                    options={SEVERITY_LEVELS}
                    value={newAlert.severity}
                    onChange={(value) => setNewAlert(prev => ({ ...prev, severity: value }))}
                  />
                </FormLayout.Group>
                
                <TextField
                  label="Title"
                  value={newAlert.title}
                  onChange={(value) => setNewAlert(prev => ({ ...prev, title: value }))}
                  required
                />
                
                <TextField
                  label="Message"
                  value={newAlert.message}
                  onChange={(value) => setNewAlert(prev => ({ ...prev, message: value }))}
                  required
                  multiline={4}
                />
                
                <FormLayout.Group>
                  <TextField
                    label="Product SKU"
                    value={newAlert.product_sku}
                    onChange={(value) => setNewAlert(prev => ({ ...prev, product_sku: value }))}
                  />
                  <TextField
                    label="Location"
                    value={newAlert.location_name}
                    onChange={(value) => setNewAlert(prev => ({ ...prev, location_name: value }))}
                  />
                </FormLayout.Group>
                
                <FormLayout.Group>
                  <TextField
                    label="Current Stock"
                    type="number"
                    value={newAlert.current_stock}
                    onChange={(value) => setNewAlert(prev => ({ ...prev, current_stock: value }))}
                  />
                  <TextField
                    label="Auto-resolve (hours)"
                    type="number"
                    value={newAlert.auto_resolve_hours}
                    onChange={(value) => setNewAlert(prev => ({ ...prev, auto_resolve_hours: value }))}
                    helpText="Alert will auto-resolve after this many hours"
                  />
                </FormLayout.Group>
                
                <TextField
                  label="Recommended Action"
                  value={newAlert.recommended_action}
                  onChange={(value) => setNewAlert(prev => ({ ...prev, recommended_action: value }))}
                  multiline={3}
                />
              </FormLayout>
            </Form>
          </Modal.Section>
        </Modal>

        {/* Alert Details Modal */}
        {editingAlert && (
          <Modal
            open={true}
            onClose={() => setEditingAlert(null)}
            title="Alert Details"
            secondaryActions={[{
              content: 'Close',
              onAction: () => setEditingAlert(null)
            }]}
          >
            <Modal.Section>
              <BlockStack spacing="loose">
                <InlineStack distribution="equalSpacing">
                  <Text variant="headingMd" as="h2">{editingAlert.title}</Text>
                  {getSeverityBadge(editingAlert.severity)}
                </InlineStack>
                
                <div>
                  <Text variant="headingSm" as="h3">Message</Text>
                  <p>{editingAlert.message}</p>
                </div>
                
                {editingAlert.product_sku && (
                  <div>
                    <Text variant="headingSm" as="h3">Product SKU</Text>
                    <p>{editingAlert.product_sku}</p>
                  </div>
                )}
                
                {editingAlert.recommended_action && (
                  <div>
                    <Text variant="headingSm" as="h3">Recommended Action</Text>
                    <p>{editingAlert.recommended_action}</p>
                  </div>
                )}
                
                <div>
                  <Text variant="headingSm" as="h3">Status</Text>
                  <p>
                    {getStatusBadge(editingAlert)}
                    {editingAlert.is_acknowledged && editingAlert.acknowledged_at && (
                      <span style={{ marginLeft: '1rem' }}>
                        Acknowledged on {formatDate(editingAlert.acknowledged_at)}
                      </span>
                    )}
                    {editingAlert.is_resolved && editingAlert.resolved_at && (
                      <span style={{ marginLeft: '1rem' }}>
                        Resolved on {formatDate(editingAlert.resolved_at)}
                      </span>
                    )}
                  </p>
                </div>
                
                <div>
                  <Text variant="headingSm" as="h3">Created</Text>
                  <p>{formatDate(editingAlert.created_at)}</p>
                </div>
              </BlockStack>
            </Modal.Section>
          </Modal>
        )}

        {/* Toast notifications */}
        {toast && (
          <Toast
            content={toast.content}
            error={toast.error}
            onDismiss={() => setToast(null)}
          />
        )}
      </Page>
    </Frame>
  );
};

export default AlertsManager;
