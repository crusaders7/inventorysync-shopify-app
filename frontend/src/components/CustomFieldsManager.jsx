import React, { useState, useEffect } from 'react';
import { Badge, Banner, BlockStack, Button, ButtonGroup, Card, Checkbox, Collapsible, DataTable, EmptyState, Form, FormLayout, InlineStack, Layout, Modal, Page, Select, Spinner, Tabs, Text, TextField, Toast } from '@shopify/polaris';

const CustomFieldsManager = ({ shop, showToast }) => {
  // Use provided shop or fallback to localStorage/default
  const shopDomain = shop || 
    localStorage.getItem('shopDomain') || 
    localStorage.getItem('shopify_shop_domain') ||
    'inventorysync-dev.myshopify.com';
    
  const [fieldDefinitions, setFieldDefinitions] = useState({});
  const [loading, setLoading] = useState(true);
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);
  const [selectedTab, setSelectedTab] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newField, setNewField] = useState({
    field_name: '',
    display_name: '',
    field_type: 'text',
    target_entity: 'product',
    is_required: false,
    is_searchable: true,
    is_filterable: true,
    help_text: '',
    field_group: 'basic',
    validation_rules: {}
  });
  const [selectedEntityType, setSelectedEntityType] = useState('product');
  const [showTemplates, setShowTemplates] = useState(false);
  const [industryTemplates, setIndustryTemplates] = useState({});

  const entityTypes = [
    { label: 'Products', value: 'product' },
    { label: 'Product Variants', value: 'variant' }, 
    { label: 'Inventory Items', value: 'inventory_item' },
    { label: 'Suppliers', value: 'supplier' },
    { label: 'Locations', value: 'location' }
  ];

  const fieldTypes = [
    { label: 'Text', value: 'text' },
    { label: 'Number', value: 'number' },
    { label: 'Date', value: 'date' },
    { label: 'Yes/No', value: 'boolean' },
    { label: 'Dropdown (Single)', value: 'select' },
    { label: 'Dropdown (Multiple)', value: 'multi_select' },
    { label: 'Email', value: 'email' },
    { label: 'URL', value: 'url' },
    { label: 'Long Text', value: 'textarea' },
    { label: 'Currency', value: 'currency' },
    { label: 'Percentage', value: 'percentage' }
  ];

  const fieldGroups = [
    { label: 'Basic Information', value: 'basic' },
    { label: 'Advanced Details', value: 'advanced' },
    { label: 'Cultural/Regional', value: 'cultural' },
    { label: 'Compliance', value: 'compliance' },
    { label: 'Marketing', value: 'marketing' }
  ];

  useEffect(() => {
    if (shopDomain) {
      fetchFieldDefinitions();
      fetchIndustryTemplates();
    }
  }, [shopDomain]);

  const fetchFieldDefinitions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/custom-fields/${shopDomain}`);
      const data = await response.json();
      
      // Group fields by entity type
      const groupedFields = {};
      if (data.fields) {
        data.fields.forEach(field => {
          const category = field.category || 'product';
          if (!groupedFields[category]) {
            groupedFields[category] = [];
          }
          groupedFields[category].push(field);
        });
      }
      
      setFieldDefinitions(groupedFields);
      setInitialLoadComplete(true);
    } catch (error) {
      console.error('Failed to fetch field definitions:', error);
      showToast('Failed to load custom fields', true);
    } finally {
      setLoading(false);
    }
  };

  const fetchIndustryTemplates = async () => {
    try {
      const response = await fetch('/api/custom-fields/templates');
      const data = await response.json();
      setIndustryTemplates(data.templates || {});
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const handleCreateField = async () => {
    try {
      const response = await fetch(`/api/custom-fields/${shopDomain}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newField)
      });

      if (response.ok) {
        showToast('Custom field created successfully!');
        setShowCreateModal(false);
        setNewField({
          field_name: '',
          display_name: '',
          field_type: 'text',
          target_entity: 'product',
          is_required: false,
          is_searchable: true,
          is_filterable: true,
          help_text: '',
          field_group: 'basic',
          validation_rules: {}
        });
        fetchFieldDefinitions();
      } else {
        const error = await response.json();
        showToast(error.detail || 'Failed to create field', true);
      }
    } catch (error) {
      console.error('Failed to create field:', error);
      showToast('Failed to create field', true);
    }
  };

  const applyTemplate = async (templateName) => {
    try {
      const response = await fetch(`/api/custom-fields/templates/${templateName}/apply/${shopDomain}`, {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        showToast(data.message);
        fetchFieldDefinitions();
        setShowTemplates(false);
      } else {
        const error = await response.json();
        showToast(error.detail || 'Failed to apply template', true);
      }
    } catch (error) {
      console.error('Failed to apply template:', error);
      showToast('Failed to apply template', true);
    }
  };

  const renderFieldDefinitionTable = (entityType) => {
    const fields = fieldDefinitions[entityType] || [];
    
    if (fields.length === 0) {
      return (
        <EmptyState
          heading={`No custom fields for ${entityType}s yet`}
          action={{
            content: 'Create your first field',
            onAction: () => {
              setNewField({ ...newField, target_entity: entityType });
              setShowCreateModal(true);
            }
          }}
          image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
        >
          <p>Custom fields let you store additional information specific to your business needs.</p>
        </EmptyState>
      );
    }

    const rows = fields.map(field => [
      <BlockStack gap="200">
        <Text variant="bodyMd" fontWeight="semibold">{field.display_name}</Text>
        <Text variant="bodySm" color="subdued">{field.field_name}</Text>
      </BlockStack>,
      <Badge status={getFieldTypeBadgeStatus(field.field_type)}>
        {fieldTypes.find(t => t.value === field.field_type)?.label || field.field_type}
      </Badge>,
      field.field_group || 'Basic',
      <InlineStack gap="200">
        {field.is_required && <Badge status="attention">Required</Badge>}
        {field.is_searchable && <Badge>Searchable</Badge>}
        {field.is_filterable && <Badge>Filterable</Badge>}
      </InlineStack>,
      <ButtonGroup>
        <Button size="slim" outline>Edit</Button>
        <Button size="slim" destructive outline>Delete</Button>
      </ButtonGroup>
    ]);

    return (
      <DataTable
        columnContentTypes={['text', 'text', 'text', 'text', 'text']}
        headings={['Field Name', 'Type', 'Group', 'Properties', 'Actions']}
        rows={rows}
      />
    );
  };

  const getFieldTypeBadgeStatus = (type) => {
    const statusMap = {
      text: 'info',
      number: 'success',
      date: 'warning',
      boolean: 'critical',
      select: 'attention',
      multi_select: 'attention'
    };
    return statusMap[type] || 'info';
  };

  const renderValidationRulesInput = () => {
    const { field_type } = newField;
    
    if (field_type === 'select' || field_type === 'multi_select') {
      return (
        <TextField
          label="Options (one per line)"
          value={newField.validation_rules.options?.join('\n') || ''}
          onChange={(value) => {
            const options = value.split('\n').filter(opt => opt.trim());
            setNewField({
              ...newField,
              validation_rules: { ...newField.validation_rules, options }
            });
          }}
          multiline={4}
          helpText="Enter each option on a new line"
        />
      );
    }
    
    if (field_type === 'number') {
      return (
        <FormLayout.Group>
          <TextField
            label="Minimum Value"
            type="number"
            value={newField.validation_rules.min?.toString() || ''}
            onChange={(value) => {
              setNewField({
                ...newField,
                validation_rules: {
                  ...newField.validation_rules,
                  min: value ? parseFloat(value) : undefined
                }
              });
            }}
          />
          <TextField
            label="Maximum Value"
            type="number"
            value={newField.validation_rules.max?.toString() || ''}
            onChange={(value) => {
              setNewField({
                ...newField,
                validation_rules: {
                  ...newField.validation_rules,
                  max: value ? parseFloat(value) : undefined
                }
              });
            }}
          />
        </FormLayout.Group>
      );
    }
    
    if (field_type === 'text' || field_type === 'textarea') {
      return (
        <TextField
          label="Maximum Length"
          type="number"
          value={newField.validation_rules.max_length?.toString() || ''}
          onChange={(value) => {
            setNewField({
              ...newField,
              validation_rules: {
                ...newField.validation_rules,
                max_length: value ? parseInt(value) : undefined
              }
            });
          }}
          helpText="Leave empty for no limit"
        />
      );
    }
    
    return null;
  };

  const tabs = entityTypes.map((entity, index) => ({
    id: entity.value,
    content: `${entity.label} (${fieldDefinitions[entity.value]?.length || 0})`,
    panelID: `${entity.value}-panel`
  }));

  const createModal = (
    <Modal
      open={showCreateModal}
      onClose={() => setShowCreateModal(false)}
      title="Create Custom Field"
      primaryAction={{
        content: 'Create Field',
        onAction: handleCreateField,
        disabled: !newField.field_name || !newField.display_name
      }}
      secondaryActions={[{
        content: 'Cancel',
        onAction: () => setShowCreateModal(false)
      }]}
      large
    >
      <Modal.Section>
        <Form>
          <FormLayout>
            <FormLayout.Group>
              <TextField
                label="Field Name"
                value={newField.field_name}
                onChange={(value) => setNewField({ ...newField, field_name: value })}
                helpText="Internal name (lowercase, no spaces). Cannot be changed later."
                placeholder="e.g., season, material, supplier_rating"
              />
              <TextField
                label="Display Name"
                value={newField.display_name}
                onChange={(value) => setNewField({ ...newField, display_name: value })}
                helpText="User-friendly name shown in forms"
                placeholder="e.g., Season, Material Type, Supplier Rating"
              />
            </FormLayout.Group>

            <FormLayout.Group>
              <Select
                label="Field Type"
                options={fieldTypes}
                value={newField.field_type}
                onChange={(value) => setNewField({ ...newField, field_type: value })}
              />
              <Select
                label="Apply To"
                options={entityTypes}
                value={newField.target_entity}
                onChange={(value) => setNewField({ ...newField, target_entity: value })}
              />
            </FormLayout.Group>

            <Select
              label="Field Group"
              options={fieldGroups}
              value={newField.field_group}
              onChange={(value) => setNewField({ ...newField, field_group: value })}
            />

            {renderValidationRulesInput()}

            <TextField
              label="Help Text"
              value={newField.help_text}
              onChange={(value) => setNewField({ ...newField, help_text: value })}
              helpText="Optional guidance for users filling out this field"
              placeholder="e.g., Select the primary season this product is intended for"
            />

            <FormLayout.Group>
              <Checkbox
                label="Required Field"
                checked={newField.is_required}
                onChange={(checked) => setNewField({ ...newField, is_required: checked })}
              />
              <Checkbox
                label="Searchable"
                checked={newField.is_searchable}
                onChange={(checked) => setNewField({ ...newField, is_searchable: checked })}
              />
              <Checkbox
                label="Filterable"
                checked={newField.is_filterable}
                onChange={(checked) => setNewField({ ...newField, is_filterable: checked })}
              />
            </FormLayout.Group>
          </FormLayout>
        </Form>
      </Modal.Section>
    </Modal>
  );

  const templatesModal = (
    <Modal
      open={showTemplates}
      onClose={() => setShowTemplates(false)}
      title="Industry Templates"
      large
    >
      <Modal.Section>
        <BlockStack gap="loose">
          <Text variant="bodyMd">
            Quick-start templates create common custom fields for your industry.
          </Text>
          
          {Object.entries(industryTemplates).map(([key, template]) => (
            <Card key={key} sectioned>
              <InlineStack align="space-between" wrap={false}>
                <BlockStack gap="tight">
                  <Text variant="headingMd">{template?.name || 'Unnamed Template'}</Text>
                  <Text variant="bodyMd" color="subdued">{template?.description || 'No description available'}</Text>
                  <Text variant="bodySm">
                    Includes {template.fields?.length || 0} custom fields
                  </Text>
                </BlockStack>
                <Button primary onClick={() => applyTemplate(key)}>
                  Apply Template
                </Button>
              </InlineStack>
              
              <Collapsible
                open={false}
                id={`template-${key}`}
                transition={{duration: '200ms', timingFunction: 'ease-in-out'}}
              >
                <div style={{ marginTop: '1rem' }}>
                  <Text variant="headingXs">Fields included:</Text>
                  <ul style={{ marginTop: '0.5rem' }}>
                    {(template.fields || []).map((field, index) => (
                      <li key={index}>
                        <strong>{field.display_name}</strong> ({field.field_type}) - {field.target_entity}
                      </li>
                    ))}
                  </ul>
                </div>
              </Collapsible>
            </Card>
          ))}
        </BlockStack>
      </Modal.Section>
    </Modal>
  );

  if (loading && !initialLoadComplete) {
    return (
      <Page title="Custom Fields">
        <Layout>
          <Layout.Section>
            <Card sectioned>
              <BlockStack gap="400" align="center">
                <Spinner size="large" />
                <Text variant="bodyMd">Loading custom fields...</Text>
              </BlockStack>
            </Card>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  return (
    <Page
      title="Custom Fields"
      subtitle="Create flexible fields for any industry - your competitive advantage"
      primaryAction={{
        content: 'Create Field',
        onAction: () => setShowCreateModal(true)
      }}
      secondaryActions={[
        {
          content: 'Industry Templates',
          onAction: () => setShowTemplates(true)
        }
      ]}
    >
      <Layout>
        <Layout.Section>
          <Banner
            title="Unlimited Customization"
            status="success"
          >
            <Text variant="bodyMd">
              Create custom fields for products, variants, inventory, suppliers, and locations. 
              Perfect for cultural differences, niche categories, and compliance requirements.
            </Text>
          </Banner>
        </Layout.Section>

        <Layout.Section>
          <Card>
            <Tabs
              tabs={tabs}
              selected={selectedTab}
              onSelect={setSelectedTab}
            >
              <div style={{ padding: '1rem' }}>
                {renderFieldDefinitionTable(entityTypes[selectedTab].value)}
              </div>
            </Tabs>
          </Card>
        </Layout.Section>

        <Layout.Section secondary>
          <Card title="Getting Started" sectioned>
            <BlockStack gap="400">
              <Text variant="bodyMd">
                <strong>Why Custom Fields?</strong>
              </Text>
              <ul>
                <li>Store industry-specific data (size, color, material, etc.)</li>
                <li>Track cultural or regional requirements</li>
                <li>Manage compliance information</li>
                <li>Create filters and reports on any data</li>
              </ul>
              
              <Text variant="bodyMd">
                <strong>Field Types Available:</strong>
              </Text>
              <ul>
                <li><strong>Text</strong> - Names, descriptions, codes</li>
                <li><strong>Number</strong> - Measurements, quantities, ratings</li>
                <li><strong>Date</strong> - Expiry dates, seasons, events</li>
                <li><strong>Dropdown</strong> - Categories, status, options</li>
                <li><strong>Yes/No</strong> - Flags, certifications</li>
              </ul>
            </BlockStack>
          </Card>

          <Card title="Pro Tips" sectioned>
            <BlockStack gap="200">
              <ul>
                <li>Use field groups to organize related information</li>
                <li>Make fields searchable for quick filtering</li>
                <li>Start with industry templates for common setups</li>
                <li>Custom fields work across all inventory tools</li>
              </ul>
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>

      {createModal}
      {templatesModal}
    </Page>
  );
};

export default CustomFieldsManager;
