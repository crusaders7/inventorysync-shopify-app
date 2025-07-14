/**
 * ReportsBuilder - Custom reporting engine with drag-and-drop interface
 * Build reports on any field including custom fields
 */

import React, { useState, useEffect } from 'react';
import { Badge, Banner, BlockStack, Button, ButtonGroup, Card, Checkbox, ChoiceList, Collapsible, DataTable, EmptyState, Form, FormLayout, Frame, Icon, InlineStack, Layout, List, Modal, Page, ProgressBar, ResourceItem, ResourceList, Select, Spinner, Tabs, Text, TextField, Toast } from '@shopify/polaris';
import {
  ReportsMajor,
  EditMajor,
  DeleteMajor,
  CirclePlusMajor,
  ViewMajor,
  RefreshMajor,
  ExportMinor,
  FilterMajor,
  AnalyticsMajor,
  DragDropMajor,
  ChevronDownMinor,
  ChevronUpMinor
} from '@shopify/polaris-icons';

const ReportsBuilder = ({ shopDomain }) => {
  // State management
  const [availableFields, setAvailableFields] = useState({});
  const [savedReports, setSavedReports] = useState([]);
  const [reportResults, setReportResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedTab, setSelectedTab] = useState(0);
  const [showBuilderModal, setShowBuilderModal] = useState(false);
  const [toast, setToast] = useState(null);

  // Report builder state
  const [reportBuilder, setReportBuilder] = useState({
    name: '',
    description: '',
    entity_type: 'product',
    metrics: [],
    group_by: [],
    filters: [],
    sort_by: '',
    sort_order: 'desc',
    limit: 1000
  });

  // UI state
  const [expandedSections, setExpandedSections] = useState({
    metrics: true,
    groupBy: false,
    filters: false,
    sorting: false
  });

  // Constants
  const ENTITY_TYPES = [
    { label: 'Products', value: 'product' },
    { label: 'Product Variants', value: 'variant' },
    { label: 'Inventory Items', value: 'inventory' },
    { label: 'Alerts', value: 'alert' }
  ];

  const AGGREGATION_TYPES = [
    { label: 'Sum', value: 'sum' },
    { label: 'Average', value: 'avg' },
    { label: 'Count', value: 'count' },
    { label: 'Minimum', value: 'min' },
    { label: 'Maximum', value: 'max' },
    { label: 'Count Distinct', value: 'count_distinct' }
  ];

  const GROUP_BY_OPTIONS = [
    { label: 'Day', value: 'day' },
    { label: 'Week', value: 'week' },
    { label: 'Month', value: 'month' },
    { label: 'Year', value: 'year' },
    { label: 'Location', value: 'location' },
    { label: 'Product Type', value: 'product_type' },
    { label: 'Vendor', value: 'vendor' },
    { label: 'Custom Field', value: 'custom_field' }
  ];

  const FILTER_OPERATORS = [
    { label: 'Equals', value: 'equals' },
    { label: 'Not Equals', value: 'not_equals' },
    { label: 'Greater Than', value: 'greater_than' },
    { label: 'Less Than', value: 'less_than' },
    { label: 'Contains', value: 'contains' },
    { label: 'In List', value: 'in' }
  ];

  // Load data on component mount
  useEffect(() => {
    loadSavedReports();
    loadAvailableFields();
  }, []);

  useEffect(() => {
    loadAvailableFields();
  }, [reportBuilder.entity_type]);

  // API Functions
  const loadSavedReports = async () => {
    try {
      const response = await fetch(`/api/v1/reports/${shopDomain}/saved`);
      const data = await response.json();

      if (response.ok) {
        setSavedReports(data.saved_reports);
      } else {
        throw new Error(data.error || 'Failed to load saved reports');
      }
    } catch (error) {
      console.error('Error loading saved reports:', error);
      setToast({ content: 'Failed to load saved reports', error: true });
    }
  };

  const loadAvailableFields = async () => {
    try {
      const response = await fetch(`/api/v1/reports/${shopDomain}/fields/${reportBuilder.entity_type}`);
      const data = await response.json();

      if (response.ok) {
        setAvailableFields(data);
      } else {
        throw new Error(data.error || 'Failed to load available fields');
      }
    } catch (error) {
      console.error('Error loading available fields:', error);
      setToast({ content: 'Failed to load available fields', error: true });
    }
  };

  const buildReport = async (exportFormat = 'json') => {
    try {
      setLoading(true);
      
      const response = await fetch(`/api/v1/reports/${shopDomain}/build?export_format=${exportFormat}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reportBuilder)
      });

      if (exportFormat === 'csv') {
        // Handle CSV download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${reportBuilder.name.replace(/\s+/g, '_')}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        setToast({ content: 'Report exported to CSV', error: false });
        return;
      }

      const data = await response.json();

      if (response.ok) {
        setReportResults(data);
        setToast({ content: 'Report generated successfully', error: false });
      } else {
        throw new Error(data.error || 'Failed to build report');
      }
    } catch (error) {
      console.error('Error building report:', error);
      setToast({ content: error.message, error: true });
    } finally {
      setLoading(false);
    }
  };

  const applyTemplate = (template) => {
    setReportBuilder({
      ...template.definition,
      name: template.name,
      description: template.description
    });
    setShowBuilderModal(true);
  };

  // Report builder functions
  const addMetric = () => {
    const newMetric = {
      field: '',
      aggregation: 'count',
      label: ''
    };
    setReportBuilder(prev => ({
      ...prev,
      metrics: [...prev.metrics, newMetric]
    }));
  };

  const updateMetric = (index, field, value) => {
    setReportBuilder(prev => ({
      ...prev,
      metrics: prev.metrics.map((metric, i) => 
        i === index ? { ...metric, [field]: value } : metric
      )
    }));
  };

  const removeMetric = (index) => {
    setReportBuilder(prev => ({
      ...prev,
      metrics: prev.metrics.filter((_, i) => i !== index)
    }));
  };

  const addFilter = () => {
    const newFilter = {
      field: '',
      operator: 'equals',
      value: ''
    };
    setReportBuilder(prev => ({
      ...prev,
      filters: [...prev.filters, newFilter]
    }));
  };

  const updateFilter = (index, field, value) => {
    setReportBuilder(prev => ({
      ...prev,
      filters: prev.filters.map((filter, i) => 
        i === index ? { ...filter, [field]: value } : filter
      )
    }));
  };

  const removeFilter = (index) => {
    setReportBuilder(prev => ({
      ...prev,
      filters: prev.filters.filter((_, i) => i !== index)
    }));
  };

  const resetBuilder = () => {
    setReportBuilder({
      name: '',
      description: '',
      entity_type: 'product',
      metrics: [],
      group_by: [],
      filters: [],
      sort_by: '',
      sort_order: 'desc',
      limit: 1000
    });
    setReportResults(null);
  };

  // Helper functions
  const getFieldOptions = () => {
    if (!availableFields.standard_fields && !availableFields.custom_fields) return [];
    
    const options = [];
    
    // Add standard fields
    (availableFields.standard_fields || []).forEach(field => {
      options.push({
        label: `${field.label} (${field.type})`,
        value: field.field
      });
    });
    
    // Add custom fields
    (availableFields.custom_fields || []).forEach(field => {
      options.push({
        label: `${field.label} (Custom)`,
        value: field.field
      });
    });
    
    return options;
  };

  const getAggregationsForField = (fieldName) => {
    if (!availableFields.standard_fields && !availableFields.custom_fields) return [];
    
    // Find field in standard or custom fields
    const allFields = [
      ...(availableFields.standard_fields || []),
      ...(availableFields.custom_fields || [])
    ];
    
    const field = allFields.find(f => f.field === fieldName);
    if (!field) return AGGREGATION_TYPES;
    
    // Filter aggregations based on field type
    return AGGREGATION_TYPES.filter(agg => 
      field.aggregations && field.aggregations.includes(agg.value)
    );
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Render report results
  const renderReportResults = () => {
    if (!reportResults) return null;

    const data = reportResults.data || [];
    if (data.length === 0) {
      return (
        <EmptyState
          heading="No data found"
          image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
        >
          <p>Try adjusting your filters or metrics to get results.</p>
        </EmptyState>
      );
    }

    // Convert data to table format
    const headers = Object.keys(data[0]);
    const rows = data.map(row => headers.map(header => row[header]));

    return (
      <Card>
        <div style={{ padding: '1rem' }}>
          <InlineStack align="space-between" wrap={false}>
            <BlockStack gap="200">
              <Text variant="headingMd" as="h2">{reportResults.report_name}</Text>
              <Text variant="bodySm" color="subdued">{reportResults.row_count} rows • Generated {new Date(reportResults.generated_at).toLocaleString()}</Text>
            </BlockStack>
            <Button 
              icon={ExportMinor}
              onClick={() => buildReport('csv')}
            >
              Export CSV
            </Button>
          </InlineStack>
        </div>
        
        <DataTable
          columnContentTypes={headers.map(() => 'text')}
          headings={headers}
          rows={rows}
        />
      </Card>
    );
  };

  // Tabs
  const tabs = [
    {
      id: 'builder',
      content: 'Report Builder',
      accessibilityLabel: 'Report builder',
      panelID: 'builder-panel'
    },
    {
      id: 'templates',
      content: 'Templates',
      accessibilityLabel: 'Report templates',
      panelID: 'templates-panel'
    }
  ];

  return (
    <Frame>
      <Page
        title="Custom Reports"
        primaryAction={{
          content: 'New Report',
          icon: CirclePlusMajor,
          onAction: () => setShowBuilderModal(true)
        }}
        secondaryActions={[
          {
            content: 'Reset Builder',
            onAction: resetBuilder
          }
        ]}
      >
        <Tabs tabs={tabs} selected={selectedTab} onSelect={setSelectedTab}>
          {selectedTab === 0 && (
            <Layout>
              <Layout.Section oneThird>
                <Card sectioned>
                  <BlockStack gap="loose">
                    <Text variant="headingMd" as="h2">Report Configuration</Text>
                    
                    <TextField
                      label="Report Name"
                      value={reportBuilder.name}
                      onChange={(value) => setReportBuilder(prev => ({ ...prev, name: value }))}
                      placeholder="My Custom Report"
                    />
                    
                    <Select
                      label="Data Source"
                      options={ENTITY_TYPES}
                      value={reportBuilder.entity_type}
                      onChange={(value) => setReportBuilder(prev => ({ ...prev, entity_type: value }))}
                    />

                    {/* Metrics Section */}
                    <Card sectioned>
                      <InlineStack align="space-between">
                        <Text variant="headingSm" as="h3">Metrics</Text>
                        <Button
                          size="slim"
                          icon={expandedSections.metrics ? ChevronUpMinor : ChevronDownMinor}
                          onClick={() => toggleSection('metrics')}
                        />
                      </InlineStack>
                      
                      <Collapsible open={expandedSections.metrics}>
                        <div style={{ marginTop: '1rem' }}>
                          {reportBuilder.metrics.map((metric, index) => (
                            <div key={index} style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #e1e3e5', borderRadius: '4px' }}>
                              <InlineStack align="space-between">
                                <BlockStack gap="tight">
                                  <Select
                                    label="Field"
                                    options={getFieldOptions()}
                                    value={metric.field}
                                    onChange={(value) => updateMetric(index, 'field', value)}
                                  />
                                  <Select
                                    label="Aggregation"
                                    options={getAggregationsForField(metric.field)}
                                    value={metric.aggregation}
                                    onChange={(value) => updateMetric(index, 'aggregation', value)}
                                  />
                                  <TextField
                                    label="Label"
                                    value={metric.label}
                                    onChange={(value) => updateMetric(index, 'label', value)}
                                    placeholder="Custom label"
                                  />
                                </BlockStack>
                                <Button
                                  icon={DeleteMajor}
                                  destructive
                                  onClick={() => removeMetric(index)}
                                />
                              </InlineStack>
                            </div>
                          ))}
                          <Button onClick={addMetric} icon={CirclePlusMajor}>Add Metric</Button>
                        </div>
                      </Collapsible>
                    </Card>

                    {/* Group By Section */}
                    <Card sectioned>
                      <InlineStack align="space-between">
                        <Text variant="headingSm" as="h3">Group By</Text>
                        <Button
                          size="slim"
                          icon={expandedSections.groupBy ? ChevronUpMinor : ChevronDownMinor}
                          onClick={() => toggleSection('groupBy')}
                        />
                      </InlineStack>
                      
                      <Collapsible open={expandedSections.groupBy}>
                        <div style={{ marginTop: '1rem' }}>
                          <ChoiceList
                            allowMultiple
                            choices={GROUP_BY_OPTIONS}
                            selected={reportBuilder.group_by}
                            onChange={(value) => setReportBuilder(prev => ({ ...prev, group_by: value }))}
                          />
                        </div>
                      </Collapsible>
                    </Card>

                    {/* Filters Section */}
                    <Card sectioned>
                      <InlineStack align="space-between">
                        <Text variant="headingSm" as="h3">Filters</Text>
                        <Button
                          size="slim"
                          icon={expandedSections.filters ? ChevronUpMinor : ChevronDownMinor}
                          onClick={() => toggleSection('filters')}
                        />
                      </InlineStack>
                      
                      <Collapsible open={expandedSections.filters}>
                        <div style={{ marginTop: '1rem' }}>
                          {reportBuilder.filters.map((filter, index) => (
                            <div key={index} style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #e1e3e5', borderRadius: '4px' }}>
                              <InlineStack align="space-between">
                                <BlockStack gap="tight">
                                  <Select
                                    label="Field"
                                    options={getFieldOptions()}
                                    value={filter.field}
                                    onChange={(value) => updateFilter(index, 'field', value)}
                                  />
                                  <Select
                                    label="Operator"
                                    options={FILTER_OPERATORS}
                                    value={filter.operator}
                                    onChange={(value) => updateFilter(index, 'operator', value)}
                                  />
                                  <TextField
                                    label="Value"
                                    value={filter.value}
                                    onChange={(value) => updateFilter(index, 'value', value)}
                                  />
                                </BlockStack>
                                <Button
                                  icon={DeleteMajor}
                                  destructive
                                  onClick={() => removeFilter(index)}
                                />
                              </InlineStack>
                            </div>
                          ))}
                          <Button onClick={addFilter} icon={CirclePlusMajor}>Add Filter</Button>
                        </div>
                      </Collapsible>
                    </Card>

                    <ButtonGroup>
                      <Button 
                        primary 
                        onClick={() => buildReport()}
                        loading={loading}
                        disabled={reportBuilder.metrics.length === 0}
                      >
                        Generate Report
                      </Button>
                      <Button onClick={resetBuilder}>Reset</Button>
                    </ButtonGroup>
                  </BlockStack>
                </Card>
              </Layout.Section>

              <Layout.Section twoThirds>
                {loading ? (
                  <Card sectioned>
                    <div style={{ textAlign: 'center', padding: '2rem' }}>
                      <Spinner size="large" />
                      <p style={{ marginTop: '1rem' }}>Generating report...</p>
                    </div>
                  </Card>
                ) : reportResults ? (
                  renderReportResults()
                ) : (
                  <Card sectioned>
                    <EmptyState
                      heading="Build your first report"
                      image="https://cdn.shopify.com/s/files/1/0262/4071/2726/files/emptystate-files.png"
                    >
                      <p>Configure metrics, filters, and grouping options on the left to generate custom reports on your data.</p>
                    </EmptyState>
                  </Card>
                )}
              </Layout.Section>
            </Layout>
          )}

          {selectedTab === 1 && (
            <Layout>
              <Layout.Section>
                <Banner status="info">
                  <p>Use these pre-built report templates to get started quickly.</p>
                </Banner>
              </Layout.Section>
              
              <Layout.Section>
                <ResourceList
                  items={savedReports}
                  renderItem={(report, index) => (
                    <ResourceItem
                      id={index}
                      accessibilityLabel={`Report template ${report.name}`}
                    >
                      <InlineStack align="space-between" wrap={false}>
                        <BlockStack gap="200">
                          <Text variant="headingMd" as="h2">{report.name}</Text>
                          <p>{report.description}</p>
                          <Badge>{ENTITY_TYPES.find(t => t.value === report.definition.entity_type)?.label}</Badge>
                        </BlockStack>
                        <ButtonGroup>
                          <Button primary onClick={() => applyTemplate(report)}>
                            Use Template
                          </Button>
                          <Button onClick={() => {
                            setReportBuilder(report.definition);
                            buildReport();
                          }}>
                            Run Report
                          </Button>
                        </ButtonGroup>
                      </InlineStack>
                    </ResourceItem>
                  )}
                />
              </Layout.Section>
            </Layout>
          )}
        </Tabs>

        {/* Toast notifications */}
        {toast && (
          <Toast
            content={toast.content}
            error={toast.error}
            onDismiss={() => setToast(null)}
          />
        )}
      </Page>
    </Frame>
  );
};

export default ReportsBuilder;
