import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Card,
  FormLayout,
  TextField,
  Select,
  Button,
  Stack,
  Badge,
  InlineError,
  Spinner,
  Banner,
  Checkbox,
  Icon,
  Tooltip,
  TextContainer,
  Heading,
  ButtonGroup
} from '@shopify/polaris';
import {
  SaveIcon,
  DeleteIcon,
  DuplicateIcon,
  ImportIcon,
  ExportIcon,
  CircleTickIcon,
  AlertTriangleIcon
} from '@shopify/polaris-icons';
import { useAuthenticatedFetch } from '../hooks/useAuthenticatedFetch';
import debounce from 'lodash.debounce';

const FIELD_TYPES = [
  { label: 'Single Line Text', value: 'single_line_text_field' },
  { label: 'Multi-line Text', value: 'multi_line_text_field' },
  { label: 'Number (Integer)', value: 'number_integer' },
  { label: 'Number (Decimal)', value: 'number_decimal' },
  { label: 'Boolean', value: 'boolean' },
  { label: 'Color', value: 'color' },
  { label: 'Date', value: 'date' },
  { label: 'Date and Time', value: 'date_time' },
  { label: 'URL', value: 'url' },
  { label: 'JSON', value: 'json' },
  { label: 'Product Reference', value: 'product_reference' },
  { label: 'File Reference', value: 'file_reference' },
  { label: 'Dimension', value: 'dimension' },
  { label: 'Volume', value: 'volume' },
  { label: 'Weight', value: 'weight' },
  { label: 'Rating', value: 'rating' }
];

const ProductMetafieldsEnhanced = ({ productId, productType, productVendor, productTags }) => {
  const fetch = useAuthenticatedFetch();
  const [metafields, setMetafields] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState({});
  const [errors, setErrors] = useState({});
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const autoSaveTimers = useRef({});

  // Load metafields and templates
  useEffect(() => {
    loadMetafields();
    loadTemplates();
  }, [productId]);

  const loadMetafields = async () => {
    try {
      const response = await fetch(`/api/v1/metafields/product/${productId}`);
      const data = await response.json();
      setMetafields(data.metafields || []);
    } catch (error) {
      console.error('Error loading metafields:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/v1/metafields/templates');
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  // Auto-save functionality
  const autoSaveField = useCallback(
    debounce(async (fieldId, updates) => {
      setSaving(prev => ({ ...prev, [fieldId]: true }));
      
      try {
        const response = await fetch(`/api/v1/metafields/${fieldId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates)
        });

        if (response.ok) {
          setSaving(prev => ({ ...prev, [fieldId]: false }));
          setErrors(prev => ({ ...prev, [fieldId]: null }));
          
          // Show success indicator briefly
          setTimeout(() => {
            setSaving(prev => ({ ...prev, [fieldId]: 'saved' }));
            setTimeout(() => {
              setSaving(prev => ({ ...prev, [fieldId]: false }));
            }, 2000);
          }, 100);
        } else {
          const error = await response.json();
          setErrors(prev => ({ ...prev, [fieldId]: error.message }));
          setSaving(prev => ({ ...prev, [fieldId]: false }));
        }
      } catch (error) {
        setErrors(prev => ({ ...prev, [fieldId]: 'Failed to save' }));
        setSaving(prev => ({ ...prev, [fieldId]: false }));
      }
    }, 1000),
    []
  );

  // Handle field changes with auto-save
  const handleFieldChange = (fieldId, key, value) => {
    setMetafields(prev => 
      prev.map(field => 
        field.id === fieldId ? { ...field, [key]: value } : field
      )
    );

    // Trigger auto-save
    autoSaveField(fieldId, { [key]: value });
  };

  // Add new field
  const addField = (template = null) => {
    const newField = template || {
      id: `new_${Date.now()}`,
      namespace: 'custom',
      key: '',
      value: '',
      type: 'single_line_text_field',
      description: '',
      isNew: true,
      visible: shouldShowField({})
    };

    setMetafields(prev => [...prev, newField]);
  };

  // Apply template
  const applyTemplate = async () => {
    if (!selectedTemplate) return;

    const template = templates.find(t => t.id === selectedTemplate);
    if (!template) return;

    const newFields = template.fields.map(field => ({
      ...field,
      id: `new_${Date.now()}_${Math.random()}`,
      isNew: true,
      visible: shouldShowField(field)
    }));

    setMetafields(prev => [...prev, ...newFields]);
    setSelectedTemplate('');
  };

  // Conditional field visibility
  const shouldShowField = (field) => {
    // Show field based on product attributes
    if (field.conditions) {
      const { showFor } = field.conditions;
      
      if (showFor?.productTypes && !showFor.productTypes.includes(productType)) {
        return false;
      }
      
      if (showFor?.vendors && !showFor.vendors.includes(productVendor)) {
        return false;
      }
      
      if (showFor?.tags && !showFor.tags.some(tag => productTags.includes(tag))) {
        return false;
      }
    }
    
    return true;
  };

  // Delete field
  const deleteField = async (fieldId) => {
    const field = metafields.find(f => f.id === fieldId);
    
    if (field.isNew) {
      setMetafields(prev => prev.filter(f => f.id !== fieldId));
    } else {
      setSaving(prev => ({ ...prev, [fieldId]: true }));
      
      try {
        const response = await fetch(`/api/v1/metafields/${fieldId}`, {
          method: 'DELETE'
        });

        if (response.ok) {
          setMetafields(prev => prev.filter(f => f.id !== fieldId));
        } else {
          const error = await response.json();
          setErrors(prev => ({ ...prev, [fieldId]: error.message }));
        }
      } catch (error) {
        setErrors(prev => ({ ...prev, [fieldId]: 'Failed to delete' }));
      } finally {
        setSaving(prev => ({ ...prev, [fieldId]: false }));
      }
    }
  };

  // Bulk save new fields
  const saveNewFields = async () => {
    const newFields = metafields.filter(f => f.isNew);
    if (newFields.length === 0) return;

    setSaving({ bulk: true });

    try {
      const response = await fetch('/api/v1/metafields/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: productId,
          metafields: newFields.map(({ isNew, ...field }) => field)
        })
      });

      if (response.ok) {
        setShowSuccess(true);
        setTimeout(() => setShowSuccess(false), 3000);
        await loadMetafields();
      } else {
        const error = await response.json();
        setErrors({ bulk: error.message });
      }
    } catch (error) {
      setErrors({ bulk: 'Failed to save new fields' });
    } finally {
      setSaving({ bulk: false });
    }
  };

  // Export fields
  const exportFields = () => {
    const exportData = metafields.map(({ id, isNew, ...field }) => field);
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `product-${productId}-metafields.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Render field input based on type
  const renderFieldInput = (field) => {
    const saveStatus = saving[field.id];
    const error = errors[field.id];

    switch (field.type) {
      case 'boolean':
        return (
          <Checkbox
            label="Value"
            checked={field.value === 'true'}
            onChange={(value) => handleFieldChange(field.id, 'value', value.toString())}
          />
        );

      case 'number_integer':
      case 'number_decimal':
        return (
          <TextField
            label="Value"
            type="number"
            value={field.value}
            onChange={(value) => handleFieldChange(field.id, 'value', value)}
            error={error}
            connectedRight={renderSaveIndicator(saveStatus)}
          />
        );

      case 'multi_line_text_field':
      case 'json':
        return (
          <TextField
            label="Value"
            value={field.value}
            onChange={(value) => handleFieldChange(field.id, 'value', value)}
            multiline={4}
            error={error}
            connectedRight={renderSaveIndicator(saveStatus)}
          />
        );

      case 'color':
        return (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
            <TextField
              label="Value"
              type="color"
              value={field.value || '#000000'}
              onChange={(value) => handleFieldChange(field.id, 'value', value)}
              error={error}
            />
            <div
              style={{
                width: '40px',
                height: '40px',
                backgroundColor: field.value || '#000000',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
            />
            {renderSaveIndicator(saveStatus)}
          </div>
        );

      case 'date':
        return (
          <TextField
            label="Value"
            type="date"
            value={field.value}
            onChange={(value) => handleFieldChange(field.id, 'value', value)}
            error={error}
            connectedRight={renderSaveIndicator(saveStatus)}
          />
        );

      case 'date_time':
        return (
          <TextField
            label="Value"
            type="datetime-local"
            value={field.value}
            onChange={(value) => handleFieldChange(field.id, 'value', value)}
            error={error}
            connectedRight={renderSaveIndicator(saveStatus)}
          />
        );

      case 'url':
        return (
          <TextField
            label="Value"
            type="url"
            value={field.value}
            onChange={(value) => handleFieldChange(field.id, 'value', value)}
            placeholder="https://example.com"
            error={error}
            connectedRight={renderSaveIndicator(saveStatus)}
          />
        );

      default:
        return (
          <TextField
            label="Value"
            value={field.value}
            onChange={(value) => handleFieldChange(field.id, 'value', value)}
            error={error}
            connectedRight={renderSaveIndicator(saveStatus)}
          />
        );
    }
  };

  // Render save indicator
  const renderSaveIndicator = (status) => {
    if (status === true) {
      return <Spinner size="small" />;
    }
    if (status === 'saved') {
      return (
        <Tooltip content="Saved">
          <Icon source={CircleTickIcon} color="success" />
        </Tooltip>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <Card>
        <Card.Section>
          <Stack distribution="center">
            <Spinner />
          </Stack>
        </Card.Section>
      </Card>
    );
  }

  const visibleFields = metafields.filter(field => field.visible !== false);
  const newFieldsCount = metafields.filter(f => f.isNew).length;

  return (
    <Stack vertical>
      {showSuccess && (
        <Banner status="success" onDismiss={() => setShowSuccess(false)}>
          Fields saved successfully!
        </Banner>
      )}

      {errors.bulk && (
        <Banner status="critical" onDismiss={() => setErrors(prev => ({ ...prev, bulk: null }))}>
          {errors.bulk}
        </Banner>
      )}

      <Card>
        <Card.Section>
          <Stack distribution="equalSpacing" alignment="center">
            <TextContainer>
              <Heading>Custom Fields</Heading>
              <p>Add custom fields to store additional product information</p>
            </TextContainer>
            <ButtonGroup>
              <Button icon={ExportIcon} onClick={exportFields} disabled={metafields.length === 0}>
                Export
              </Button>
              <Button icon={ImportIcon} onClick={() => addField()} primary>
                Add Field
              </Button>
            </ButtonGroup>
          </Stack>
        </Card.Section>

        {templates.length > 0 && (
          <Card.Section>
            <Stack>
              <Select
                label="Apply Template"
                placeholder="Choose a template"
                options={[
                  { label: 'Select a template', value: '' },
                  ...templates.map(t => ({ label: t.name, value: t.id }))
                ]}
                value={selectedTemplate}
                onChange={setSelectedTemplate}
              />
              <Button onClick={applyTemplate} disabled={!selectedTemplate}>
                Apply Template
              </Button>
            </Stack>
          </Card.Section>
        )}

        {visibleFields.map((field, index) => (
          <Card.Section key={field.id} subdued={field.isNew}>
            <Stack vertical spacing="tight">
              <Stack distribution="equalSpacing" alignment="center">
                <Badge status={field.isNew ? 'attention' : 'success'}>
                  {field.isNew ? 'New' : 'Saved'}
                </Badge>
                <ButtonGroup>
                  <Tooltip content="Duplicate">
                    <Button
                      icon={DuplicateIcon}
                      plain
                      onClick={() => addField({ ...field, id: `new_${Date.now()}`, isNew: true })}
                    />
                  </Tooltip>
                  <Tooltip content="Delete">
                    <Button
                      icon={DeleteIcon}
                      plain
                      destructive
                      onClick={() => deleteField(field.id)}
                      loading={saving[field.id] === true}
                    />
                  </Tooltip>
                </ButtonGroup>
              </Stack>

              <FormLayout>
                <FormLayout.Group>
                  <TextField
                    label="Namespace"
                    value={field.namespace}
                    onChange={(value) => handleFieldChange(field.id, 'namespace', value)}
                    placeholder="custom"
                    disabled={!field.isNew}
                  />
                  <TextField
                    label="Key"
                    value={field.key}
                    onChange={(value) => handleFieldChange(field.id, 'key', value)}
                    placeholder="field_name"
                    disabled={!field.isNew}
                    error={errors[field.id] && field.isNew ? 'Key is required' : null}
                  />
                </FormLayout.Group>

                <Select
                  label="Type"
                  options={FIELD_TYPES}
                  value={field.type}
                  onChange={(value) => handleFieldChange(field.id, 'type', value)}
                  disabled={!field.isNew}
                />

                {renderFieldInput(field)}

                <TextField
                  label="Description"
                  value={field.description || ''}
                  onChange={(value) => handleFieldChange(field.id, 'description', value)}
                  placeholder="Optional description"
                  connectedRight={renderSaveIndicator(saving[field.id])}
                />
              </FormLayout>
            </Stack>
          </Card.Section>
        ))}

        {metafields.length === 0 && (
          <Card.Section>
            <Stack distribution="center">
              <Stack vertical spacing="tight" alignment="center">
                <p>No custom fields yet</p>
                <Button primary onClick={() => addField()}>
                  Add Your First Field
                </Button>
              </Stack>
            </Stack>
          </Card.Section>
        )}

        {newFieldsCount > 0 && (
          <Card.Section>
            <Stack distribution="trailing">
              <Button
                primary
                loading={saving.bulk}
                onClick={saveNewFields}
              >
                Save {newFieldsCount} New Field{newFieldsCount > 1 ? 's' : ''}
              </Button>
            </Stack>
          </Card.Section>
        )}
      </Card>
    </Stack>
  );
};

export default ProductMetafieldsEnhanced;
