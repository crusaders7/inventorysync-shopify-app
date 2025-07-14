import React, { useState, useEffect } from 'react';
import { BlockStack, Button, Card, Icon, Layout, Page, Text } from '@shopify/polaris';
import {
  SettingsMajor,
  ProductsMajor
} from '@shopify/polaris-icons';

import { useNavigate } from 'react-router-dom';

function Dashboard({ showToast }) {
  const navigate = useNavigate();
  const [customFieldsCount, setCustomFieldsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [shopDomain, setShopDomain] = useState(null);

  useEffect(() => {
    // Get shop domain from URL params or localStorage
    const params = new URLSearchParams(window.location.search);
    const shop = params.get('shop') || 
                localStorage.getItem('shopDomain') || 
                localStorage.getItem('shopify_shop_domain') ||
                'inventorysync-dev.myshopify.com';
    
    setShopDomain(shop);
    
    // Fetch custom fields count
    fetchCustomFieldsCount(shop);
  }, []);

  const fetchCustomFieldsCount = async (shop) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/custom-fields/${shop}`);
      const data = await response.json();
      
      if (response.ok && data.fields) {
        setCustomFieldsCount(data.fields.length);
      }
    } catch (error) {
      console.error('Failed to fetch custom fields count:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Page 
      title="Custom Fields Manager"
      subtitle="Add custom data fields to your Shopify products"
      primaryAction={{
        content: 'Manage Custom Fields',
        onAction: () => navigate('/custom-fields')
      }}
    >
      <Layout>
        <Layout.Section>
          <Card>
            <BlockStack gap="400">
              <BlockStack gap="200">
                <Text variant="headingMd" as="h2">
                  Welcome to Custom Fields Manager
                </Text>
                <Text variant="bodyMd" color="subdued">
                  Extend your Shopify product data with custom fields like size charts, 
                  materials, care instructions, and more.
                </Text>
              </BlockStack>

              <BlockStack gap="400">
                <Card>
                  <BlockStack gap="200">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Icon source={SettingsMajor} color="primary" />
                      <Text variant="headingMd" as="h3">
                        Custom Fields Status
                      </Text>
                    </div>
                    <Text variant="headingLg" as="p">
                      {loading ? 'Loading...' : `${customFieldsCount} Active Fields`}
                    </Text>
                    <Text variant="bodyMd" color="subdued">
                      {customFieldsCount > 0 
                        ? 'Your custom fields are active and collecting data.'
                        : 'Get started by creating your first custom field.'}
                    </Text>
                  </BlockStack>
                </Card>

                <Card>
                  <BlockStack gap="200">
                    <Text variant="headingMd" as="h3">
                      Quick Actions
                    </Text>
                    <BlockStack gap="200">
                      <Button 
                        onClick={() => navigate('/custom-fields')}
                        fullWidth
                        primary
                      >
                        Create New Custom Field
                      </Button>
                      <Button 
                        onClick={() => navigate('/inventory')}
                        fullWidth
                      >
                        View Products with Custom Fields
                      </Button>
                    </BlockStack>
                  </BlockStack>
                </Card>

                <Card>
                  <BlockStack gap="200">
                    <Text variant="headingMd" as="h3">
                      Popular Field Types
                    </Text>
                    <BlockStack gap="100">
                      <Text variant="bodyMd">• Text fields for descriptions</Text>
                      <Text variant="bodyMd">• Number fields for measurements</Text>
                      <Text variant="bodyMd">• Date fields for expiry dates</Text>
                      <Text variant="bodyMd">• Select dropdowns for categories</Text>
                      <Text variant="bodyMd">• Boolean checkboxes for features</Text>
                    </BlockStack>
                  </BlockStack>
                </Card>
              </BlockStack>
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}

export default Dashboard;
