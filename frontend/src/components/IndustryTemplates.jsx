import React, { useState, useEffect } from 'react';
import { Badge, Banner, BlockStack, Button, ButtonGroup, Card, Grid, InlineStack, Layout, Loading, Modal, Page, Text, TextContainer, Thumbnail, Toast } from '@shopify/polaris';
// Icons removed for now due to compatibility issues

const IndustryTemplates = ({ shop, showToast }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [templateDetails, setTemplateDetails] = useState(null);
  const [appliedTemplate, setAppliedTemplate] = useState(null);

  const industryIcons = {
    apparel: '👔',
    electronics: '📱',
    food_beverage: '🍎',
    jewelry: '💎',
    automotive: '🚗',
    health_beauty: '💄',
  };

  const industryColors = {
    apparel: 'info',
    electronics: 'success',
    food_beverage: 'warning',
    jewelry: 'critical',
    automotive: 'subdued',
    health_beauty: 'attention',
  };

  useEffect(() => {
    fetchTemplates();
    checkAppliedTemplate();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/v1/templates/industries');
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      showToast('Failed to load templates', true);
    } finally {
      setLoading(false);
    }
  };

  const checkAppliedTemplate = async () => {
    // Check if store already has a template applied
    // This would check store metadata
  };

  const handlePreviewTemplate = async (industry) => {
    try {
      const response = await fetch(`/api/v1/templates/industries/${industry}`);
      const data = await response.json();
      setTemplateDetails(data.template);
      setSelectedTemplate(industry);
      setShowPreview(true);
    } catch (error) {
      console.error('Failed to fetch template details:', error);
      showToast('Failed to load template details', true);
    }
  };

  const handleApplyTemplate = async () => {
    if (!selectedTemplate) return;

    setApplying(true);
    try {
      const response = await fetch(
        `/api/v1/templates/apply/${selectedTemplate}?shop=${encodeURIComponent(shop)}`,
        { method: 'POST' }
      );
      
      const data = await response.json();
      
      if (response.ok) {
        setAppliedTemplate(selectedTemplate);
        setShowPreview(false);
        showToast(`${templateDetails.name} template applied successfully!`);
      } else {
        throw new Error(data.detail || 'Failed to apply template');
      }
    } catch (error) {
      console.error('Failed to apply template:', error);
      showToast(error.message, true);
    } finally {
      setApplying(false);
    }
  };

  const templateCards = templates.map((template) => (
    <Grid.Cell columnSpan={{ xs: 6, sm: 3, md: 2, lg: 2, xl: 2 }} key={template.id}>
      <Card>
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center',
            width: '64px',
            height: '64px',
            margin: '0 auto 12px auto',
            fontSize: '48px'
          }}>
            {industryIcons[template.id] || '🏢'}
          </div>
          <BlockStack gap="200">
            <Text variant="headingMd" as="h3">
              {template.name}
            </Text>
            <Text variant="bodyMd" color="subdued">
              {template.description}
            </Text>
            <div style={{ marginTop: '8px' }}>
              <Badge status={industryColors[template.id] || 'info'}>
                {template.field_count} custom fields
              </Badge>
              {template.workflow_count > 0 && (
                <Badge status="success" size="small">
                  {template.workflow_count} workflows
                </Badge>
              )}
            </div>
          </BlockStack>
          <div style={{ marginTop: '16px' }}>
            <ButtonGroup>
              <Button 
                onClick={() => handlePreviewTemplate(template.id)}
                outline
              >
                Preview
              </Button>
              <Button 
                primary
                onClick={() => {
                  setSelectedTemplate(template.id);
                  handlePreviewTemplate(template.id);
                }}
                disabled={appliedTemplate === template.id}
              >
                {appliedTemplate === template.id ? '✓ Applied' : 'Apply'}
              </Button>
            </ButtonGroup>
          </div>
        </div>
      </Card>
    </Grid.Cell>
  ));

  if (loading) {
    return (
      <Page title="Industry Templates">
        <Layout>
          <Layout.Section>
            <Card>
              <div style={{ padding: '60px', textAlign: 'center' }}>
                <Loading />
                <Text>Loading industry templates...</Text>
              </div>
            </Card>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  return (
    <Page
      title="Industry Templates"
      subtitle="Pre-configured custom fields and workflows for your industry"
    >
      <Layout>
        <Layout.Section>
          <Banner
            title="Quick Setup for Your Industry"
            status="info"
          >
            <p>
              Choose your industry template to automatically configure custom fields, 
              workflows, and best practices for your business type. This will save you 
              hours of setup time and ensure you're tracking the right data.
            </p>
          </Banner>
        </Layout.Section>

        <Layout.Section>
          <Grid>
            {templateCards}
          </Grid>
        </Layout.Section>

        {/* Custom Template Card */}
        <Layout.Section>
          <Card>
            <div style={{ padding: '24px', textAlign: 'center' }}>
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>⚙️</div>
              <BlockStack gap="200">
                <Text variant="headingMd" as="h3">
                  Custom Setup
                </Text>
                <Text variant="bodyMd" color="subdued">
                  Don't see your industry? Create custom fields manually or contact us 
                  for a personalized template.
                </Text>
              </BlockStack>
              <div style={{ marginTop: '16px' }}>
                <ButtonGroup>
                  <Button outline>
                    Create Custom Fields
                  </Button>
                  <Button>
                    Contact Support
                  </Button>
                </ButtonGroup>
              </div>
            </div>
          </Card>
        </Layout.Section>
      </Layout>

      {/* Template Preview Modal */}
      <Modal
        open={showPreview}
        onClose={() => setShowPreview(false)}
        title={templateDetails ? `${templateDetails.name} Template` : 'Template Preview'}
        primaryAction={{
          content: applying ? 'Applying...' : 'Apply Template',
          onAction: handleApplyTemplate,
          loading: applying,
          disabled: applying || appliedTemplate === selectedTemplate
        }}
        secondaryActions={[
          {
            content: 'Cancel',
            onAction: () => setShowPreview(false)
          }
        ]}
        large
      >
        {templateDetails && (
          <Modal.Section>
            <BlockStack gap="500">
              <TextContainer>
                <Text variant="headingMd">What's Included</Text>
                <Text>{templateDetails.description}</Text>
              </TextContainer>

              <Card sectioned>
                <BlockStack gap="200">
                  <Text variant="headingSm">Custom Fields ({templateDetails.custom_fields?.length || 0})</Text>
                  {templateDetails.custom_fields?.slice(0, 5).map((field, index) => (
                    <div key={index} style={{ 
                      padding: '8px 12px', 
                      backgroundColor: '#f6f6f7', 
                      borderRadius: '4px',
                      marginBottom: '4px'
                    }}>
                      <InlineStack gap="400">
                        <InlineStack gap="200">
                          <Text variant="bodySm" fontWeight="semibold">
                            {field.display_name}
                          </Text>
                          <Badge size="small">{field.field_type}</Badge>
                        </InlineStack>
                        {field.is_required && (
                          <Badge status="critical" size="small">Required</Badge>
                        )}
                      </InlineStack>
                      {field.help_text && (
                        <Text variant="captionMd" color="subdued">
                          {field.help_text}
                        </Text>
                      )}
                    </div>
                  ))}
                  {templateDetails.custom_fields?.length > 5 && (
                    <Text variant="captionMd" color="subdued">
                      ... and {templateDetails.custom_fields.length - 5} more fields
                    </Text>
                  )}
                </BlockStack>
              </Card>

              {templateDetails.workflows && templateDetails.workflows.length > 0 && (
                <Card sectioned>
                  <BlockStack gap="200">
                    <Text variant="headingSm">Automated Workflows ({templateDetails.workflows.length})</Text>
                    {templateDetails.workflows.map((workflow, index) => (
                      <div key={index} style={{ 
                        padding: '8px 12px', 
                        backgroundColor: '#f6f6f7', 
                        borderRadius: '4px',
                        marginBottom: '4px'
                      }}>
                        <Text variant="bodySm" fontWeight="semibold">
                          {workflow.name}
                        </Text>
                        <Text variant="captionMd" color="subdued">
                          Triggers on: {workflow.trigger}
                        </Text>
                      </div>
                    ))}
                  </BlockStack>
                </Card>
              )}

              <Banner status="warning">
                <p>
                  <strong>Note:</strong> Applying this template will create new custom fields 
                  and workflows. Existing data will not be affected, but you may need to 
                  populate the new fields for existing products.
                </p>
              </Banner>
            </BlockStack>
          </Modal.Section>
        )}
      </Modal>
    </Page>
  );
};

export default IndustryTemplates;