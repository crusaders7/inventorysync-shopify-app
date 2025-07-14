/**
 * WorkflowManager - Advanced automation configuration
 * Create custom business logic and automation rules
 */

import React, { useState, useEffect } from 'react';
import { Badge, Banner, BlockStack, Button, ButtonGroup, Card, Checkbox, DataTable, EmptyState, Form, FormLayout, Frame, InlineStack, Layout, Modal, Page, Select, Spinner, Tabs, Text, TextField, Toast } from '@shopify/polaris';
import {
  AutomationMajor,
  EditMajor,
  DeleteMajor,
  CirclePlusMajor,
  ViewMajor,
  RefreshMajor,
  PlayMajor
} from '@shopify/polaris-icons';

const WorkflowManager = ({ shopDomain }) => {
  // Get shop domain with fallback
  const shop = shopDomain || 
    localStorage.getItem('shopDomain') || 
    localStorage.getItem('shopify_shop_domain') || 
    'inventorysync-dev.myshopify.com';
  
  // State management
  const [workflows, setWorkflows] = useState([]);
  const [templates, setTemplates] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState(null);
  const [toast, setToast] = useState(null);

  // Form state
  const [newWorkflow, setNewWorkflow] = useState({
    rule_name: '',
    description: '',
    trigger_event: 'inventory_low',
    trigger_conditions: {},
    actions: [],
    priority: 100,
    max_executions_per_hour: 60,
    is_active: true
  });

  // Constants
  const TRIGGER_EVENTS = [
    { label: 'Inventory Low', value: 'inventory_low' },
    { label: 'Custom Field Change', value: 'custom_field_change' },
    { label: 'Product Created', value: 'product_created' },
    { label: 'Variant Low Stock', value: 'variant_low_stock' },
    { label: 'Daily Schedule', value: 'daily_schedule' },
    { label: 'Manual', value: 'manual' }
  ];

  const ACTION_TYPES = [
    { label: 'Create Alert', value: 'create_alert' },
    { label: 'Update Field', value: 'update_field' },
    { label: 'Send Webhook', value: 'send_webhook' },
    { label: 'Send Email', value: 'send_email' }
  ];

  // Load data on component mount
  useEffect(() => {
    if (shop) {
      loadWorkflows();
      loadTemplates();
    }
  }, [shop]);

  // API Functions
  const loadWorkflows = async () => {
    if (!shop) {
      console.error('No shop domain available');
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/workflows/rules/${shop}?include_stats=true`);
      const data = await response.json();

      if (response.ok) {
        setWorkflows(data.rules);
      } else {
        throw new Error(data.error || 'Failed to load workflows');
      }
    } catch (error) {
      console.error('Error loading workflows:', error);
      setToast({ content: 'Failed to load workflows', error: true });
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/v1/workflows/templates');
      const data = await response.json();

      if (response.ok) {
        setTemplates(data.templates);
      }
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  const createWorkflow = async () => {
    try {
      const response = await fetch(`/api/v1/workflows/rules/${shop}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newWorkflow)
      });

      const data = await response.json();

      if (response.ok) {
        setToast({ content: 'Workflow created successfully', error: false });
        setShowCreateModal(false);
        resetNewWorkflow();
        loadWorkflows();
      } else {
        throw new Error(data.error || 'Failed to create workflow');
      }
    } catch (error) {
      console.error('Error creating workflow:', error);
      setToast({ content: error.message, error: true });
    }
  };

  const toggleWorkflow = async (workflowId, currentStatus) => {
    try {
      const response = await fetch(`/api/v1/workflows/rules/${workflowId}?shop_domain=${shop}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !currentStatus })
      });

      if (response.ok) {
        setToast({ content: 'Workflow updated successfully', error: false });
        loadWorkflows();
      } else {
        const data = await response.json();
        throw new Error(data.error || 'Failed to update workflow');
      }
    } catch (error) {
      console.error('Error updating workflow:', error);
      setToast({ content: error.message, error: true });
    }
  };

  const deleteWorkflow = async (workflowId) => {
    if (!confirm('Are you sure you want to delete this workflow?')) return;

    try {
      const response = await fetch(`/api/v1/workflows/rules/${workflowId}?shop_domain=${shop}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setToast({ content: 'Workflow deleted successfully', error: false });
        loadWorkflows();
      } else {
        const data = await response.json();
        throw new Error(data.error || 'Failed to delete workflow');
      }
    } catch (error) {
      console.error('Error deleting workflow:', error);
      setToast({ content: error.message, error: true });
    }
  };

  const testWorkflow = async (workflowId) => {
    try {
      const response = await fetch(`/api/v1/workflows/rules/${workflowId}/test?shop_domain=${shop}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_stock: 5,
          reorder_point: 10,
          sku: 'TEST-SKU-001'
        })
      });

      const data = await response.json();

      if (response.ok) {
        const message = data.would_execute ? 
          'Test passed! Workflow would execute with test data.' : 
          'Test completed. Workflow conditions not met with test data.';
        setToast({ content: message, error: false });
      } else {
        throw new Error(data.error || 'Failed to test workflow');
      }
    } catch (error) {
      console.error('Error testing workflow:', error);
      setToast({ content: error.message, error: true });
    }
  };

  const applyTemplate = (templateKey) => {
    const template = templates[templateKey];
    if (!template) return;

    setNewWorkflow({
      rule_name: template.name,
      description: template.description,
      trigger_event: template.trigger_event,
      trigger_conditions: template.trigger_conditions,
      actions: template.actions,
      priority: 100,
      max_executions_per_hour: 60,
      is_active: true
    });
    setShowCreateModal(true);
  };

  // Helper functions
  const resetNewWorkflow = () => {
    setNewWorkflow({
      rule_name: '',
      description: '',
      trigger_event: 'inventory_low',
      trigger_conditions: {},
      actions: [],
      priority: 100,
      max_executions_per_hour: 60,
      is_active: true
    });
  };

  const getStatusBadge = (workflow) => {
    return workflow.is_active ? 
      <Badge status="success">Active</Badge> : 
      <Badge>Inactive</Badge>;
  };

  const formatDate = (dateString) => {
    return dateString ? new Date(dateString).toLocaleString() : 'Never';
  };

  // DataTable columns
  const workflowsTableColumns = [
    { id: 'rule_name', label: 'Name', sortable: true },
    { id: 'trigger_event', label: 'Trigger Event', sortable: true },
    { id: 'status', label: 'Status' },
    { id: 'execution_count', label: 'Executions', sortable: true },
    { id: 'last_executed_at', label: 'Last Run', sortable: true },
    { id: 'actions', label: 'Actions' }
  ];

  const workflowsTableRows = workflows.map(workflow => [
    workflow.rule_name,
    TRIGGER_EVENTS.find(event => event.value === workflow.trigger_event)?.label || workflow.trigger_event,
    getStatusBadge(workflow),
    workflow.execution_count.toString(),
    formatDate(workflow.last_executed_at),
    (
      <ButtonGroup>
        <Button
          size="slim"
          icon={workflow.is_active ? 'pause' : PlayMajor}
          onClick={() => toggleWorkflow(workflow.id, workflow.is_active)}
        >
          {workflow.is_active ? 'Pause' : 'Activate'}
        </Button>
        <Button
          size="slim"
          icon={PlayMajor}
          onClick={() => testWorkflow(workflow.id)}
        >
          Test
        </Button>
        <Button
          size="slim"
          icon={ViewMajor}
          onClick={() => setEditingWorkflow(workflow)}
        >
          View
        </Button>
        <Button
          size="slim"
          icon={DeleteMajor}
          destructive
          onClick={() => deleteWorkflow(workflow.id)}
        >
          Delete
        </Button>
      </ButtonGroup>
    )
  ]);

  // Templates panel
  const templatesPanel = (
    <Layout>
      <Layout.Section>
        <Banner status="info">
          <p>Use these pre-built templates to quickly set up common automation scenarios.</p>
        </Banner>
      </Layout.Section>
      
      {Object.entries(templates).map(([key, template]) => (
        <Layout.Section key={key}>
          <Card sectioned>
            <InlineStack align="space-between" wrap={false}>
              <BlockStack gap="200">
                <Text variant="headingMd" as="h2">{template.name}</Text>
                <p>{template.description}</p>
                <Badge>{TRIGGER_EVENTS.find(e => e.value === template.trigger_event)?.label}</Badge>
              </BlockStack>
              <Button primary onClick={() => applyTemplate(key)}>
                Use Template
              </Button>
            </InlineStack>
          </Card>
        </Layout.Section>
      ))}
    </Layout>
  );

  // Tabs
  const tabs = [
    {
      id: 'workflows',
      content: 'Active Workflows',
      accessibilityLabel: 'Active workflows',
      panelID: 'workflows-panel'
    },
    {
      id: 'templates',
      content: 'Templates',
      accessibilityLabel: 'Workflow templates',
      panelID: 'templates-panel'
    }
  ];

  return (
    <Frame>
      <Page
        title="Workflow Automation"
        primaryAction={{
          content: 'Create Workflow',
          icon: CirclePlusMajor,
          onAction: () => setShowCreateModal(true)
        }}
        secondaryActions={[
          {
            content: 'Refresh',
            icon: RefreshMajor,
            onAction: loadWorkflows
          }
        ]}
      >
        <Tabs tabs={tabs} selected={selectedTab} onSelect={setSelectedTab}>
          {selectedTab === 0 && (
            <Layout>
              <Layout.Section>
                <Card>
                  {loading ? (
                    <div style={{ padding: '2rem', textAlign: 'center' }}>
                      <Spinner size="large" />
                    </div>
                  ) : workflows.length > 0 ? (
                    <DataTable
                      columnContentTypes={['text', 'text', 'text', 'numeric', 'text', 'text']}
                      headings={workflowsTableColumns.map(col => col.label)}
                      rows={workflowsTableRows}
                    />
                  ) : (
                    <EmptyState
                      heading="No workflows found"
                      image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
                      action={{
                        content: 'Create Workflow',
                        onAction: () => setShowCreateModal(true)
                      }}
                    >
                      <p>Automate your inventory management with custom workflows.</p>
                    </EmptyState>
                  )}
                </Card>
              </Layout.Section>
            </Layout>
          )}

          {selectedTab === 1 && templatesPanel}
        </Tabs>

        {/* Create Workflow Modal */}
        <Modal
          open={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create New Workflow"
          primaryAction={{
            content: 'Create Workflow',
            onAction: createWorkflow
          }}
          secondaryActions={[{
            content: 'Cancel',
            onAction: () => setShowCreateModal(false)
          }]}
        >
          <Modal.Section>
            <Form onSubmit={createWorkflow}>
              <FormLayout>
                <TextField
                  label="Workflow Name"
                  value={newWorkflow.rule_name}
                  onChange={(value) => setNewWorkflow(prev => ({ ...prev, rule_name: value }))}
                  required
                />
                
                <TextField
                  label="Description"
                  value={newWorkflow.description}
                  onChange={(value) => setNewWorkflow(prev => ({ ...prev, description: value }))}
                  multiline={3}
                />
                
                <Select
                  label="Trigger Event"
                  options={TRIGGER_EVENTS}
                  value={newWorkflow.trigger_event}
                  onChange={(value) => setNewWorkflow(prev => ({ ...prev, trigger_event: value }))}
                />
                
                <FormLayout.Group>
                  <TextField
                    label="Priority"
                    type="number"
                    value={newWorkflow.priority.toString()}
                    onChange={(value) => setNewWorkflow(prev => ({ ...prev, priority: parseInt(value) || 100 }))}
                    helpText="Lower number = higher priority"
                  />
                  <TextField
                    label="Max Executions/Hour"
                    type="number"
                    value={newWorkflow.max_executions_per_hour.toString()}
                    onChange={(value) => setNewWorkflow(prev => ({ ...prev, max_executions_per_hour: parseInt(value) || 60 }))}
                  />
                </FormLayout.Group>
                
                <Checkbox
                  label="Active"
                  checked={newWorkflow.is_active}
                  onChange={(value) => setNewWorkflow(prev => ({ ...prev, is_active: value }))}
                />
              </FormLayout>
            </Form>
          </Modal.Section>
        </Modal>

        {/* Workflow Details Modal */}
        {editingWorkflow && (
          <Modal
            open={true}
            onClose={() => setEditingWorkflow(null)}
            title="Workflow Details"
            secondaryActions={[{
              content: 'Close',
              onAction: () => setEditingWorkflow(null)
            }]}
          >
            <Modal.Section>
              <BlockStack gap="loose">
                <InlineStack align="space-between">
                  <Text variant="headingMd" as="h2">{editingWorkflow.rule_name}</Text>
                  {getStatusBadge(editingWorkflow)}
                </InlineStack>
                
                <div>
                  <Text variant="headingSm" as="h3">Description</Text>
                  <p>{editingWorkflow.description || 'No description provided'}</p>
                </div>
                
                <div>
                  <Text variant="headingSm" as="h3">Trigger Event</Text>
                  <p>{TRIGGER_EVENTS.find(e => e.value === editingWorkflow.trigger_event)?.label}</p>
                </div>
                
                <div>
                  <Text variant="headingSm" as="h3">Execution Statistics</Text>
                  <p>Total executions: {editingWorkflow.execution_count}</p>
                  <p>Last executed: {formatDate(editingWorkflow.last_executed_at)}</p>
                  {editingWorkflow.stats && (
                    <div>
                      <p>Success rate: {editingWorkflow.stats.last_30_days.success_rate.toFixed(1)}%</p>
                      <p>Avg execution time: {editingWorkflow.stats.last_30_days.avg_execution_time_ms}ms</p>
                    </div>
                  )}
                </div>
                
                <div>
                  <Text variant="headingSm" as="h3">Actions</Text>
                  <p>{editingWorkflow.actions.length} action(s) configured</p>
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

export default WorkflowManager;
