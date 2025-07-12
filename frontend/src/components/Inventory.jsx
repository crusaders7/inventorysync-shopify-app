import React, { useState, useEffect } from 'react';
import { Badge, BlockStack, Button, Card, DataTable, Layout, Page, Select, TextField } from '@shopify/polaris';
import ReactSelect from 'react-select';

function Inventory({ showToast }) {
  const [searchValue, setSearchValue] = useState('');
  const [locationFilter, setLocationFilter] = useState('all');
  const [inventory, setInventory] = useState([]);
  const [categoryFilter, setCategoryFilter] = useState(null);
  const [statusFilter, setStatusFilter] = useState(null);
  const [supplierFilter, setSupplierFilter] = useState(null);

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    try {
      const params = new URLSearchParams();
      if (searchValue) params.append('search', searchValue);
      if (locationFilter && locationFilter !== 'all') params.append('location', locationFilter);
      
      const url = `http://localhost:8000/api/v1/inventory/?${params.toString()}`;
      const response = await fetch(url);
      const data = await response.json();
      
      // Transform API data for DataTable
      const tableData = data.items.map(item => [
        item.product_name,
        item.sku || 'N/A',
        item.current_stock.toString(),
        item.reorder_point.toString(),
        item.location_name || 'Main Location',
        <Badge status={getStockStatus(item.status)}>{getStatusText(item.status)}</Badge>
      ]);
      
      setInventory(tableData);
    } catch (error) {
      console.error('Failed to fetch inventory:', error);
      showToast('Failed to load inventory data');
    }
  };

  const getStockStatus = (status) => {
    switch (status) {
      case 'out_of_stock': return 'critical';
      case 'low_stock': return 'warning';
      case 'overstock': return 'attention';
      default: return 'success';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'out_of_stock': return 'Out of Stock';
      case 'low_stock': return 'Low Stock';
      case 'overstock': return 'Overstock';
      default: return 'In Stock';
    }
  };

  const handleSearchChange = (value) => {
    setSearchValue(value);
  };

  const handleLocationChange = (value) => {
    setLocationFilter(value);
  };

  // Auto-fetch when filters change
  useEffect(() => {
    fetchInventory();
  }, [searchValue, locationFilter, categoryFilter, statusFilter, supplierFilter]);

  const locationOptions = [
    { label: 'All Locations', value: 'all' },
    { label: 'Warehouse A', value: 'Warehouse A' },
    { label: 'Warehouse B', value: 'Warehouse B' },
  ];

  const categoryOptions = [
    { value: 'clothing', label: 'Clothing' },
    { value: 'electronics', label: 'Electronics' },
    { value: 'home', label: 'Home & Garden' },
    { value: 'sports', label: 'Sports' },
    { value: 'books', label: 'Books' },
  ];

  const statusOptions = [
    { value: 'in_stock', label: 'In Stock' },
    { value: 'low_stock', label: 'Low Stock' },
    { value: 'out_of_stock', label: 'Out of Stock' },
    { value: 'discontinued', label: 'Discontinued' },
  ];

  const supplierOptions = [
    { value: 'fashioncorp', label: 'FashionCorp' },
    { value: 'shoeco', label: 'ShoeCo' },
    { value: 'electronicsplus', label: 'ElectronicsPlus' },
    { value: 'homegoods', label: 'HomeGoods' },
  ];

  const customSelectStyles = {
    control: (provided) => ({
      ...provided,
      minHeight: '36px',
      borderColor: '#c9cccf',
      fontSize: '14px',
    }),
    placeholder: (provided) => ({
      ...provided,
      color: '#6d7175',
    }),
  };

  return (
    <Page 
      title="Inventory Management"
      breadcrumbs={[{content: 'Dashboard', url: '/'}]}
      primaryAction={{
        content: 'Add Product',
        onAction: () => showToast('Add product feature coming soon!')
      }}
    >
      <Layout>
        <Layout.Section>
          <Card>
            <div style={{padding: '20px'}}>
              <BlockStack vertical spacing="loose">
                <TextField
                  label="Search products"
                  value={searchValue}
                  onChange={handleSearchChange}
                  placeholder="Search by name or SKU..."
                />
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '600' }}>
                      Category
                    </label>
                    <ReactSelect
                      options={categoryOptions}
                      value={categoryFilter}
                      onChange={setCategoryFilter}
                      placeholder="Select category..."
                      isClearable
                      styles={customSelectStyles}
                    />
                  </div>
                  
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '600' }}>
                      Status
                    </label>
                    <ReactSelect
                      options={statusOptions}
                      value={statusFilter}
                      onChange={setStatusFilter}
                      placeholder="Select status..."
                      isClearable
                      styles={customSelectStyles}
                    />
                  </div>
                  
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '600' }}>
                      Supplier
                    </label>
                    <ReactSelect
                      options={supplierOptions}
                      value={supplierFilter}
                      onChange={setSupplierFilter}
                      placeholder="Select supplier..."
                      isClearable
                      styles={customSelectStyles}
                    />
                  </div>
                  
                  <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '600' }}>
                      Location
                    </label>
                    <ReactSelect
                      options={locationOptions.slice(1)}
                      value={locationFilter === 'all' ? null : locationOptions.find(opt => opt.value === locationFilter)}
                      onChange={(option) => setLocationFilter(option ? option.value : 'all')}
                      placeholder="Select location..."
                      isClearable
                      styles={customSelectStyles}
                    />
                  </div>
                </div>
                
                <Button 
                  onClick={() => {
                    setSearchValue('');
                    setCategoryFilter(null);
                    setStatusFilter(null);
                    setSupplierFilter(null);
                    setLocationFilter('all');
                  }}
                  outline
                >
                  Clear All Filters
                </Button>
              </BlockStack>
            </div>
            
            <div style={{padding: '0 20px 20px'}}>
              <DataTable
                columnContentTypes={['text', 'text', 'numeric', 'numeric', 'text', 'text']}
                headings={[
                  'Product Name',
                  'SKU',
                  'Current Stock',
                  'Reorder Point',
                  'Location',
                  'Status'
                ]}
                rows={inventory}
              />
            </div>
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}

export default Inventory;