import React, { useState, useEffect } from 'react';
import { Badge, Banner, BlockStack, Button, ButtonGroup, Card, DataTable, InlineStack, InlineStack Page, Layout, List, Loading, Modal, Page, ProgressBar, Select, Text, TextContainer, TextField, Tooltip } from '@shopify/polaris';
import {
  AnalyticsMajor,
  TrendingUpMajor,
  AlertMajor,
  ExportIcon,
  RefreshMajor
} from '@shopify/polaris-icons';

const ForecastingDashboard = ({ shop, showToast }) => {
  const [forecasts, setForecasts] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showProductDetail, setShowProductDetail] = useState(false);
  const [forecastDays, setForecastDays] = useState('30');
  const [sensitivity, setSensitivity] = useState('2.5');

  const forecastDaysOptions = [
    { label: '7 days', value: '7' },
    { label: '14 days', value: '14' },
    { label: '30 days', value: '30' },
    { label: '60 days', value: '60' },
    { label: '90 days', value: '90' }
  ];

  const sensitivityOptions = [
    { label: 'Low (1.0)', value: '1.0' },
    { label: 'Medium (2.5)', value: '2.5' },
    { label: 'High (4.0)', value: '4.0' }
  ];

  useEffect(() => {
    loadForecastingData();
  }, [forecastDays, sensitivity]);

  const loadForecastingData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchForecasts(),
        fetchAnomalies(),
        fetchInsights()
      ]);
    } catch (error) {
      console.error('Failed to load forecasting data:', error);
      showToast('Failed to load forecasting data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchForecasts = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/forecasting/all-products?shop=${encodeURIComponent(shop)}&days_ahead=${forecastDays}&limit=20`
      );
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Forecasting not available in your current plan');
        }
        throw new Error('Failed to fetch forecasts');
      }
      
      const data = await response.json();
      setForecasts(data.forecasts || []);
    } catch (error) {
      console.error('Failed to fetch forecasts:', error);
      throw error;
    }
  };

  const fetchAnomalies = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/forecasting/anomalies?shop=${encodeURIComponent(shop)}&sensitivity=${sensitivity}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setAnomalies(data.anomalies || []);
      }
    } catch (error) {
      console.error('Failed to fetch anomalies:', error);
    }
  };

  const fetchInsights = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/forecasting/insights?shop=${encodeURIComponent(shop)}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setInsights(data);
      }
    } catch (error) {
      console.error('Failed to fetch insights:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadForecastingData();
      showToast('Forecasting data refreshed', 'success');
    } catch (error) {
      showToast('Failed to refresh data', 'error');
    } finally {
      setRefreshing(false);
    }
  };

  const handleProductDetail = async (productId) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/forecasting/product/${productId}?shop=${encodeURIComponent(shop)}&days_ahead=${forecastDays}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setSelectedProduct(data);
        setShowProductDetail(true);
      } else {
        throw new Error('Failed to fetch product forecast');
      }
    } catch (error) {
      console.error('Failed to fetch product detail:', error);
      showToast('Failed to load product forecast', 'error');
    }
  };

  const getConfidenceBadge = (confidence) => {
    if (confidence >= 0.8) return <Badge status="success">High Confidence</Badge>;
    if (confidence >= 0.6) return <Badge status="warning">Medium Confidence</Badge>;
    return <Badge status="critical">Low Confidence</Badge>;
  };

  const getUrgencyBadge = (daysOfSupply) => {
    if (daysOfSupply < 7) return <Badge status="critical">Critical</Badge>;
    if (daysOfSupply < 14) return <Badge status="warning">Low</Badge>;
    if (daysOfSupply > 90) return <Badge status="attention">Overstocked</Badge>;
    return <Badge status="success">Normal</Badge>;
  };

  const forecastRows = forecasts.map((forecast) => [
    forecast.product?.title || 'Unknown Product',
    forecast.product?.sku || '-',
    Math.round(forecast.forecast || 0),
    `${forecast.inventory?.current || 0}`,
    forecast.inventory?.days_of_supply ? `${forecast.inventory.days_of_supply} days` : '-',
    getConfidenceBadge(forecast.confidence || 0),
    getUrgencyBadge(forecast.inventory?.days_of_supply || 999),
    <Button
      size="slim"
      onClick={() => handleProductDetail(forecast.product?.id)}
    >
      View Details
    </Button>
  ]);

  const anomalyRows = anomalies.map((anomaly) => [
    anomaly.product_title,
    anomaly.type === 'sales_spike' ? 'Sales Spike' : 'Sales Drop',
    `${anomaly.deviation_percentage > 0 ? '+' : ''}${anomaly.deviation_percentage}%`,
    anomaly.severity === 'high' ? <Badge status="critical">High</Badge> : <Badge status="warning">Medium</Badge>,
    anomaly.recommendation
  ]);

  if (loading) {
    return (
      <Page title="AI Forecasting">
        <Layout>
          <Layout.Section>
            <Card>
              <div style={{ padding: '60px', textAlign: 'center' }}>
                <Loading />
                <Text>Loading forecasting data...</Text>
              </div>
            </Card>
          </Layout.Section>
        </Layout>
      </Page>
    );
  }

  return (
    <Page
      title="AI Forecasting"
      subtitle="Predict demand and optimize inventory with machine learning"
      primaryAction={{
        content: refreshing ? 'Refreshing...' : 'Refresh Data',
        onAction: handleRefresh,
        loading: refreshing,
        icon: RefreshMajor
      }}
    >
      <Layout>
        {/* Controls */}
        <Layout.Section>
          <Card sectioned>
            <InlineStack gap="400">
              <InlineStack gap="500">
                <Select
                  label="Forecast Period"
                  options={forecastDaysOptions}
                  value={forecastDays}
                  onChange={setForecastDays}
                />
                <Select
                  label="Anomaly Sensitivity"
                  options={sensitivityOptions}
                  value={sensitivity}
                  onChange={setSensitivity}
                />
              </BlockStack>
              <ButtonGroup>
                <Button icon={ExportIcon}>Export Report</Button>
                <Button primary icon={AnalyticsMajor}>
                  Generate Insights
                </Button>
              </ButtonGroup>
            </BlockStack>
          </Card>
        </Layout.Section>

        {/* Overview Cards */}
        {insights && (
          <Layout.Section>
            <Layout.Section secondary>
              <BlockStack gap="200">
                <Card>
                  <div style={{ padding: '16px' }}>
                    <BlockStack gap="100">
                      <Text variant="headingLg" color="success">
                        {insights.overview?.low_stock_items || 0}
                      </Text>
                      <Text variant="bodySm" color="subdued">
                        Items Need Reordering
                      </Text>
                    </BlockStack>
                  </div>
                </Card>
                
                <Card>
                  <div style={{ padding: '16px' }}>
                    <BlockStack gap="100">
                      <Text variant="headingLg" color="warning">
                        {insights.overview?.overstock_items || 0}
                      </Text>
                      <Text variant="bodySm" color="subdued">
                        Overstocked Items
                      </Text>
                    </BlockStack>
                  </div>
                </Card>

                <Card>
                  <div style={{ padding: '16px' }}>
                    <BlockStack gap="100">
                      <Text variant="headingLg">
                        {insights.trends?.trend_percentage > 0 ? '+' : ''}{insights.trends?.trend_percentage || 0}%
                      </Text>
                      <Text variant="bodySm" color="subdued">
                        Sales Trend
                      </Text>
                    </BlockStack>
                  </div>
                </Card>
              </BlockStack>
            </Layout.Section>

            <Layout.Section>
              <Card sectioned title="AI Recommendations">
                <BlockStack gap="200">
                  {insights.recommendations?.map((rec, index) => (
                    <Banner
                      key={index}
                      status={rec.priority === 'high' ? 'critical' : rec.priority === 'medium' ? 'warning' : 'info'}
                    >
                      <p><strong>{rec.message}</strong></p>
                      <p>{rec.action}</p>
                    </Banner>
                  ))}
                  {insights.trends?.seasonal_alert && (
                    <Banner status="info">
                      <p>{insights.trends.seasonal_alert}</p>
                    </Banner>
                  )}
                </BlockStack>
              </Card>
            </Layout.Section>
          </Layout.Section>
        )}

        {/* Forecasts Table */}
        <Layout.Section>
          <Card>
            <DataTable
              columnContentTypes={['text', 'text', 'numeric', 'numeric', 'text', 'text', 'text', 'text']}
              headings={[
                'Product',
                'SKU',
                `Forecast (${forecastDays} days)`,
                'Current Stock',
                'Days of Supply',
                'Confidence',
                'Status',
                'Actions'
              ]}
              rows={forecastRows}
              pagination={{
                hasNext: false,
                hasPrevious: false,
                onNext: () => {},
                onPrevious: () => {}
              }}
            />
            {forecasts.length === 0 && (
              <div style={{ padding: '40px', textAlign: 'center' }}>
                <Text color="subdued">
                  No forecast data available. Make sure you have sales history and active products.
                </Text>
              </div>
            )}
          </Card>
        </Layout.Section>

        {/* Anomalies */}
        {anomalies.length > 0 && (
          <Layout.Section>
            <Card title="Sales Anomalies Detected">
              <DataTable
                columnContentTypes={['text', 'text', 'text', 'text', 'text']}
                headings={[
                  'Product',
                  'Anomaly Type',
                  'Deviation',
                  'Severity',
                  'Recommendation'
                ]}
                rows={anomalyRows}
              />
            </Card>
          </Layout.Section>
        )}
      </Layout>

      {/* Product Detail Modal */}
      <Modal
        open={showProductDetail}
        onClose={() => setShowProductDetail(false)}
        title={selectedProduct?.product?.title || 'Product Forecast'}
        large
      >
        {selectedProduct && (
          <Modal.Section>
            <BlockStack gap="500">
              <Layout>
                <Layout.Section oneThird>
                  <Card sectioned title="Forecast Summary">
                    <BlockStack gap="200">
                      <div>
                        <Text variant="headingLg">{Math.round(selectedProduct.forecast || 0)}</Text>
                        <Text variant="bodySm" color="subdued">Units forecasted</Text>
                      </div>
                      <div>
                        <Text variant="bodyLg">{selectedProduct.inventory?.current || 0}</Text>
                        <Text variant="bodySm" color="subdued">Current inventory</Text>
                      </div>
                      <div>
                        <Text variant="bodyLg">{selectedProduct.inventory?.days_of_supply || 0} days</Text>
                        <Text variant="bodySm" color="subdued">Days of supply</Text>
                      </div>
                    </BlockStack>
                  </Card>
                </Layout.Section>

                <Layout.Section>
                  <Card sectioned title="Forecast Details">
                    <BlockStack gap="200">
                      <div>
                        <Text variant="headingSm">Confidence: {getConfidenceBadge(selectedProduct.confidence)}</Text>
                        <ProgressBar progress={selectedProduct.confidence * 100} size="small" />
                      </div>
                      
                      <div>
                        <Text variant="bodySm" color="subdued">Method: {selectedProduct.method}</Text>
                      </div>

                      {selectedProduct.confidence_interval && (
                        <div>
                          <Text variant="bodySm">
                            Range: {Math.round(selectedProduct.confidence_interval.lower)} - {Math.round(selectedProduct.confidence_interval.upper)} units
                          </Text>
                        </div>
                      )}

                      {selectedProduct.metrics && (
                        <div>
                          <Text variant="bodySm">
                            Avg Daily Sales: {selectedProduct.metrics.avg_daily_sales}
                          </Text>
                          <Text variant="bodySm">
                            Trend: {selectedProduct.metrics.trend > 0 ? '↗️ Increasing' : selectedProduct.metrics.trend < 0 ? '↘️ Decreasing' : '➡️ Stable'}
                          </Text>
                        </div>
                      )}
                    </BlockStack>
                  </Card>
                </Layout.Section>
              </Layout>

              {selectedProduct.recommendations && selectedProduct.recommendations.length > 0 && (
                <Card sectioned title="Recommendations">
                  <List>
                    {selectedProduct.recommendations.map((rec, index) => (
                      <List.Item key={index}>{rec}</List.Item>
                    ))}
                  </List>
                </Card>
              )}
            </BlockStack>
          </Modal.Section>
        )}
      </Modal>
    </Page>
  );
};

export default ForecastingDashboard;