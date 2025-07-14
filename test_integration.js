#!/usr/bin/env node

/**
 * Integration test script to verify frontend-backend connectivity
 * Tests all critical API endpoints that the frontend uses
 */

const API_BASE = 'http://localhost:8000';

async function makeRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        return { success: response.ok, status: response.status, data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

async function runTests() {
    console.log('🚀 Starting InventorySync API Integration Tests\n');
    
    const tests = [
        {
            name: 'Dashboard Stats',
            test: () => makeRequest(`${API_BASE}/api/v1/dashboard/stats`)
        },
        {
            name: 'Dashboard Alerts',
            test: () => makeRequest(`${API_BASE}/api/v1/dashboard/alerts`)
        },
        {
            name: 'Inventory List',
            test: () => makeRequest(`${API_BASE}/api/v1/inventory/`)
        },
        {
            name: 'Inventory Search',
            test: () => makeRequest(`${API_BASE}/api/v1/inventory/?search=blue`)
        },
        {
            name: 'Inventory Location Filter',
            test: () => makeRequest(`${API_BASE}/api/v1/inventory/?location=Warehouse%20A`)
        },
        {
            name: 'Alerts List',
            test: () => makeRequest(`${API_BASE}/api/v1/alerts/`)
        },
        {
            name: 'Alerts Filter Active',
            test: () => makeRequest(`${API_BASE}/api/v1/alerts/?status=active`)
        },
        {
            name: 'Create Product',
            test: () => makeRequest(`${API_BASE}/api/v1/inventory/`, {
                method: 'POST',
                body: JSON.stringify({
                    product_name: 'Integration Test Product',
                    sku: 'INT-TEST-001',
                    current_stock: 75,
                    reorder_point: 25,
                    location: 'Warehouse A'
                })
            })
        },
        {
            name: 'Update Stock',
            test: () => makeRequest(`${API_BASE}/api/v1/inventory/1/stock`, {
                method: 'PUT',
                body: JSON.stringify({ quantity: 30 })
            })
        },
        {
            name: 'Resolve Alert',
            test: () => makeRequest(`${API_BASE}/api/v1/alerts/1/resolve`, {
                method: 'PUT'
            })
        },
        {
            name: 'Auth Status',
            test: () => makeRequest(`${API_BASE}/auth/status`)
        }
    ];
    
    let passed = 0;
    let failed = 0;
    
    for (const test of tests) {
        try {
            console.log(`Testing: ${test.name}...`);
            const result = await test.test();
            
            if (result.success) {
                console.log(`✅ ${test.name} - PASSED`);
                passed++;
            } else {
                console.log(`❌ ${test.name} - FAILED: ${result.error || result.data?.detail || 'Unknown error'}`);
                failed++;
            }
        } catch (error) {
            console.log(`❌ ${test.name} - ERROR: ${error.message}`);
            failed++;
        }
        
        // Small delay between tests
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.log(`\n📊 Test Results:`);
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%`);
    
    if (failed === 0) {
        console.log('\n🎉 All tests passed! Frontend-Backend integration is working correctly.');
    } else {
        console.log('\n⚠️  Some tests failed. Check the API endpoints and CORS configuration.');
    }
}

// Check if fetch is available (Node 18+)
if (typeof fetch === 'undefined') {
    console.log('❌ This script requires Node.js 18+ with fetch support.');
    console.log('Run with: node --experimental-fetch test_integration.js');
    process.exit(1);
}

runTests().catch(console.error);