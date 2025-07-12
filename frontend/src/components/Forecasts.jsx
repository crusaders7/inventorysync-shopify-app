import React, { useState, useEffect } from 'react';
import { Badge, BlockStack, Button, Card, DataTable, Layout, Page, Text } from '@shopify/polaris';
import ForecastingEngine from './ForecastingEngine';
import AnalyticsChart from './AnalyticsChart';

function Forecasts({ showToast }) {
  const [forecastData, setForecastData] = useState([]);
  const [forecastChartData, setForecastChartData] = useState(null);
  const [forecastingEngine] = useState(new ForecastingEngine());

  useEffect(() => {
    fetchForecasts();
  }, []);

  const fetchForecasts = async () => {
    try {
      // Generate advanced forecast data using the forecasting engine
      const mockProducts = [
        { name: 'Blue T-Shirt (M)', currentStock: 5, salesHistory: [3, 5, 2, 4, 6, 3, 5, 4, 2, 7] },
        { name: 'Red Sneakers (42)', currentStock: 0, salesHistory: [8, 12, 15, 10, 14, 18, 16, 20, 22, 25] },
        { name: 'Green Hat', currentStock: 150, salesHistory: [2, 1, 3, 2, 1, 2, 3, 1, 2, 1] },
        { name: 'Black Jeans (32)', currentStock: 12, salesHistory: [4, 6, 5, 7, 6, 8, 5, 6, 9, 7] },
        { name: 'White Sneakers (40)', currentStock: 25, salesHistory: [10, 12, 8, 15, 18, 14, 16, 12, 20, 22] },
      ];

      const forecastResults = [];
      const chartLabels = [];
      const actualData = [];
      const forecastedData = [];

      // Generate chart data for the last 30 days + 7 days forecast
      for (let i = 29; i >= -7; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        chartLabels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        if (i >= 0) {
          // Historical data
          actualData.push(50 + Math.sin(i * 0.3) * 20 + (Math.random() - 0.5) * 15);
          forecastedData.push(null);
        } else {
          // Forecast data
          actualData.push(null);
          forecastedData.push(55 + Math.sin(-i * 0.3) * 20 + (Math.random() - 0.5) * 10);
        }
      }

      mockProducts.forEach(product => {
        const forecast = forecastingEngine.calculateDemandForecast(
          product.salesHistory.map(qty => ({ quantity: qty })), 
          7
        );

        let status = 'success';
        let recommendation = 'Optimal';
        
        if (product.currentStock <= forecast.reorderPoint) {
          status = product.currentStock === 0 ? 'critical' : 'warning';
          recommendation = product.currentStock === 0 ? 'Urgent' : 'Reorder Soon';
        } else if (product.currentStock > forecast.totalDemand * 3) {
          status = 'attention';
          recommendation = 'Overstocked';
        }

        forecastResults.push([
          product.name,
          product.currentStock.toString(),
          forecast.totalDemand.toString(),
          'Next 7 days',
          <Badge status={status}>{recommendation}</Badge>,
          `${Math.round(forecast.confidence * 100)}%`
        ]);
      });

      setForecastData(forecastResults);
      
      // Set chart data
      setForecastChartData({
        labels: chartLabels,
        datasets: [
          {
            label: 'Historical Sales',
            data: actualData,
            borderColor: 'rgb(0, 128, 96)',
            backgroundColor: 'rgba(0, 128, 96, 0.1)',
            tension: 0.4,
          },
          {
            label: 'Forecast',
            data: forecastedData,
            borderColor: 'rgb(255, 183, 76)',
            backgroundColor: 'rgba(255, 183, 76, 0.1)',
            borderDash: [5, 5],
            tension: 0.4,
          }
        ],
      });
      
    } catch (error) {
      showToast('Failed to load forecasts');
    }
  };

  const handleRunForecast = (period) => {
    showToast(`Running ${period} forecast analysis...`);
    // TODO: Implement actual forecasting
  };

  return (
    <Page 
      title="Inventory Forecasting"
      breadcrumbs={[{content: 'Dashboard', url: '/'}]}
      primaryAction={{
        content: 'Run Full Forecast',
        onAction: () => handleRunForecast('complete')
      }}
    >
      <Layout>
        {/* Forecast Chart */}
        <Layout.Section>
          {forecastChartData && (
            <AnalyticsChart 
              type="line"
              title="Sales Forecast Analysis"
              data={forecastChartData}
              height={350}
            />
          )}
        </Layout.Section>

        <Layout.Section>
          <Card>
            <div style={{padding: '20px'}}>
              <Text variant="headingMd" as="h2">Demand Forecasts</Text>
              <div style={{marginTop: '16px'}}>
                <DataTable
                  columnContentTypes={['text', 'numeric', 'numeric', 'text', 'text', 'text']}
                  headings={['Product', 'Current Stock', 'Predicted Demand', 'Time Period', 'Recommendation', 'Confidence']}
                  rows={forecastData}
                />
              </div>
            </div>
          </Card>
        </Layout.Section>

        <Layout.Section secondary>
          <Card>
            <div style={{padding: '20px'}}>
              <BlockStack gap="400">
                <Text variant="headingMd" as="h2">Forecast Options</Text>
                <Button 
                  fullWidth 
                  onClick={() => handleRunForecast('7-day')}
                  outline
                >
                  7-Day Forecast
                </Button>
                <Button 
                  fullWidth 
                  onClick={() => handleRunForecast('30-day')}
                  outline
                >
                  30-Day Forecast
                </Button>
                <Button 
                  fullWidth 
                  onClick={() => handleRunForecast('seasonal')}
                  outline
                >
                  Seasonal Analysis
                </Button>
                <div style={{marginTop: '20px', padding: '16px', backgroundColor: '#f1f2f3', borderRadius: '8px'}}>
                  <Text variant="bodyMd" color="subdued">
                    Forecasts are based on sales history, seasonal trends, and market data. 
                    Enable "Advanced Forecasting" in Settings for ML-powered predictions.
                  </Text>
                </div>
              </BlockStack>
            </div>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}

export default Forecasts;