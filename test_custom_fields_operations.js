#!/usr/bin/env node

/**
 * Custom Fields API Test Script
 * Tests all CRUD operations for custom fields
 */

const API_BASE = 'http://localhost:8000';
const SHOP_DOMAIN = 'inventorysync-dev.myshopify.com';

// Color codes for output
const colors = {
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    reset: '\x1b[0m'
};

// Helper function to make requests
async function makeRequest(url, options = {}) {
    try {
        console.log(`${colors.blue}🌐 ${options.method || 'GET'} ${url}${colors.reset}`);
        
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            console.log(`${colors.red}❌ Error: ${response.status} - ${JSON.stringify(data)}${colors.reset}`);
        }
        
        return { success: response.ok, status: response.status, data };
    } catch (error) {
        console.log(`${colors.red}❌ Request failed: ${error.message}${colors.reset}`);
        return { success: false, error: error.message };
    }
}

// Test data
const testField = {
    field_name: 'test_priority',
    field_type: 'select',
    display_name: 'Product Priority',
    description: 'Priority level for this product',
    required: false,
    default_value: 'Medium',
    validation_rules: {
        options: ['Low', 'Medium', 'High', 'Critical']
    },
    category: 'product'
};

const updateData = {
    display_name: 'Updated Product Priority',
    description: 'Updated description for priority field',
    validation_rules: {
        options: ['Low', 'Medium', 'High', 'Critical', 'Urgent']
    }
};

let createdFieldId = null;

// Test functions
async function testFetchCustomFields() {
    console.log('\n📋 Test 1: Fetching Custom Fields List');
    console.log('=====================================');
    
    const result = await makeRequest(`${API_BASE}/api/custom-fields/${SHOP_DOMAIN}`);
    
    if (result.success) {
        console.log(`${colors.green}✅ Successfully fetched custom fields${colors.reset}`);
        console.log(`   Found ${result.data.fields?.length || 0} custom fields`);
        
        if (result.data.fields && result.data.fields.length > 0) {
            console.log('   Sample fields:');
            result.data.fields.slice(0, 3).forEach(field => {
                console.log(`   - ${field.field_name}: ${field.display_name} (${field.field_type})`);
            });
        }
    } else {
        console.log(`${colors.red}❌ Failed to fetch custom fields${colors.reset}`);
    }
    
    return result.success;
}

async function testCreateCustomField() {
    console.log('\n➕ Test 2: Creating a New Custom Field');
    console.log('=====================================');
    
    const result = await makeRequest(`${API_BASE}/api/custom-fields/${SHOP_DOMAIN}`, {
        method: 'POST',
        body: JSON.stringify(testField)
    });
    
    if (result.success) {
        createdFieldId = result.data.field_id;
        console.log(`${colors.green}✅ Successfully created custom field${colors.reset}`);
        console.log(`   Field ID: ${createdFieldId}`);
        console.log(`   Field Name: ${result.data.field_name}`);
    } else {
        console.log(`${colors.red}❌ Failed to create custom field${colors.reset}`);
    }
    
    return result.success;
}

async function testUpdateCustomField() {
    console.log('\n✏️  Test 3: Updating an Existing Custom Field');
    console.log('==========================================');
    
    if (!createdFieldId) {
        console.log(`${colors.yellow}⚠️  Skipping update test - no field created${colors.reset}`);
        return false;
    }
    
    const result = await makeRequest(`${API_BASE}/api/custom-fields/${SHOP_DOMAIN}/${createdFieldId}`, {
        method: 'PUT',
        body: JSON.stringify(updateData)
    });
    
    if (result.success) {
        console.log(`${colors.green}✅ Successfully updated custom field${colors.reset}`);
        console.log(`   New display name: ${result.data.display_name}`);
        console.log(`   Options count: ${result.data.validation_rules?.options?.length || 0}`);
    } else {
        console.log(`${colors.red}❌ Failed to update custom field${colors.reset}`);
    }
    
    return result.success;
}

async function testDeleteCustomField() {
    console.log('\n🗑️  Test 4: Deleting a Custom Field');
    console.log('=================================');
    
    if (!createdFieldId) {
        console.log(`${colors.yellow}⚠️  Skipping delete test - no field created${colors.reset}`);
        return false;
    }
    
    const result = await makeRequest(`${API_BASE}/api/custom-fields/${SHOP_DOMAIN}/${createdFieldId}`, {
        method: 'DELETE'
    });
    
    if (result.success) {
        console.log(`${colors.green}✅ Successfully deleted custom field${colors.reset}`);
    } else {
        console.log(`${colors.red}❌ Failed to delete custom field${colors.reset}`);
    }
    
    return result.success;
}

async function testInvalidOperations() {
    console.log('\n🚫 Test 5: Testing Invalid Operations');
    console.log('===================================');
    
    let failedAsExpected = 0;
    let unexpectedSuccess = 0;
    
    // Test 1: Invalid field name
    console.log('   Testing invalid field name...');
    const invalidNameResult = await makeRequest(`${API_BASE}/api/custom-fields/${SHOP_DOMAIN}`, {
        method: 'POST',
        body: JSON.stringify({
            ...testField,
            field_name: 'Invalid Field Name!' // Should fail due to spaces and special chars
        })
    });
    
    if (!invalidNameResult.success) {
        console.log(`   ${colors.green}✓ Correctly rejected invalid field name${colors.reset}`);
        failedAsExpected++;
    } else {
        console.log(`   ${colors.red}✗ Unexpectedly accepted invalid field name${colors.reset}`);
        unexpectedSuccess++;
    }
    
    // Test 2: Missing required fields
    console.log('   Testing missing required fields...');
    const missingFieldsResult = await makeRequest(`${API_BASE}/api/custom-fields/${SHOP_DOMAIN}`, {
        method: 'POST',
        body: JSON.stringify({
            field_name: 'incomplete_field'
            // Missing field_type and display_name
        })
    });
    
    if (!missingFieldsResult.success) {
        console.log(`   ${colors.green}✓ Correctly rejected incomplete field data${colors.reset}`);
        failedAsExpected++;
    } else {
        console.log(`   ${colors.red}✗ Unexpectedly accepted incomplete field data${colors.reset}`);
        unexpectedSuccess++;
    }
    
    // Test 3: Invalid shop domain
    console.log('   Testing invalid shop domain...');
    const invalidShopResult = await makeRequest(`${API_BASE}/api/custom-fields/invalid-shop`, {
        method: 'GET'
    });
    
    if (!invalidShopResult.success) {
        console.log(`   ${colors.green}✓ Correctly rejected invalid shop domain${colors.reset}`);
        failedAsExpected++;
    } else {
        console.log(`   ${colors.red}✗ Unexpectedly accepted invalid shop domain${colors.reset}`);
        unexpectedSuccess++;
    }
    
    return unexpectedSuccess === 0;
}

async function testTemplates() {
    console.log('\n📋 Test 6: Testing Industry Templates');
    console.log('===================================');
    
    const result = await makeRequest(`${API_BASE}/api/custom-fields/templates`);
    
    if (result.success) {
        console.log(`${colors.green}✅ Successfully fetched templates${colors.reset}`);
        console.log(`   Available industries: ${result.data.industries?.join(', ') || 'none'}`);
        
        // Show sample template
        const industries = Object.keys(result.data.templates || {});
        if (industries.length > 0) {
            const sampleIndustry = industries[0];
            const sampleFields = result.data.templates[sampleIndustry];
            console.log(`   Sample template (${sampleIndustry}):`);
            sampleFields.slice(0, 2).forEach(field => {
                console.log(`   - ${field.field_name}: ${field.display_name}`);
            });
        }
    } else {
        console.log(`${colors.red}❌ Failed to fetch templates${colors.reset}`);
    }
    
    return result.success;
}

// Browser network tab instructions
function showNetworkTabInstructions() {
    console.log('\n🔍 Browser Network Tab Verification');
    console.log('==================================');
    console.log('To verify the correct URLs are being called in the browser:');
    console.log('1. Open your browser DevTools (F12)');
    console.log('2. Go to the Network tab');
    console.log('3. Clear the network log');
    console.log('4. In your app, navigate to the Custom Fields section');
    console.log('5. Perform these operations and check the requests:');
    console.log(`   - List fields: GET ${API_BASE}/api/custom-fields/{shop_domain}`);
    console.log(`   - Create field: POST ${API_BASE}/api/custom-fields/{shop_domain}`);
    console.log(`   - Update field: PUT ${API_BASE}/api/custom-fields/{shop_domain}/{field_id}`);
    console.log(`   - Delete field: DELETE ${API_BASE}/api/custom-fields/{shop_domain}/{field_id}`);
    console.log(`   - Get templates: GET ${API_BASE}/api/custom-fields/templates`);
    console.log('\n6. Check that:');
    console.log('   - Request URLs match the patterns above');
    console.log('   - Request methods are correct (GET, POST, PUT, DELETE)');
    console.log('   - Request payloads contain the expected data');
    console.log('   - Response status codes are appropriate (200, 201, 400, 404, etc.)');
    console.log('   - CORS headers are present (Access-Control-Allow-Origin)');
}

// Main test runner
async function runTests() {
    console.log(`${colors.blue}🚀 Starting Custom Fields API Tests${colors.reset}`);
    console.log(`API Base: ${API_BASE}`);
    console.log(`Shop Domain: ${SHOP_DOMAIN}\n`);
    
    const results = {
        fetch: false,
        create: false,
        update: false,
        delete: false,
        invalid: false,
        templates: false
    };
    
    // Run tests in sequence
    results.fetch = await testFetchCustomFields();
    results.create = await testCreateCustomField();
    results.update = await testUpdateCustomField();
    results.delete = await testDeleteCustomField();
    results.invalid = await testInvalidOperations();
    results.templates = await testTemplates();
    
    // Show summary
    console.log('\n📊 Test Summary');
    console.log('==============');
    const passed = Object.values(results).filter(r => r).length;
    const total = Object.keys(results).length;
    
    Object.entries(results).forEach(([test, result]) => {
        const status = result ? `${colors.green}✅ PASSED${colors.reset}` : `${colors.red}❌ FAILED${colors.reset}`;
        console.log(`${test.padEnd(15)} ${status}`);
    });
    
    console.log(`\n${colors.blue}Total: ${passed}/${total} tests passed (${Math.round(passed/total * 100)}%)${colors.reset}`);
    
    if (passed === total) {
        console.log(`\n${colors.green}🎉 All tests passed! Custom fields API is working correctly.${colors.reset}`);
    } else {
        console.log(`\n${colors.yellow}⚠️  Some tests failed. Check the API implementation.${colors.reset}`);
    }
    
    // Show browser verification instructions
    showNetworkTabInstructions();
}

// Check if fetch is available
if (typeof fetch === 'undefined') {
    console.log(`${colors.red}❌ This script requires Node.js 18+ with fetch support.${colors.reset}`);
    console.log('Run with: node test_custom_fields_operations.js');
    process.exit(1);
}

// Check if backend is running
fetch(`${API_BASE}/health`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Backend not responding');
        }
        return runTests();
    })
    .catch(error => {
        console.log(`${colors.red}❌ Backend is not running at ${API_BASE}${colors.reset}`);
        console.log('Please start the backend server first:');
        console.log('  cd backend && python main.py');
        process.exit(1);
    });
