import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Layout,
  Page,
  FormLayout,
  TextField,
  Select,
  Button,
  Stack,
  Badge,
  Banner,
  Spinner,
  Toast,
  Modal,
  TextContainer,
  Checkbox,
  DatePicker,
  Popover,
  Icon
} from '@shopify/polaris';
import {
  CalendarMinor,
  InfoMinor
} from '@shopify/polaris-icons';
import { useSearchParams } from 'react-router-dom';
import { api } from '../utils/api';

/**
 * ProductMetafields Component
 * This component is designed to be embedded in the Shopify admin product page
 * It provides a seamless experience for managing custom fields
 */
export default function ProductMetafields({ shop, productId }) {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [definitions, setDefinitions] = useState([]);
  const [values, setValues] = useState({});
  const [showTemplates, setShowTemplates] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [toastActive, setToastActive] = useState(false);
  const [toastContent, setToastContent] = useState('');
  const [datePickerActive, setDatePickerActive] = useState({});
  
  // Get product ID from URL params if not provided
  const currentProductId = productId || searchParams.get('id') || searchParams.get('product_id');
  const currentShop = shop || searchParams.get('shop') || localStorage.getItem('shopify_shop_domain');

  // Fetch field definitions and values
  useEffect(() => {
    if (currentShop && currentProductId) {
      fetchData();
    }
  }, [currentShop, currentProductId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch field definitions
      const defsResponse = await api.get(`/api/metafields/definitions?shop=${currentShop}`);
      setDefinitions(defsResponse.data.definitions || []);
      
      // Fetch current values for this product
      const valuesResponse = await api.get(`/api/metafields/values/${currentProductId}?shop=${currentShop}`);
      setValues(valuesResponse.data.values || {});
      
      // Fetch available templates
      const templatesResponse = await api.get('/api/metafields/templates');
      setTemplates(templatesResponse.data.templates || []);
      
    } catch (error) {
      console.error('Error fetching data:', error);
      showToast('Error loading custom fields');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (content) => {
    setToastContent(content);
    setToastActive(true);
  };

  const handleValueChange = (fieldKey, value) => {
    setValues(prev => ({
      ...prev,
      [fieldKey]: {
        ...prev[fieldKey],
        value
      }
    }));
  };

  const saveValues = async () => {
    try {
      setSaving(true);
      
      // Save each value
      for (const definition of definitions) {
        if (values[definition.key]) {
          await api.post(`/api/metafields/values?shop=${currentShop}`, {
            resource_id: currentProductId,
            resource_type: 'product',
            definition_id: definition.id,
            value: values[definition.key].value
          });
        }
      }
      
      showToast('Custom fields saved successfully!');
      
      // Optionally trigger Shopify to refresh the product page
      if (window.ShopifyApp) {
        window.ShopifyApp.Bar.loadingOff();
      }
      
    } catch (error) {
      console.error('Error saving values:', error);
      showToast('Error saving custom fields');
    } finally {
      setSaving(false);
    }
  };

  const applyTemplate = async (templateId) => {
    try {
      setLoading(true);
      await api.post(`/api/metafields/templates/${templateId}/apply?shop=${currentShop}`);
      await fetchData();
      setShowTemplates(false);
      showToast('Template applied successfully!');
    } catch (error) {
      console.error('Error applying template:', error);
      showToast('Error applying template');
    } finally {
      setLoading(false);
    }
  };

  const renderField = (definition) => {
    const value = values[definition.key]?.value || '';
    
    switch (definition.type) {
      case 'single_line_text_field':
      case 'text':
        return (
          <TextField
            label={definition.name}
            value={value}
            onChange={(newValue) => handleValueChange(definition.key, newValue)}
            helpText={definition.description}
          />
        );
        
      case 'multi_line_text_field':
      case 'multiline':
        return (
          <TextField
            label={definition.name}
            value={value}
            onChange={(newValue) => handleValueChange(definition.key, newValue)}
            multiline={4}
            helpText={definition.description}
          />
        );
        
      case 'number_integer':
      case 'integer':
        return (
          <TextField
            label={definition.name}
            type="number"
            value={value}
            onChange={(newValue) => handleValueChange(definition.key, parseInt(newValue) || 0)}
            helpText={definition.description}
          />
        );
        
      case 'number_decimal':
      case 'number':
        return (
          <TextField
            label={definition.name}
            type="number"
            step="0.01"
            value={value}
            onChange={(newValue) => handleValueChange(definition.key, parseFloat(newValue) || 0)}
            helpText={definition.description}
          />
        );
        
      case 'boolean':
        return (
          <Checkbox
            label={definition.name}
            checked={value === true}
            onChange={(newValue) => handleValueChange(definition.key, newValue)}
            helpText={definition.description}
          />
        );
        
      case 'date':
        const dateValue = value ? new Date(value) : new Date();
        return (
          <div>
            <label>{definition.name}</label>
            <Popover
              active={datePickerActive[definition.key] || false}
              activator={
                <TextField
                  prefix={<Icon source={CalendarMinor} />}
                  value={value ? new Date(value).toLocaleDateString() : ''}
                  onFocus={() => setDatePickerActive(prev => ({ ...prev, [definition.key]: true }))}
                  placeholder="Select date"
                  helpText={definition.description}
                />
              }
              onClose={() => setDatePickerActive(prev => ({ ...prev, [definition.key]: false }))}
            >
              <DatePicker
                month={dateValue.getMonth()}
                year={dateValue.getFullYear()}
                selected={dateValue}
                onMonthChange={(month, year) => {
                  const newDate = new Date(year, month, dateValue.getDate());
                  handleValueChange(definition.key, newDate.toISOString());
                }}
                onChange={(date) => {
                  handleValueChange(definition.key, date.start.toISOString());
                  setDatePickerActive(prev => ({ ...prev, [definition.key]: false }));
                }}
              />
            </Popover>
          </div>
        );
        
      default:
        return (
          <TextField
            label={definition.name}
            value={value}
            onChange={(newValue) => handleValueChange(definition.key, newValue)}
            helpText={definition.description}
          />
        );
    }
  };

  if (loading) {
    return (
      <Card>
        <Card.Section>
          <Stack vertical spacing="loose">
            <Spinner size="small" />
            <p>Loading custom fields...</p>
          </Stack>
        </Card.Section>
      </Card>
    );
  }

  if (!currentProductId) {
    return (
      <Banner status="warning">
        <p>Please select a product to manage custom fields.</p>
      </Banner>
    );
  }

  return (
    <>
      <Card>
        <Card.Section>
          <Stack vertical spacing="loose">
            <Stack distribution="equalSpacing" alignment="center">
              <Stack.Item>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 600 }}>Custom Fields</h2>
              </Stack.Item>
              <Stack.Item>
                <Badge status="success">Save $1,971/month vs Plus</Badge>
              </Stack.Item>
            </Stack>
            
            {definitions.length === 0 ? (
              <Banner
                title="No custom fields defined yet"
                status="info"
                action={{
                  content: 'Apply Template',
                  onAction: () => setShowTemplates(true)
                }}
              >
                <p>Start by applying an industry template or create custom fields.</p>
              </Banner>
            ) : (
              <FormLayout>
                {definitions.map((definition) => (
                  <FormLayout.Group key={definition.id}>
                    {renderField(definition)}
                  </FormLayout.Group>
                ))}
              </FormLayout>
            )}
            
            <Stack distribution="trailing">
              {definitions.length > 0 && (
                <Button onClick={() => setShowTemplates(true)}>
                  Add More Fields
                </Button>
              )}
              <Button
                primary
                loading={saving}
                disabled={definitions.length === 0}
                onClick={saveValues}
              >
                Save Custom Fields
              </Button>
            </Stack>
          </Stack>
        </Card.Section>
      </Card>

      <Modal
        open={showTemplates}
        onClose={() => setShowTemplates(false)}
        title="Apply Industry Template"
        primaryAction={{
          content: 'Close',
          onAction: () => setShowTemplates(false),
        }}
      >
        <Modal.Section>
          <Stack vertical spacing="loose">
            <TextContainer>
              <p>Quick-start templates for common industries. Select one to instantly add relevant custom fields.</p>
            </TextContainer>
            
            {templates.map((template) => (
              <Card key={template.id} sectioned>
                <Stack vertical spacing="tight">
                  <Stack distribution="equalSpacing" alignment="center">
                    <h3 style={{ fontWeight: 600 }}>{template.name}</h3>
                    <Button size="slim" onClick={() => applyTemplate(template.id)}>
                      Apply
                    </Button>
                  </Stack>
                  <p style={{ fontSize: '0.9rem', color: '#637381' }}>
                    {template.field_count} fields
                  </p>
                  <Stack vertical spacing="extraTight">
                    {template.fields.slice(0, 3).map((field, idx) => (
                      <Badge key={idx} size="small" status="info">
                        {field.name}
                      </Badge>
                    ))}
                    {template.fields.length > 3 && (
                      <span style={{ fontSize: '0.85rem', color: '#637381' }}>
                        +{template.fields.length - 3} more
                      </span>
                    )}
                  </Stack>
                </Stack>
              </Card>
            ))}
          </Stack>
        </Modal.Section>
      </Modal>

      {toastActive && (
        <Toast content={toastContent} onDismiss={() => setToastActive(false)} />
      )}
    </>
  );
}
