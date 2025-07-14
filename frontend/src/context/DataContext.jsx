import React, { createContext, useContext, useReducer, useEffect } from 'react';

const DataContext = createContext();

const initialState = {
  inventory: [],
  alerts: [],
  stats: {
    totalProducts: 0,
    lowStockAlerts: 0,
    totalValue: 0,
    activeLocations: 0
  },
  lastUpdated: null,
  isLoading: false,
  error: null
};

function dataReducer(state, action) {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
      
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
      
    case 'UPDATE_INVENTORY':
      return { 
        ...state, 
        inventory: action.payload, 
        lastUpdated: new Date(),
        isLoading: false 
      };
      
    case 'UPDATE_ALERTS':
      return { 
        ...state, 
        alerts: action.payload, 
        lastUpdated: new Date(),
        isLoading: false 
      };
      
    case 'UPDATE_STATS':
      return { 
        ...state, 
        stats: action.payload, 
        lastUpdated: new Date(),
        isLoading: false 
      };
      
    case 'ADD_ALERT':
      return {
        ...state,
        alerts: [action.payload, ...state.alerts],
        stats: {
          ...state.stats,
          lowStockAlerts: state.stats.lowStockAlerts + 1
        }
      };
      
    case 'REMOVE_ALERT':
      return {
        ...state,
        alerts: state.alerts.filter(alert => alert.id !== action.payload),
        stats: {
          ...state.stats,
          lowStockAlerts: Math.max(0, state.stats.lowStockAlerts - 1)
        }
      };
      
    case 'UPDATE_PRODUCT_STOCK':
      return {
        ...state,
        inventory: state.inventory.map(item =>
          item.id === action.payload.id
            ? { ...item, current_stock: action.payload.stock }
            : item
        ),
        lastUpdated: new Date()
      };
      
    default:
      return state;
  }
}

export function DataProvider({ children }) {
  const [state, dispatch] = useReducer(dataReducer, initialState);

  // Auto-refresh data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (!state.isLoading) {
        refreshAllData();
      }
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [state.isLoading]);

  const refreshAllData = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      // Fetch all data in parallel
      const [inventoryResponse, alertsResponse, statsResponse] = await Promise.all([
        fetch('http://localhost:8000/api/v1/inventory/'),
        fetch('http://localhost:8000/api/v1/alerts/'),
        fetch('http://localhost:8000/api/v1/dashboard/stats')
      ]);

      if (inventoryResponse.ok) {
        const inventoryData = await inventoryResponse.json();
        dispatch({ type: 'UPDATE_INVENTORY', payload: inventoryData.items || [] });
      }

      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        dispatch({ type: 'UPDATE_ALERTS', payload: alertsData.alerts || [] });
      }

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        dispatch({ type: 'UPDATE_STATS', payload: statsData });
      }

    } catch (error) {
      console.error('Failed to refresh data:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  };

  const updateProductStock = async (productId, newStock) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/inventory/${productId}/stock`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ quantity: newStock }),
      });

      if (response.ok) {
        const data = await response.json();
        dispatch({ 
          type: 'UPDATE_PRODUCT_STOCK', 
          payload: { id: productId, stock: newStock }
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to update stock:', error);
      return false;
    }
  };

  const resolveAlert = async (alertId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/alerts/${alertId}/resolve`, {
        method: 'PUT',
      });

      if (response.ok) {
        dispatch({ type: 'REMOVE_ALERT', payload: alertId });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to resolve alert:', error);
      return false;
    }
  };

  const simulateRealTimeUpdate = () => {
    // Simulate real-time stock changes for demo purposes
    if (state.inventory.length > 0) {
      const randomProduct = state.inventory[Math.floor(Math.random() * state.inventory.length)];
      const stockChange = Math.floor(Math.random() * 10) - 5; // -5 to +5
      const newStock = Math.max(0, randomProduct.current_stock + stockChange);
      
      dispatch({ 
        type: 'UPDATE_PRODUCT_STOCK', 
        payload: { id: randomProduct.id, stock: newStock }
      });

      // Add low stock alert if needed
      if (newStock <= randomProduct.reorder_point && randomProduct.current_stock > randomProduct.reorder_point) {
        const newAlert = {
          id: Date.now(),
          title: 'Low Stock Alert',
          product: randomProduct.product_name,
          message: `Stock level is now ${newStock}, below reorder point of ${randomProduct.reorder_point}`,
          severity: 'warning',
          created_at: new Date().toISOString(),
          status: 'active'
        };
        dispatch({ type: 'ADD_ALERT', payload: newAlert });
      }
    }
  };

  const value = {
    ...state,
    refreshAllData,
    updateProductStock,
    resolveAlert,
    simulateRealTimeUpdate
  };

  return (
    <DataContext.Provider value={value}>
      {children}
    </DataContext.Provider>
  );
}

export function useData() {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
}

export default DataContext;