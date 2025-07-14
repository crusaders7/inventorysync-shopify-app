import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  DataTable,
  Button,
  Stack,
  TextField,
  Select,
  Filters,
  ChoiceList,
  Badge,
  Banner,
  Modal,
  TextContainer,
  Heading,
  ButtonGroup,
  Checkbox,
  Icon,
  Tooltip,
  Pagination,
  ResourceList,
  ResourceItem,
  Thumbnail,
  TextStyle
} from '@shopify/polaris';
import {
  ImportIcon,
  ExportIcon,
  SaveIcon,
  EditIcon,
  SearchIcon,
  FilterIcon,
  CheckIcon,
  XIcon
} from '@shopify/polaris-icons';
import { useAuthenticatedFetch } from '../hooks/useAuthenticatedFetch';
import debounce from 'lodash.debounce';

const BulkMetafieldEditor = () => {
  const fetch = useAuthenticatedFetch();
  const [products, setProducts] = useState([]);
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [metafieldDefinitions, setMetafieldDefinitions] = useState([]);
  const [editingCells, setEditingCells] = useState({});
  const [changes, setChanges] = useState({});
  const [filters, setFilters] = useState({
    query: '',
    productType: [],
    vendor: [],
    status: []
  });
  const [showImportModal, setShowImportModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showSuccess, setShowSuccess] = useState(false);
  const [errors, setErrors] = useState({});

  const ITEMS_PER_PAGE = 50;

  // Load products and metafield definitions
  useEffect(() => {
    loadProducts();
    loadMetafieldDefinitions();
  }, [currentPage, filters]);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage,
        limit: ITEMS_PER_PAGE,
        ...filters
      });

      const response = await fetch(`/api/v1/products/bulk-metafields?${params}`);
      const data = await response.json();
      
      setProducts(data.products || []);
      setTotalPages(Math.ceil(data.total / ITEMS_PER_PAGE));
    } catch (error) {
      console.error('Error loading products:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMetafieldDefinitions = async () => {
    try {
      const response = await fetch('/api/v1/metafields/definitions');
      const data = await response.json();
      setMetafieldDefinitions(data.definitions || []);
    } catch (error) {
      console.error('Error loading metafield definitions:', error);
    }
  };

  // Handle cell editing
  const handleCellEdit = (productId, metafieldKey, value) => {
    setEditingCells(prev => ({
      ...prev,
      [`${productId}-${metafieldKey}`]: value
    }));

    setChanges(prev => ({
      ...prev,
      [productId]: {
        ...prev[productId],
        [metafieldKey]: value
      }
    }));
  };

  // Save changes
  const saveChanges = async () => {
    setSaving(true);
    setErrors({});

    const bulkUpdates = Object.entries(changes).map(([productId, fields]) => ({
      product_id: productId,
      metafields: Object.entries(fields).map(([key, value]) => ({
        namespace: 'custom',
        key,
        value,
        type: getFieldType(key)
      }))
    }));

    try {
      const response = await fetch('/api/v1/metafields/bulk-update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ updates: bulkUpdates })
      });

      if (response.ok) {
        setShowSuccess(true);
        setTimeout(() => setShowSuccess(false), 3000);
        setChanges({});
        setEditingCells({});
        await loadProducts();
      } else {
        const error = await response.json();
        setErrors({ save: error.message });
      }
    } catch (error) {
      setErrors({ save: 'Failed to save changes' });
    } finally {
      setSaving(false);
    }
  };

  // Get field type from definition
  const getFieldType = (key) => {
    const definition = metafieldDefinitions.find(def => def.key === key);
    return definition?.type || 'single_line_text_field';
  };

  // Export data
  const exportData = async () => {
    const exportProducts = selectedProducts.length > 0 
      ? products.filter(p => selectedProducts.includes(p.id))
      : products;

    const csvData = convertToCSV(exportProducts);
    downloadCSV(csvData, 'product-metafields.csv');
  };

  // Convert to CSV
  const convertToCSV = (data) => {
    if (data.length === 0) return '';

    // Get all unique metafield keys
    const metafieldKeys = new Set();
    data.forEach(product => {
      Object.keys(product.metafields || {}).forEach(key => metafieldKeys.add(key));
    });

    // Create headers
    const headers = ['Product ID', 'Title', 'SKU', 'Product Type', 'Vendor', ...Array.from(metafieldKeys)];
    
    // Create rows
    const rows = data.map(product => {
      const row = [
        product.id,
        product.title,
        product.sku || '',
        product.product_type || '',
        product.vendor || ''
      ];

      Array.from(metafieldKeys).forEach(key => {
        row.push(product.metafields?.[key] || '');
      });

      return row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',');
    });

    return [headers.join(','), ...rows].join('\n');
  };

  // Download CSV
  const downloadCSV = (csvContent, filename) => {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  // Import CSV
  const handleImport = async (file) => {
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const csvData = e.target.result;
        const parsedData = parseCSV(csvData);
        
        const response = await fetch('/api/v1/metafields/import', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ data: parsedData })
        });

        if (response.ok) {
          setShowImportModal(false);
          await loadProducts();
          setShowSuccess(true);
          setTimeout(() => setShowSuccess(false), 3000);
        } else {
          const error = await response.json();
          setErrors({ import: error.message });
        }
      } catch (error) {
        setErrors({ import: 'Failed to parse CSV file' });
      }
    };
    reader.readAsText(file);
  };

  // Parse CSV
  const parseCSV = (csvText) => {
    const lines = csvText.split('\n');
    const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
    
    const data = [];
    for (let i = 1; i < lines.length; i++) {
      if (lines[i].trim()) {
        const values = lines[i].match(/(".*?"|[^,]+)/g).map(v => v.trim().replace(/^"|"$/g, ''));
        const row = {};
        headers.forEach((header, index) => {
          row[header] = values[index] || '';
        });
        data.push(row);
      }
    }
    
    return data;
  };

  // Filter handlers
  const handleQueryChange = useCallback(
    debounce((value) => {
      setFilters(prev => ({ ...prev, query: value }));
      setCurrentPage(1);
    }, 500),
    []
  );

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  // Clear filters
  const clearFilters = () => {
    setFilters({
      query: '',
      productType: [],
      vendor: [],
      status: []
    });
    setCurrentPage(1);
  };

  // Build data table
  const buildDataTable = () => {
    const rows = products.map(product => {
      const row = [
        <Checkbox
          checked={selectedProducts.includes(product.id)}
          onChange={(checked) => {
            if (checked) {
              setSelectedProducts(prev => [...prev, product.id]);
            } else {
              setSelectedProducts(prev => prev.filter(id => id !== product.id));
            }
          }}
        />,
        <Stack spacing="tight" alignment="center">
          {product.image && (
            <Thumbnail source={product.image} alt={product.title} size="small" />
          )}
          <TextStyle variation="strong">{product.title}</TextStyle>
        </Stack>,
        product.sku || '—',
        product.product_type || '—',
        product.vendor || '—'
      ];

      // Add metafield columns
      metafieldDefinitions.forEach(def => {
        const cellKey = `${product.id}-${def.key}`;
        const currentValue = editingCells[cellKey] !== undefined 
          ? editingCells[cellKey] 
          : product.metafields?.[def.key] || '';
        
        const hasChanges = changes[product.id]?.[def.key] !== undefined;

        row.push(
          <div style={{ position: 'relative' }}>
            <TextField
              value={currentValue}
              onChange={(value) => handleCellEdit(product.id, def.key, value)}
              placeholder="—"
              connectedRight={hasChanges && <Icon source={EditIcon} color="highlight" />}
            />
          </div>
        );
      });

      return row;
    });

    const headings = [
      '',
      'Product',
      'SKU',
      'Type',
      'Vendor',
      ...metafieldDefinitions.map(def => (
        <Tooltip content={def.description || def.key}>
          <span>{def.name || def.key}</span>
        </Tooltip>
      ))
    ];

    return { rows, headings };
  };

  const { rows, headings } = buildDataTable();
  const hasChanges = Object.keys(changes).length > 0;

  return (
    <Stack vertical>
      {showSuccess && (
        <Banner status="success" onDismiss={() => setShowSuccess(false)}>
          Changes saved successfully!
        </Banner>
      )}

      {errors.save && (
        <Banner status="critical" onDismiss={() => setErrors(prev => ({ ...prev, save: null }))}>
          {errors.save}
        </Banner>
      )}

      <Card>
        <Card.Section>
          <Stack distribution="equalSpacing" alignment="center">
            <TextContainer>
              <Heading>Bulk Edit Metafields</Heading>
              <p>Edit multiple product metafields in a spreadsheet-like interface</p>
            </TextContainer>
            <ButtonGroup>
              <Button
                icon={ImportIcon}
                onClick={() => setShowImportModal(true)}
              >
                Import CSV
              </Button>
              <Button
                icon={ExportIcon}
                onClick={exportData}
                disabled={products.length === 0}
              >
                Export {selectedProducts.length > 0 ? `${selectedProducts.length} Selected` : 'All'}
              </Button>
              <Button
                icon={SaveIcon}
                primary
                onClick={saveChanges}
                loading={saving}
                disabled={!hasChanges}
              >
                Save Changes ({Object.keys(changes).length})
              </Button>
            </ButtonGroup>
          </Stack>
        </Card.Section>

        <Card.Section>
          <Filters
            queryValue={filters.query}
            onQueryChange={handleQueryChange}
            onQueryClear={() => handleQueryChange('')}
            onClearAll={clearFilters}
            filters={[
              {
                key: 'productType',
                label: 'Product type',
                filter: (
                  <ChoiceList
                    title="Product type"
                    titleHidden
                    choices={[
                      { label: 'T-Shirts', value: 't-shirts' },
                      { label: 'Accessories', value: 'accessories' },
                      { label: 'Gift Cards', value: 'gift-cards' }
                    ]}
                    selected={filters.productType}
                    onChange={(value) => handleFilterChange('productType', value)}
                    allowMultiple
                  />
                ),
                shortcut: true
              },
              {
                key: 'vendor',
                label: 'Vendor',
                filter: (
                  <ChoiceList
                    title="Vendor"
                    titleHidden
                    choices={[
                      { label: 'Vendor A', value: 'vendor-a' },
                      { label: 'Vendor B', value: 'vendor-b' },
                      { label: 'Vendor C', value: 'vendor-c' }
                    ]}
                    selected={filters.vendor}
                    onChange={(value) => handleFilterChange('vendor', value)}
                    allowMultiple
                  />
                ),
                shortcut: true
              }
            ]}
          />
        </Card.Section>

        <Card.Section flush>
          {loading ? (
            <Stack distribution="center" vertical>
              <Spinner />
              <p>Loading products...</p>
            </Stack>
          ) : (
            <>
              <div style={{ overflowX: 'auto' }}>
                <DataTable
                  columnContentTypes={[
                    'text',
                    'text',
                    'text',
                    'text',
                    'text',
                    ...metafieldDefinitions.map(() => 'text')
                  ]}
                  headings={headings}
                  rows={rows}
                  hasZebraStriping
                />
              </div>
              
              {totalPages > 1 && (
                <div style={{ padding: '16px', borderTop: '1px solid #e1e3e5' }}>
                  <Stack distribution="center">
                    <Pagination
                      hasPrevious={currentPage > 1}
                      hasNext={currentPage < totalPages}
                      onPrevious={() => setCurrentPage(prev => prev - 1)}
                      onNext={() => setCurrentPage(prev => prev + 1)}
                    />
                  </Stack>
                </div>
              )}
            </>
          )}
        </Card.Section>
      </Card>

      <Modal
        open={showImportModal}
        onClose={() => setShowImportModal(false)}
        title="Import Metafields from CSV"
        primaryAction={{
          content: 'Import',
          onAction: () => {
            const input = document.getElementById('csv-upload');
            if (input?.files?.[0]) {
              handleImport(input.files[0]);
            }
          }
        }}
        secondaryActions={[
          {
            content: 'Cancel',
            onAction: () => setShowImportModal(false)
          }
        ]}
      >
        <Modal.Section>
          <Stack vertical>
            <TextContainer>
              <p>Upload a CSV file with product metafields. The CSV should have columns for Product ID and metafield values.</p>
            </TextContainer>
            <input
              type="file"
              id="csv-upload"
              accept=".csv"
              style={{
                padding: '8px',
                border: '1px solid #c4cdd5',
                borderRadius: '4px',
                width: '100%'
              }}
            />
            {errors.import && (
              <Banner status="critical">
                {errors.import}
              </Banner>
            )}
          </Stack>
        </Modal.Section>
      </Modal>
    </Stack>
  );
};

export default BulkMetafieldEditor;
