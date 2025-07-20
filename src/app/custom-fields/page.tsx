'use client';

import { useState } from 'react';
import { 
  Page, 
  Card, 
  Button, 
  Modal, 
  FormLayout, 
  TextField, 
  Select, 
  Checkbox 
} from '@shopify/polaris';

export default function CustomFields() {
  const [showModal, setShowModal] = useState(false);
  const [newField, setNewField] = useState({
    name: '',
    label: '',
    type: 'text',
    required: false
  });

  const fieldTypes = [
    {label: 'Text', value: 'text'},
    {label: 'Number', value: 'number'},
    {label: 'Date', value: 'date'},
    {label: 'Select', value: 'select'},
    {label: 'Checkbox', value: 'checkbox'}
  ];

  const handleCreateField = async () => {
    try {
      const response = await fetch('/api/custom-fields/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newField),
      });

      if (response.ok) {
        alert('Custom field created successfully!');
        setShowModal(false);
        setNewField({ name: '', label: '', type: 'text', required: false });
      } else {
        alert('Failed to create custom field');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error creating custom field');
    }
  };

  return (
    <Page 
      title="Custom Fields"
      primaryAction={{
        content: 'Add custom field',
        onAction: () => setShowModal(true)
      }}
    >
      <Card>
        <Card.Section>
          <p>Create custom fields to store additional information about your products.</p>
        </Card.Section>
      </Card>

      <Modal
        open={showModal}
        onClose={() => setShowModal(false)}
        title="Add custom field"
        primaryAction={{
          content: 'Add field',
          onAction: handleCreateField
        }}
        secondaryActions={[{
          content: 'Cancel',
          onAction: () => setShowModal(false)
        }]}
      >
        <Modal.Section>
          <FormLayout>
            <TextField
              label="Field name"
              value={newField.name}
              onChange={(value) => setNewField({ ...newField, name: value })}
              helpText="Internal name (lowercase, no spaces)"
            />
            
            <TextField
              label="Display label"
              value={newField.label}
              onChange={(value) => setNewField({ ...newField, label: value })}
              helpText="How the field will be displayed"
            />
            
            <Select
              label="Field type"
              options={fieldTypes}
              value={newField.type}
              onChange={(value) => setNewField({ ...newField, type: value })}
            />
            
            <Checkbox
              label="This field is required"
              checked={newField.required}
              onChange={(checked) => setNewField({ ...newField, required: checked })}
            />
          </FormLayout>
        </Modal.Section>
      </Modal>
    </Page>
  );
}
