import React from 'react';
import { BlockStack, Card, InlineStack, Layout, Page, Text } from '@shopify/polaris';

export default function CustomFieldsTest() {
  return (
    <Page title="Custom Fields Test">
      <Layout>
        <Layout.Section>
          <Card>
            <BlockStack gap="400">
              <Text variant="headingMd">Custom Fields Test</Text>
              <Text>This is a test to verify Polaris components work correctly.</Text>
              <InlineStack gap="200">
                <Text>Item 1</Text>
                <Text>Item 2</Text>
                <Text>Item 3</Text>
              </InlineStack>
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}