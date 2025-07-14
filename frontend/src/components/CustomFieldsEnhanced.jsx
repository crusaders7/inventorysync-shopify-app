import React, { useState, useEffect, useCallback } from 'react';
import {
  Page,
  Layout,
  Card,
  Button,
  DataTable,
  TextField,
  Select,
  Badge,
  Text,
  Banner,
  Modal,
  LegacyStack,
  RadioButton,
  Checkbox,
  Icon,
  Tabs,
  EmptyState,
  SkeletonBodyText,
  Filters,
  ChoiceList,
  ResourceList,
  ResourceItem,
  Avatar,
  TextStyle,
  ButtonGroup,
  Tooltip,
  InlineError,
  FormLayout,
  TextContainer,
} from '@shopify/polaris';
import {
  SearchMinor,
  FilterMinor,
  ImportMinor,
  ExportMinor,
  CirclePlusMinor,
  DuplicateMinor,
  DeleteMinor,
  AnalyticsMinor,
} from '@shopify/polaris-icons';

const CustomFieldsEnhanced = () => {
  // State management
  const [fields, setFields] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedTab, setSelectedTab] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [activeFilter, setActiveFilter] = useState(null);
  const [selectedFields, setSelectedFields] = useState([]);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});

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
      if (activeFilter !== null) params.append('is_active', activeFilter);

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
  }, [shopDomain, searchTerm, selectedType, activeFilter]);

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

  // Bulk operations
  const handleBulkOperation = async (operation) => {
    setSaving(true);
    try {
      const payload = {
        operation,
        field_ids: selectedFields,
      };

      if (operation === 'update') {
        payload.update_data = {
          is_active: true, // Example update
        };
      }

      const response = await fetch(`/api/custom-fields/bulk?shop_domain=${shopDomain}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || 'dev-token'}`,
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Bulk operation result:', result);
        fetchFields();
        setSelectedFields([]);
        setShowBulkModal(false);
      }
    } catch (error) {
      console.error('Bulk operation error:', error);
    } finally {
      setSaving(false);
    }
  };

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

  // Validate field value
  const validateFieldValue = async (fieldId, value) => {
    try {
      const response = await fetch(
        `/api/custom-fields/validate/${shopDomain}/${fieldId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token') || 'dev-token'}`,
          },
          body: JSON.stringify({ value }),
        }
      );

      if (response.ok) {
        const result = await response.json();
        if (!result.is_valid) {
          setValidationErrors({
            ...validationErrors,
            [fieldId]: result.errors,
          });
        } else {
          const newErrors = { ...validationErrors };
          delete newErrors[fieldId];
          setValidationErrors(newErrors);
        }
      }
    } catch (error) {
      console.error('Validation error:', error);
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

  // Filter options
  const filterOptions = [
    {
      label: 'Status',
      value: 'status',
      choices: [
        { label: 'Active', value: 'true' },
        { label: 'Inactive', value: 'false' },
      ],
    },
    {
      label: 'Type',
      value: 'type',
      choices: fieldTypes,
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
        media={
          <Avatar
            size="medium"
            name={name}
            source={field_type === 'text' ? '📝' : field_type === 'number' ? '🔢' : '📋'}
          />
        }
        onClick={() => console.log('Edit field:', id)}
      >
        <LegacyStack vertical spacing="tight">
          <LegacyStack alignment="center">
            <LegacyLegacyStack.Item fill>
              <TextStyle variation="strong">{label}</TextStyle>
            </LegacyStack.Item>
            <LegacyLegacyStack.Item>
              <Badge status={is_active ? 'success' : 'default'}>
                {is_active ? 'Active' : 'Inactive'}
              </Badge>
            </LegacyStack.Item>
            <LegacyLegacyStack.Item>
              <Badge>{field_type}</Badge>
            </LegacyStack.Item>
          </LegacyStack>
          {description && (
            <TextStyle variation="subdued">{description}</TextStyle>
          )}
        </LegacyStack>
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
        <LegacyStack vertical>
          {templates.map((template) => (
            <Card
              key={template.id}
              sectioned
              onClick={() => applyTemplate(template.id)}
            >
              <LegacyStack vertical spacing="tight">
                <TextStyle variation="strong">{template.name}</TextStyle>
                <TextStyle variation="subdued">{template.description}</TextStyle>
                <LegacyStack>
                  <Badge>{template.category}</Badge>
                  <Badge status="info">{template.field_count} fields</Badge>
                </LegacyStack>
              </LegacyStack>
            </Card>
          ))}
        </LegacyStack>
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
            <LegacyStack vertical>
              <LegacyStack distribution="equalSpacing">
                <TextStyle>Total Fields</TextStyle>
                <Text variant="headingLg" as="p">{statistics.total_fields}</Text>
              </LegacyStack>
              <LegacyStack distribution="equalSpacing">
                <TextStyle>Active Fields</TextStyle>
                <Text variant="headingLg" as="p">
                  <TextStyle variation="positive">{statistics.active_fields}</TextStyle>
                </Text>
              </LegacyStack>
              <LegacyStack distribution="equalSpacing">
                <TextStyle>Usage Rate</TextStyle>
                <Badge status="success">{statistics.usage_percentage.toFixed(1)}%</Badge>
              </LegacyStack>
            </LegacyStack>
          </Card>
        </Layout.Section>

        <Layout.Section oneThird>
          <Card title="Fields by Type" sectioned>
            <LegacyStack vertical>
              {Object.entries(statistics.fields_by_type || {}).map(([type, count]) => (
                <LegacyStack key={type} distribution="equalSpacing">
                  <Badge>{type}</Badge>
                  <TextStyle>{count}</TextStyle>
                </LegacyStack>
              ))}
            </LegacyStack>
          </Card>
        </Layout.Section>

        <Layout.Section oneThird>
          <Card title="Quick Actions" sectioned>
            <LegacyStack vertical>
              <Button fullWidth onClick={() => setShowTemplateModal(true)}>
                Apply Template
              </Button>
              <Button fullWidth plain>
                Export Configuration
              </Button>
              <Button fullWidth plain>
                Import Configuration
              </Button>
            </LegacyStack>
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
      {selectedFields.length > 0 && (
        <Banner
          title={`${selectedFields.length} fields selected`}
          action={{
            content: 'Clear selection',
            onAction: () => setSelectedFields([]),
          }}
          secondaryAction={{
            content: 'Bulk actions',
            onAction: () => setShowBulkModal(true),
          }}
          status="info"
        />
      )}

      <Tabs tabs={tabs} selected={selectedTab} onSelect={setSelectedTab}>
        {selectedTab === 0 && (
          <Card>
            <Card.Section>
              <LegacyStack>
                <LegacyLegacyStack.Item fill>
                  <TextField
                    value={searchTerm}
                    onChange={setSearchTerm}
                    placeholder="Search fields..."
                    prefix={<Icon source={SearchMinor} />}
                    clearButton
                    onClearButtonClick={() => setSearchTerm('')}
                  />
                </LegacyStack.Item>
                <Select
                  label="Type"
                  labelHidden
                  options={[{ label: 'All types', value: '' }, ...fieldTypes]}
                  value={selectedType}
                  onChange={setSelectedType}
                />
                <ButtonGroup>
                  <Button
                    icon={CirclePlusMinor}
                    onClick={() => setShowTemplateModal(true)}
                  >
                    Templates
                  </Button>
                  <Button
                    icon={FilterMinor}
                    disclosure
                    onClick={() => console.log('Show filters')}
                  >
                    Filters
                  </Button>
                </ButtonGroup>
              </LegacyStack>
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
                bulkActions={[
                  {
                    content: 'Activate',
                    onAction: () => handleBulkOperation('update'),
                  },
                  {
                    content: 'Deactivate',
                    onAction: () => handleBulkOperation('update'),
                  },
                  {
                    content: 'Delete',
                    destructive: true,
                    onAction: () => handleBulkOperation('delete'),
                  },
                ]}
                sortValue="name"
                sortOptions={[
                  { label: 'Name', value: 'name' },
                  { label: 'Type', value: 'type' },
                  { label: 'Created', value: 'created' },
                ]}
              />
            )}
          </Card>
        )}

        {selectedTab === 1 && (
          <Card title="Field Templates" sectioned>
            <LegacyStack vertical>
              <TextStyle>
                Quick-start templates for common product categories
              </TextStyle>
              <ResourceList
                resourceName={{ singular: 'template', plural: 'templates' }}
                items={templates}
                renderItem={(template) => (
                  <ResourceItem
                    id={template.id}
                    accessibilityLabel={`Apply ${template.name} template`}
                    onClick={() => applyTemplate(template.id)}
                  >
                    <LegacyStack>
                      <LegacyLegacyStack.Item fill>
                        <LegacyStack vertical spacing="tight">
                          <TextStyle variation="strong">{template.name}</TextStyle>
                          <TextStyle variation="subdued">{template.description}</TextStyle>
                        </LegacyStack>
                      </LegacyStack.Item>
                      <LegacyLegacyStack.Item>
                        <ButtonGroup>
                          <Badge>{template.category}</Badge>
                          <Badge status="info">{template.field_count} fields</Badge>
                          <Button plain>Preview</Button>
                          <Button primary>Apply</Button>
                        </ButtonGroup>
                      </LegacyStack.Item>
                    </LegacyStack>
                  </ResourceItem>
                )}
              />
            </LegacyStack>
          </Card>
        )}

        {selectedTab === 2 && renderAnalytics()}
      </Tabs>

      {templateModal}
    </Page>
  );
};

export default CustomFieldsEnhanced;
