import React, { useState } from 'react';
import { Badge, Banner, BlockStack, Button, Card, InlineStack, Layout, Page, Text } from '@shopify/polaris';
import { clearAllCachingMechanisms } from '../utils/clearCache';

export default function CacheManager() {
  const [clearing, setClearing] = useState(false);
  const [cleared, setCleared] = useState(false);
  const [error, setError] = useState(null);

  const handleClearCache = async () => {
    setClearing(true);
    setCleared(false);
    setError(null);

    try {
      await clearAllCachingMechanisms();
      setCleared(true);
      
      // Auto-reload after 2 seconds
      setTimeout(() => {
        window.location.reload(true);
      }, 2000);
    } catch (e) {
      setError(e.message || 'Failed to clear cache');
    } finally {
      setClearing(false);
    }
  };

  return (
    <Page title="Cache Management">
      <Layout>
        <Layout.Section>
          {error && (
            <Banner status="critical" onDismiss={() => setError(null)}>
              <p>{error}</p>
            </Banner>
          )}
          
          {cleared && (
            <Banner status="success">
              <p>All caches cleared successfully! The page will reload in 2 seconds...</p>
            </Banner>
          )}

          <Card>
            <Card.Section>
              <BlockStack gap="500">
                <Text variant="headingMd" as="h2">
                  Browser Cache Management
                </Text>
                
                <Text color="subdued">
                  Clear all cached data including API endpoints, localStorage, sessionStorage, 
                  cookies, service workers, and IndexedDB to ensure the application uses the 
                  latest configuration.
                </Text>

                <BlockStack gap="200">
                  <Text variant="headingSm" as="h3">
                    This will clear:
                  </Text>
                  <InlineStack gap="200">
                    <Badge>localStorage</Badge>
                    <Badge>sessionStorage</Badge>
                    <Badge>Cookies</Badge>
                    <Badge>Service Workers</Badge>
                    <Badge>Cache API</Badge>
                    <Badge>IndexedDB</Badge>
                  </InlineStack>
                </BlockStack>

                <div>
                  <Button
                    primary
                    onClick={handleClearCache}
                    loading={clearing}
                    disabled={clearing}
                  >
                    Clear All Caches
                  </Button>
                </div>

                <Banner status="info">
                  <p>
                    <strong>Note:</strong> After clearing caches, you may need to log in again 
                    and reconfigure any saved preferences.
                  </p>
                </Banner>
              </BlockStack>
            </Card.Section>
          </Card>

          <Card>
            <Card.Section>
              <BlockStack gap="500">
                <Text variant="headingMd" as="h2">
                  Manual Cache Clear Instructions
                </Text>
                
                <Text color="subdued">
                  If the automatic cache clear doesn't work, you can manually clear your browser cache:
                </Text>

                <BlockStack gap="200">
                  <div>
                    <Text variant="headingSm" as="h3">Chrome/Edge:</Text>
                    <Text>Press Ctrl+Shift+Delete (Windows/Linux) or Cmd+Shift+Delete (Mac)</Text>
                  </div>
                  
                  <div>
                    <Text variant="headingSm" as="h3">Firefox:</Text>
                    <Text>Press Ctrl+Shift+Delete (Windows/Linux) or Cmd+Shift+Delete (Mac)</Text>
                  </div>
                  
                  <div>
                    <Text variant="headingSm" as="h3">Safari:</Text>
                    <Text>Go to Safari → Preferences → Privacy → Manage Website Data</Text>
                  </div>
                </BlockStack>

                <Text color="subdued">
                  Additionally, you can force a hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
                </Text>
              </BlockStack>
            </Card.Section>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}
