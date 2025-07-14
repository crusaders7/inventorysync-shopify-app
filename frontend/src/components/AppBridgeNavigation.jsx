import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { NavigationMenu } from '@shopify/app-bridge-react';

const AppBridgeNavigation = () => {
  const navigate = useNavigate();

  const navigationItems = [
    {
      label: 'Dashboard',
      destination: '/',
    },
    {
      label: 'Inventory',
      destination: '/inventory',
    },
    {
      label: 'Alerts', 
      destination: '/alerts',
    },
    {
      label: 'Reports',
      destination: '/reports',
    },
    {
      label: 'Forecasts',
      destination: '/forecasts',
    },
    {
      label: 'Settings',
      destination: '/settings',
    }
  ];

  // Handle navigation clicks
  const handleNavigationClick = (destination) => {
    navigate(destination);
  };

  return (
    <NavigationMenu
      navigationLinks={navigationItems}
      matcher={(link, location) => link.destination === location.pathname}
      onNavigationDismiss={() => {}}
    />
  );
};

export default AppBridgeNavigation;