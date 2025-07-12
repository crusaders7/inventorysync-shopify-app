import React, { useState } from 'react';
import { Banner, Button, Card, FormLayout, Icon, Layout, Page, Text, TextField } from '@shopify/polaris';
import { StoreMajor } from '@shopify/polaris-icons';

const ShopifyInstall = () => {
  const [shopDomain, setShopDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const validateShopDomain = (domain) => {
    // Basic validation for Shopify domain format
    const pattern = /^[a-zA-Z0-9][a-zA-Z0-9-]*\.myshopify\.com$/;
    return pattern.test(domain);
  };

  const handleInstall = async () => {
    setError('');
    
    // Ensure the domain ends with .myshopify.com
    let formattedDomain = shopDomain.trim();
    if (!formattedDomain.includes('.myshopify.com')) {
      formattedDomain += '.myshopify.com';
    }

    if (!validateShopDomain(formattedDomain)) {
      setError('Please enter a valid Shopify store domain (e.g., mystore.myshopify.com)');
      return;
    }

    setLoading(true);

    try {
      // Redirect to the backend OAuth installation endpoint
      const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const installUrl = `${backendUrl}/api/v1/auth/install?shop=${encodeURIComponent(formattedDomain)}`;
      
      // Redirect to the installation URL
      window.location.href = installUrl;
    } catch (err) {
      setError('Failed to start installation. Please try again.');
      setLoading(false);
    }
  };

  return (
    <Page>
      <Layout>
        <Layout.Section>
          <div style={{ maxWidth: '600px', margin: '0 auto', paddingTop: '40px' }}>
            <Card sectioned>
              <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                <Icon source={StoreMajor} color="primary" backdrop />
                <Text variant="headingXl" as="h1" alignment="center">
                  Install InventorySync
                </Text>
                <Text variant="bodyMd" color="subdued" alignment="center">
                  Smart inventory management for your Shopify store
                </Text>
              </div>

              <FormLayout>
                {error && (
                  <Banner status="critical" onDismiss={() => setError('')}>
                    {error}
                  </Banner>
                )}

                <TextField
                  label="Store domain"
                  value={shopDomain}
                  onChange={setShopDomain}
                  placeholder="mystore.myshopify.com"
                  helpText="Enter your Shopify store domain"
                  autoComplete="off"
                  disabled={loading}
                />

                <Button
                  primary
                  fullWidth
                  size="large"
                  onClick={handleInstall}
                  loading={loading}
                  disabled={!shopDomain || loading}
                >
                  Install App
                </Button>
              </FormLayout>
            </Card>

            <div style={{ marginTop: '20px', textAlign: 'center' }}>
              <Text variant="bodyMd" color="subdued">
                By installing, you agree to our Terms of Service and Privacy Policy
              </Text>
            </div>
          </div>
        </Layout.Section>
      </Layout>
    </Page>
  );
};

export default ShopifyInstall;