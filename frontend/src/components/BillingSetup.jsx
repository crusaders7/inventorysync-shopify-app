import React, { useState, useEffect } from 'react';
import { Badge, Banner, BlockStack, Button, ButtonGroup, Card, Divider, InlineStack, Layout, List, Page, Spinner, Text } from '@shopify/polaris';

const BillingSetup = ({ shop, onComplete }) => {
  const [loading, setLoading] = useState(false);
  const [plans, setPlans] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState('growth');

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await fetch('/api/v1/billing/plans');
      const data = await response.json();
      setPlans(data.plans);
    } catch (error) {
      console.error('Failed to fetch plans:', error);
    }
  };

  const handleSubscribe = async (planName) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/billing/subscribe/${planName}?shop=${shop}`, {
        method: 'POST'
      });
      
      if (response.redirected) {
        // Redirect to Shopify billing confirmation
        window.location.href = response.url;
      } else {
        const data = await response.json();
        if (data.confirmation_url) {
          window.location.href = data.confirmation_url;
        }
      }
    } catch (error) {
      console.error('Subscription failed:', error);
      setLoading(false);
    }
  };

  const getPlanBadge = (planKey) => {
    const badges = {
      starter: { status: 'info', children: 'Best for Small Stores' },
      growth: { status: 'success', children: 'Most Popular' },
      pro: { status: 'attention', children: 'Maximum Power' }
    };
    return badges[planKey] || null;
  };

  if (!plans) {
    return (
      <Page title="Setting up your subscription...">
        <Layout>
          <Layout.Section>
            <Card>
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <Spinner size="large" />
                <Text variant="bodyMd">Loading subscription plans...</Text>
              </div>
            </Card>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  return (
    <Page 
      title="Choose Your FlexInventory Plan"
      subtitle="Start with a 7-day free trial, cancel anytime"
    >
      <Layout>
        <Layout.Section>
          <Banner
            title="Welcome to FlexInventory!"
            status="info"
          >
            <Text variant="bodyMd">
              Select a plan to get started. All plans include a 7-day free trial with full access to features.
            </Text>
          </Banner>
        </Layout.Section>

        <Layout.Section>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
            {Object.entries(plans).map(([planKey, plan]) => (
              <Card key={planKey} sectioned>
                <BlockStack gap="tight">
                  <InlineStack align="space-between" wrap={false}>
                    <Text variant="headingMd" as="h3">
                      {plan.name.replace('FlexInventory ', '')}
                    </Text>
                    {getPlanBadge(planKey) && <Badge {...getPlanBadge(planKey)} />}
                  </InlineStack>

                  <InlineStack gap="200">
                    <Text variant="headingLg" as="h2">
                      ${plan.price}
                    </Text>
                    <Text variant="bodyMd" color="subdued">
                      /month
                    </Text>
                  </InlineStack>

                  <Text variant="bodyMd" color="subdued">
                    7-day free trial included
                  </Text>

                  <Divider />

                  <List type="bullet">
                    {plan.features.map((feature, index) => (
                      <List.Item key={index}>
                        <Text variant="bodyMd">{feature}</Text>
                      </List.Item>
                    ))}
                  </List>

                  <div style={{ marginTop: 'auto', paddingTop: '1rem' }}>
                    <Button
                      primary={planKey === 'growth'}
                      fullWidth
                      loading={loading}
                      onClick={() => handleSubscribe(planKey)}
                      disabled={loading}
                    >
                      {planKey === 'growth' ? 'Start Free Trial (Recommended)' : 'Start Free Trial'}
                    </Button>
                  </div>
                </BlockStack>
              </Card>
            ))}
          </div>
        </Layout.Section>

        <Layout.Section>
          <Card sectioned>
            <BlockStack gap="tight">
              <Text variant="headingMd" as="h3">
                What happens next?
              </Text>
              <List type="number">
                <List.Item>
                  <Text variant="bodyMd">Click "Start Free Trial" on your preferred plan</Text>
                </List.Item>
                <List.Item>
                  <Text variant="bodyMd">Review and approve the subscription in Shopify</Text>
                </List.Item>
                <List.Item>
                  <Text variant="bodyMd">Return to FlexInventory to start managing your inventory</Text>
                </List.Item>
                <List.Item>
                  <Text variant="bodyMd">Your trial lasts 7 days - cancel anytime before then with no charge</Text>
                </List.Item>
              </List>
            </BlockStack>
          </Card>
        </Layout.Section>

        <Layout.Section>
          <Card sectioned>
            <BlockStack gap="tight">
              <Text variant="headingMd" as="h3">
                Questions about pricing?
              </Text>
              <Text variant="bodyMd">
                • All plans include unlimited users and premium support
              </Text>
              <Text variant="bodyMd">
                • Usage limits are soft limits with grace periods
              </Text>
              <Text variant="bodyMd">
                • Cancel anytime - no long-term contracts
              </Text>
              <Text variant="bodyMd">
                • Enterprise plans available for 50,000+ products
              </Text>
            </BlockStack>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
};

export default BillingSetup;
