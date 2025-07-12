import React, { useState } from 'react';
import { BlockStack, Button, Card, Form, Layout, Page, Select, Text, TextField } from '@shopify/polaris';

function Settings({ showToast }) {
  const [settings, setSettings] = useState({
    defaultReorderPoint: '10',
    defaultReorderQuantity: '50',
    alertEmail: 'notifications@example.com',
    alertFrequency: 'immediate',
    forecastingEnabled: 'true',
    advancedForecastingEnabled: 'false',
    multiLocationEnabled: 'true',
    realTimeUpdatesEnabled: 'true'
  });

  const handleChange = (field) => (value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    showToast('Settings saved successfully!');
    // TODO: Implement actual settings save to backend
  };

  const alertFrequencyOptions = [
    { label: 'Immediate', value: 'immediate' },
    { label: 'Hourly', value: 'hourly' },
    { label: 'Daily', value: 'daily' }
  ];

  const booleanOptions = [
    { label: 'Enabled', value: 'true' },
    { label: 'Disabled', value: 'false' }
  ];

  return (
    <Page
      title="Settings"
      breadcrumbs={[{ content: 'Dashboard', url: '/' }]}
      primaryAction={{
        content: 'Save Settings',
        onAction: handleSave
      }}
    >
      <Layout>
        <Layout.Section>
          <Card>
            <div style={{padding: '20px'}}>
              <Form onSubmit={handleSave}>
                <BlockStack vertical spacing="loose">
                  <div style={{marginBottom: '16px'}}>
                    <Text variant="headingMd" as="h2">Inventory Defaults</Text>
                  </div>
                  <TextField
                    label="Default Reorder Point"
                    type="number"
                    value={settings.defaultReorderPoint}
                    onChange={handleChange('defaultReorderPoint')}
                    helpText="Default minimum stock level before reordering"
                  />
                  <TextField
                    label="Default Reorder Quantity"
                    type="number"
                    value={settings.defaultReorderQuantity}
                    onChange={handleChange('defaultReorderQuantity')}
                    helpText="Default quantity to order when restocking"
                  />
                  <div style={{marginTop: '32px', marginBottom: '16px'}}>
                    <Text variant="headingMd" as="h2">Alert Configuration</Text>
                  </div>
                  <TextField
                    label="Alert Email"
                    type="email"
                    value={settings.alertEmail}
                    onChange={handleChange('alertEmail')}
                    helpText="Email address for inventory alerts"
                  />
                  <Select
                    label="Alert Frequency"
                    options={alertFrequencyOptions}
                    value={settings.alertFrequency}
                    onChange={handleChange('alertFrequency')}
                    helpText="How often to send alert notifications"
                  />
                  <div style={{marginTop: '32px', marginBottom: '16px'}}>
                    <Text variant="headingMd" as="h2">Advanced Features</Text>
                  </div>
                  <Select
                    label="Forecasting"
                    options={booleanOptions}
                    value={settings.forecastingEnabled}
                    onChange={handleChange('forecastingEnabled')}
                    helpText="Enable demand forecasting based on sales history"
                  />
                  <Select
                    label="Advanced Forecasting (ML Analysis)"
                    options={booleanOptions}
                    value={settings.advancedForecastingEnabled}
                    onChange={handleChange('advancedForecastingEnabled')}
                    helpText="Enable machine learning-powered predictions with time series analysis"
                  />
                  <Select
                    label="Real-time Updates"
                    options={booleanOptions}
                    value={settings.realTimeUpdatesEnabled}
                    onChange={handleChange('realTimeUpdatesEnabled')}
                    helpText="Enable automatic data refresh and live inventory updates"
                  />
                  <Select
                    label="Multi-Location Support"
                    options={booleanOptions}
                    value={settings.multiLocationEnabled}
                    onChange={handleChange('multiLocationEnabled')}
                    helpText="Enable inventory tracking across multiple locations"
                  />
                </BlockStack>
              </Form>
            </div>
          </Card>
        </Layout.Section>

        <Layout.Section secondary>
          <Card>
            <div style={{padding: '20px'}}>
              <BlockStack vertical spacing="loose">
                <Text variant="headingMd" as="h2">Subscription Plan</Text>
                <div style={{padding: '16px', backgroundColor: '#f1f2f3', borderRadius: '8px'}}>
                  <BlockStack distribution="equalSpacing" alignment="center">
                    <div>
                      <Text variant="headingLg" as="h3">Growth Plan</Text>
                      <Text variant="bodyMd" color="subdued">$59/month</Text>
                    </div>
                    <Button outline>Upgrade</Button>
                  </BlockStack>
                </div>
                <Text variant="bodyMd" color="subdued">
                  Your current plan includes up to 10,000 products and 5 locations.
                </Text>
              </BlockStack>
            </div>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}

export default Settings;