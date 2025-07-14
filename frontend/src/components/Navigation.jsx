import React from 'react';
import { Button } from '@shopify/polaris';
import { useNavigate, useLocation } from 'react-router-dom';

function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();

  const navigationItems = [
    { path: '/', label: '🏠 Dashboard', primary: true },
    { path: '/custom-fields', label: '⚡ Custom Fields', primary: true },
    { path: '/inventory', label: '📦 Inventory' },
    { path: '/settings', label: '⚙️ Settings' }
  ];

  return (
    <div style={{
      padding: '12px 20px',
      backgroundColor: '#fafbfb',
      borderBottom: '1px solid #e1e3e5',
      marginBottom: '20px'
    }}>
      <div style={{
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
        flexWrap: 'wrap'
      }}>
        {navigationItems.map((item) => (
          <Button
            key={item.path}
            onClick={() => navigate(item.path)}
            primary={item.primary && location.pathname !== '/'}
            pressed={location.pathname === item.path}
            outline={location.pathname !== item.path && !item.primary}
            size="slim"
          >
            {item.label}
          </Button>
        ))}
      </div>
    </div>
  );
}

export default Navigation;