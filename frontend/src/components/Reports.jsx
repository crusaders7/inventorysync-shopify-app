import React, { useState, useEffect } from 'react';
import { Badge, BlockStack, Button, Card, DataTable, Layout, Page, Text } from '@shopify/polaris';
import { CSVLink } from 'react-csv';

function Reports({ showToast }) {
  const [reportData, setReportData] = useState([]);
  const [csvData, setCsvData] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      // Generate mock report data
      const mockReports = [
        ['Low Stock Report', '23 items below reorder point', 'Today', <Badge status="warning">Action Needed</Badge>],
        ['Sales Velocity', 'Top 10 fastest moving products', 'Yesterday', <Badge status="success">Complete</Badge>],
        ['Inventory Value', 'Total value: $125,430', 'This Week', <Badge status="info">Ready</Badge>],
        ['Dead Stock', '5 items with no sales in 90 days', 'This Month', <Badge status="attention">Review</Badge>],
      ];
      
      setReportData(mockReports);
    } catch (error) {
      showToast('Failed to load reports');
    }
  };

  const handleGenerateReport = (reportType) => {
    showToast(`Generating ${reportType} report...`);
    setSelectedReport(reportType);
    
    // Generate actual report data based on type
    const reportData = generateReportData(reportType);
    setCsvData(reportData);
  };

  const generateReportData = (reportType) => {
    const headers = getReportHeaders(reportType);
    const data = getReportData(reportType);
    
    return [headers, ...data];
  };

  const getReportHeaders = (reportType) => {
    switch (reportType) {
      case 'Low Stock':
        return ['Product Name', 'SKU', 'Current Stock', 'Reorder Point', 'Status', 'Supplier'];
      case 'Sales Velocity':
        return ['Product Name', 'SKU', 'Units Sold (30 days)', 'Revenue', 'Velocity', 'Category'];
      case 'Dead Stock':
        return ['Product Name', 'SKU', 'Current Stock', 'Last Sale Date', 'Days Since Sale', 'Value'];
      case 'Inventory Value':
        return ['Product Name', 'SKU', 'Quantity', 'Unit Cost', 'Total Value', 'Category'];
      default:
        return ['Product Name', 'SKU', 'Quantity', 'Value'];
    }
  };

  const getReportData = (reportType) => {
    switch (reportType) {
      case 'Low Stock':
        return [
          ['Blue T-Shirt (M)', 'TSH-BLU-M', '5', '20', 'Critical', 'FashionCorp'],
          ['Red Sneakers (42)', 'SNK-RED-42', '2', '15', 'Low', 'ShoeCo'],
          ['Green Hat', 'HAT-GRN-001', '8', '25', 'Low', 'AccessoryInc'],
          ['Black Jeans (32)', 'JNS-BLK-32', '12', '30', 'Warning', 'DenimPlus'],
        ];
      case 'Sales Velocity':
        return [
          ['Blue T-Shirt (M)', 'TSH-BLU-M', '156', '$3,120', 'High', 'Clothing'],
          ['Red Sneakers (42)', 'SNK-RED-42', '89', '$8,900', 'High', 'Footwear'],
          ['Wireless Headphones', 'HDR-WLS-001', '67', '$6,700', 'Medium', 'Electronics'],
          ['Coffee Mug', 'MUG-COF-001', '234', '$2,340', 'High', 'Home'],
        ];
      case 'Dead Stock':
        return [
          ['Vintage Lamp', 'LMP-VNT-001', '15', '2024-01-15', '145', '$1,500'],
          ['Retro Phone', 'PHN-RET-001', '8', '2023-12-20', '171', '$800'],
          ['Old Calculator', 'CAL-OLD-001', '22', '2024-02-01', '128', '$660'],
          ['Antique Clock', 'CLK-ANT-001', '5', '2023-11-30', '191', '$2,500'],
        ];
      case 'Inventory Value':
        return [
          ['Blue T-Shirt (M)', 'TSH-BLU-M', '156', '$15.00', '$2,340', 'Clothing'],
          ['Red Sneakers (42)', 'SNK-RED-42', '89', '$75.00', '$6,675', 'Footwear'],
          ['Wireless Headphones', 'HDR-WLS-001', '67', '$120.00', '$8,040', 'Electronics'],
          ['Coffee Mug', 'MUG-COF-001', '234', '$8.00', '$1,872', 'Home'],
        ];
      default:
        return [];
    }
  };

  return (
    <Page 
      title="Inventory Reports"
      breadcrumbs={[{content: 'Dashboard', url: '/'}]}
      primaryAction={{
        content: 'Generate Custom Report',
        onAction: () => showToast('Custom report builder coming soon!')
      }}
    >
      <Layout>
        <Layout.Section>
          <Card>
            <div style={{padding: '20px'}}>
              <Text variant="headingMd" as="h2">Available Reports</Text>
              <div style={{marginTop: '16px'}}>
                <DataTable
                  columnContentTypes={['text', 'text', 'text', 'text']}
                  headings={['Report Name', 'Description', 'Last Generated', 'Status']}
                  rows={reportData}
                />
              </div>
            </div>
          </Card>
        </Layout.Section>

        <Layout.Section secondary>
          <Card>
            <div style={{padding: '20px'}}>
              <BlockStack vertical spacing="loose">
                <Text variant="headingMd" as="h2">Quick Reports</Text>
                <Button 
                  fullWidth 
                  onClick={() => handleGenerateReport('Low Stock')}
                  outline
                >
                  Low Stock Items
                </Button>
                <Button 
                  fullWidth 
                  onClick={() => handleGenerateReport('Sales Velocity')}
                  outline
                >
                  Sales Velocity Analysis
                </Button>
                <Button 
                  fullWidth 
                  onClick={() => handleGenerateReport('Dead Stock')}
                  outline
                >
                  Dead Stock Report
                </Button>
                <Button 
                  fullWidth 
                  onClick={() => handleGenerateReport('Inventory Value')}
                  outline
                >
                  Inventory Valuation
                </Button>
                
                {csvData.length > 0 && (
                  <CSVLink
                    data={csvData}
                    filename={`${selectedReport}-report-${new Date().toISOString().split('T')[0]}.csv`}
                    style={{ textDecoration: 'none' }}
                  >
                    <Button fullWidth primary>
                      Download {selectedReport} Report (CSV)
                    </Button>
                  </CSVLink>
                )}
              </BlockStack>
            </div>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}

export default Reports;