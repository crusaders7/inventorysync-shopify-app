import React, { useState } from 'react';
import {
  Page, Layout, Card, Button, TextField, Select, FormLayout,
  Banner, Badge, BlockStack, InlineStack, Text, Thumbnail,
  EmptyState, DataTable, Modal, ChoiceList, DatePicker
} from '@shopify/polaris';

const CustomFieldsDemo = () => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [demoFields, setDemoFields] = useState([
    { name: 'Material Type', type: 'Dropdown', value: 'Cotton' },
    { name: 'Care Instructions', type: 'Text', value: 'Machine wash cold' },
    { name: 'Season', type: 'Dropdown', value: 'Summer 2024' }
  ]);

  // This is what merchants see in their product editor
  const ProductEditorDemo = () => (
    <Card sectioned>
      <BlockStack gap="500">
        <InlineStack align="space-between">
          <Text variant="headingMd" as="h2">Product: Summer Cotton T-Shirt</Text>
          <Badge status="success">Saved</Badge>
        </InlineStack>
        
        {/* Standard Shopify Fields */}
        <FormLayout>
          <TextField label="Title" value="Summer Cotton T-Shirt" />
          <TextField label="Description" multiline value="Comfortable cotton t-shirt perfect for summer" />
        </FormLayout>

        {/* OUR CUSTOM FIELDS SECTION - This is the magic! */}
        <div style={{ 
          border: '2px solid #5c6ac4', 
          borderRadius: '8px', 
          padding: '16px',
          background: '#f4f6f8'
        }}>
          <BlockStack gap="400">
            <InlineStack align="space-between">
              <Text variant="headingMd" as="h3">
                🎯 Custom Fields <Badge status="info">by InventorySync</Badge>
              </Text>
              <Text variant="bodySm" color="success">
                Saving you $1,971/month!
              </Text>
            </InlineStack>

            <FormLayout>
              <Select
                label="Material Type"
                options={[
                  { label: 'Cotton', value: 'cotton' },
                  { label: 'Polyester', value: 'polyester' },
                  { label: 'Wool', value: 'wool' },
                  { label: 'Silk', value: 'silk' }
                ]}
                value="cotton"
              />
              
              <TextField
                label="Care Instructions"
                value="Machine wash cold, tumble dry low"
                helpText="Visible on product page"
              />
              
              <Select
                label="Season"
                options={[
                  { label: 'Spring 2024', value: 'spring24' },
                  { label: 'Summer 2024', value: 'summer24' },
                  { label: 'Fall 2024', value: 'fall24' },
                  { label: 'Winter 2024', value: 'winter24' }
                ]}
                value="summer24"
              />
              
              <TextField
                label="Supplier SKU"
                value="SUP-COTTON-234"
                helpText="For internal tracking"
              />
            </FormLayout>
          </BlockStack>
        </div>

        {/* Standard fields continue */}
        <FormLayout>
          <TextField label="Price" value="$29.99" prefix="$" />
          <TextField label="Inventory" value="150" type="number" />
        </FormLayout>
      </BlockStack>
    </Card>
  );

  // Field Creation Modal
  const CreateFieldModal = () => (
    <Modal
      open={showCreateModal}
      onClose={() => setShowCreateModal(false)}
      title="Create Custom Field"
      primaryAction={{
        content: 'Create Field',
        onAction: () => {
          setDemoFields([...demoFields, {
            name: 'New Field',
            type: 'Text',
            value: ''
          }]);
          setShowCreateModal(false);
        }
      }}
    >
      <Modal.Section>
        <FormLayout>
          <TextField
            label="Field Name"
            value="warranty_period"
            helpText="Lowercase, no spaces"
          />
          <TextField
            label="Display Name"
            value="Warranty Period"
          />
          <Select
            label="Field Type"
            options={[
              { label: 'Text', value: 'text' },
              { label: 'Number', value: 'number' },
              { label: 'Dropdown', value: 'select' },
              { label: 'Date', value: 'date' },
              { label: 'Yes/No', value: 'boolean' },
              { label: 'File Upload', value: 'file' }
            ]}
          />
          <ChoiceList
            title="Field Options"
            choices={[
              { label: 'Required field', value: 'required' },
              { label: 'Show in product list', value: 'list' },
              { label: 'Searchable', value: 'search' }
            ]}
            selected={['required', 'search']}
          />
        </FormLayout>
      </Modal.Section>
    </Modal>
  );

  // Industry Templates
  const TemplateSelector = () => (
    <Card sectioned>
      <BlockStack gap="400">
        <Text variant="headingLg" as="h2">🚀 Quick Start Templates</Text>
        <Text>Get started in seconds with industry-specific fields</Text>
        
        <BlockStack gap="300">
          <InlineStack gap="300">
            <Button onClick={() => applyTemplate('apparel')}>
              👕 Apparel (Size, Color, Material, Care)
            </Button>
            <Button onClick={() => applyTemplate('food')}>
              🍕 Food (Expiry, Ingredients, Allergens)
            </Button>
            <Button onClick={() => applyTemplate('electronics')}>
              📱 Electronics (Warranty, Specs, Compatibility)
            </Button>
          </InlineStack>
        </BlockStack>
      </BlockStack>
    </Card>
  );

  const applyTemplate = (template) => {
    const templates = {
      apparel: [
        { name: 'Size', type: 'Dropdown', value: 'Medium' },
        { name: 'Color', type: 'Text', value: 'Blue' },
        { name: 'Material', type: 'Text', value: '100% Cotton' },
        { name: 'Care Instructions', type: 'Text', value: 'Machine wash' }
      ],
      food: [
        { name: 'Expiry Date', type: 'Date', value: '2024-12-31' },
        { name: 'Ingredients', type: 'Text', value: 'Flour, Sugar, Eggs' },
        { name: 'Allergens', type: 'Multi-select', value: 'Gluten, Eggs' }
      ],
      electronics: [
        { name: 'Warranty', type: 'Number', value: '12 months' },
        { name: 'Voltage', type: 'Text', value: '110-240V' },
        { name: 'Compatible With', type: 'Text', value: 'iOS, Android' }
      ]
    };
    setDemoFields(templates[template]);
  };

  // Value Proposition Banner
  const ValueBanner = () => (
    <Banner
      title="You're saving $1,971/month with custom fields!"
      status="success"
      action={{ content: 'View comparison', url: '#' }}
    >
      <p>
        Basic Shopify + InventorySync: $29 + $29 = $58/month<br />
        vs Shopify Plus: $2,000+/month
      </p>
    </Banner>
  );

  return (
    <Page
      title="Custom Fields Demo"
      subtitle="See how custom fields look in your Shopify admin"
      primaryAction={{
        content: 'Create Custom Field',
        onAction: () => setShowCreateModal(true)
      }}
    >
      <Layout>
        <Layout.Section>
          <BlockStack gap="500">
            <ValueBanner />
            <TemplateSelector />
            <ProductEditorDemo />
          </BlockStack>
        </Layout.Section>

        <Layout.Section secondary>
          <Card title="Current Custom Fields" sectioned>
            <BlockStack gap="300">
              {demoFields.map((field, index) => (
                <InlineStack key={index} align="space-between">
                  <BlockStack gap="100">
                    <Text variant="bodyMd" fontWeight="semibold">{field.name}</Text>
                    <Text variant="bodySm" color="subdued">{field.type}</Text>
                  </BlockStack>
                  <Button plain destructive size="slim">Remove</Button>
                </InlineStack>
              ))}
            </BlockStack>
          </Card>

          <Card title="Marketing Stats" sectioned>
            <BlockStack gap="200">
              <Text variant="bodyMd">Monthly Savings: <Text variant="bodyMd" fontWeight="bold" color="success">$1,971</Text></Text>
              <Text variant="bodyMd">Annual Savings: <Text variant="bodyMd" fontWeight="bold" color="success">$23,652</Text></Text>
              <Text variant="bodyMd">Setup Time: <Text variant="bodyMd" fontWeight="bold">3 clicks</Text></Text>
              <Text variant="bodyMd">Coding Required: <Text variant="bodyMd" fontWeight="bold">None</Text></Text>
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>

      <CreateFieldModal />
    </Page>
  );
};

export default CustomFieldsDemo;
