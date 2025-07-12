import React, { useState, useEffect, useCallback } from 'react';
import {
  Page,
  Layout,
  Card,
  Button,
  TextField,
  Select,
  Badge,
  Text,
  Banner,
  Modal,
  RadioButton,
  Checkbox,
  Icon,
  Tabs,
  EmptyState,
  SkeletonBodyText,
  ResourceList,
  ResourceItem,
  Avatar,
  ButtonGroup,
  FormLayout,
  TextContainer,
} from '@shopify/polaris';
import {
  SearchMinor,
  FilterMinor,
  ImportMinor,
  ExportMinor,
  CirclePlusMinor,
} from '@shopify/polaris-icons';

const CustomFieldsEnhancedSimple = () => {
  // State management
  const [fields, setFields] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedTab, setSelectedTab] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [selectedFields, setSelectedFields] = useState([]);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [statistics, setStatistics] = useState(null);

  // Get shop domain
  const shopDomain = window.shopDomain || 'inventorysync-dev.myshopify.com';

  // Field types with enhanced options
  const fieldTypes = [
    { label: 'Text', value: 'text' },
    { label: 'Number', value: 'number' },
    { label: 'Select', value: 'select' },
    { label: 'Multi-Select', value: 'multiselect' },
    { label: 'Boolean', value: 'boolean' },
    { label: 'Date', value: 'date' },
    { label: 'Email', value: 'email' },
    { label: 'URL', value: 'url' },
    { label: 'Text Area', value: 'textarea' },
    { label: 'JSON', value: 'json' },
  ];

  // Fetch functions
  const fetchFields = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('q', searchTerm);
      if (selectedType) params.append('field_type', selectedType);

      const response = await fetch(
        `/api/custom-fields/search/${shopDomain}?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || 'dev-token'}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setFields(data.fields);
      }
    } catch (error) {
      console.error('Error fetching fields:', error);
    } finally {
      setLoading(false);
    }
  }, [shopDomain, searchTerm, selectedType]);

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/custom-fields/templates', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'dev-token'}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates);
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await fetch(`/api/custom-fields/statistics/${shopDomain}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'dev-token'}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  useEffect(() => {
    fetchFields();
    fetchTemplates();
    fetchStatistics();
  }, [fetchFields]);

  // Apply template
  const applyTemplate = async (templateId) => {
    setSaving(true);
    try {
      const response = await fetch(
        `/api/custom-fields/templates/${templateId}/apply/${shopDomain}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || 'dev-token'}`,
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log('Template applied:', result);
        fetchFields();
        setShowTemplateModal(false);
      }
    } catch (error) {
      console.error('Error applying template:', error);
    } finally {
      setSaving(false);
    }
  };

  // Tabs
  const tabs = [
    {
      id: 'fields',
      content: 'Fields',
      badge: fields.length.toString(),
      panelID: 'fields-panel',
    },
    {
      id: 'templates',
      content: 'Templates',
      badge: templates.length.toString(),
      panelID: 'templates-panel',
    },
    {
      id: 'analytics',
      content: 'Analytics',
      panelID: 'analytics-panel',
    },
  ];

  // Resource list view for fields
  const renderFieldItem = (field) => {
    const { id, name, label, field_type, is_active, description } = field;

    return (
      <ResourceItem
        id={id}
        accessibilityLabel={`View details for ${name}`}
        name={name}
        onClick={() => console.log('Edit field:', id)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ flex: 1 }}>
            <Text variant="bodyMd" fontWeight="semibold">{label}</Text>
            {description && (
              <Text variant="bodySm" color="subdued">{description}</Text>
            )}
          </div>
          <Badge status={is_active ? 'success' : 'default'}>
            {is_active ? 'Active' : 'Inactive'}
          </Badge>
          <Badge>{field_type}</Badge>
        </div>
      </ResourceItem>
    );
  };

  // Template modal
  const templateModal = (
    <Modal
      open={showTemplateModal}
      onClose={() => setShowTemplateModal(false)}
      title="Choose a Template"
      primaryAction={{
        content: 'Cancel',
        onAction: () => setShowTemplateModal(false),
      }}
    >
      <Modal.Section>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {templates.map((template) => (
            <Card
              key={template.id}
              sectioned
              onClick={() => applyTemplate(template.id)}
            >
              <div style={{ cursor: 'pointer' }}>
                <Text variant="bodyMd" fontWeight="semibold">{template.name}</Text>
                <Text variant="bodySm" color="subdued">{template.description}</Text>
                <div style={{ marginTop: '8px', display: 'flex', gap: '8px' }}>
                  <Badge>{template.category}</Badge>
                  <Badge status="info">{template.field_count} fields</Badge>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </Modal.Section>
    </Modal>
  );

  // Analytics view
  const renderAnalytics = () => {
    if (!statistics) return <SkeletonBodyText lines={5} />;

    return (
      <Layout>
        <Layout.Section oneThird>
          <Card title="Field Statistics" sectioned>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>Total Fields</Text>
                <Text variant="headingMd">{statistics.total_fields}</Text>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>Active Fields</Text>
                <Text variant="headingMd" color="success">{statistics.active_fields}</Text>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>Usage Rate</Text>
                <Badge status="success">{statistics.usage_percentage.toFixed(1)}%</Badge>
              </div>
            </div>
          </Card>
        </Layout.Section>

        <Layout.Section oneThird>
          <Card title="Fields by Type" sectioned>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {Object.entries(statistics.fields_by_type || {}).map(([type, count]) => (
                <div key={type} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Badge>{type}</Badge>
                  <Text>{count}</Text>
                </div>
              ))}
            </div>
          </Card>
        </Layout.Section>

        <Layout.Section oneThird>
          <Card title="Quick Actions" sectioned>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <Button fullWidth onClick={() => setShowTemplateModal(true)}>
                Apply Template
              </Button>
              <Button fullWidth plain>
                Export Configuration
              </Button>
              <Button fullWidth plain>
                Import Configuration
              </Button>
            </div>
          </Card>
        </Layout.Section>
      </Layout>
    );
  };

  return (
    <Page
      title="Custom Fields Manager"
      subtitle="Enhanced field management with templates and bulk operations"
      primaryAction={{
        content: 'Add Field',
        onAction: () => console.log('Add field'),
      }}
      secondaryActions={[
        {
          content: 'Import',
          icon: ImportMinor,
          onAction: () => console.log('Import'),
        },
        {
          content: 'Export',
          icon: ExportMinor,
          onAction: () => console.log('Export'),
        },
      ]}
    >
      <Tabs tabs={tabs} selected={selectedTab} onSelect={setSelectedTab}>
        {selectedTab === 0 && (
          <Card>
            <Card.Section>
              <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                <div style={{ flex: 1 }}>
                  <TextField
                    value={searchTerm}
                    onChange={setSearchTerm}
                    placeholder="Search fields..."
                    clearButton
                    onClearButtonClick={() => setSearchTerm('')}
                  />
                </div>
                <Select
                  label="Type"
                  labelHidden
                  options={[{ label: 'All types', value: '' }, ...fieldTypes]}
                  value={selectedType}
                  onChange={setSelectedType}
                />
                <Button
                  icon={CirclePlusMinor}
                  onClick={() => setShowTemplateModal(true)}
                >
                  Templates
                </Button>
              </div>
            </Card.Section>

            {loading ? (
              <Card.Section>
                <SkeletonBodyText lines={5} />
              </Card.Section>
            ) : fields.length === 0 ? (
              <EmptyState
                heading="No custom fields yet"
                action={{
                  content: 'Add your first field',
                  onAction: () => console.log('Add field'),
                }}
                secondaryAction={{
                  content: 'Use a template',
                  onAction: () => setShowTemplateModal(true),
                }}
                image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
              >
                <p>Create custom fields to track additional product information.</p>
              </EmptyState>
            ) : (
              <ResourceList
                resourceName={{ singular: 'field', plural: 'fields' }}
                items={fields}
                renderItem={renderFieldItem}
                selectedItems={selectedFields}
                onSelectionChange={setSelectedFields}
              />
            )}
          </Card>
        )}

        {selectedTab === 1 && (
          <Card title="Field Templates" sectioned>
            <TextContainer>
              <Text>Quick-start templates for common product categories</Text>
            </TextContainer>
            <div style={{ marginTop: '16px' }}>
              <ResourceList
                resourceName={{ singular: 'template', plural: 'templates' }}
                items={templates}
                renderItem={(template) => (
                  <ResourceItem
                    id={template.id}
                    accessibilityLabel={`Apply ${template.name} template`}
                    onClick={() => applyTemplate(template.id)}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <Text variant="bodyMd" fontWeight="semibold">{template.name}</Text>
                        <Text variant="bodySm" color="subdued">{template.description}</Text>
                      </div>
                      <ButtonGroup>
                        <Badge>{template.category}</Badge>
                        <Badge status="info">{template.field_count} fields</Badge>
                        <Button primary>Apply</Button>
                      </ButtonGroup>
                    </div>
                  </ResourceItem>
                )}
              />
            </div>
          </Card>
        )}

        {selectedTab === 2 && renderAnalytics()}
      </Tabs>

      {templateModal}
    </Page>
  );
};

export default CustomFieldsEnhancedSimple;
