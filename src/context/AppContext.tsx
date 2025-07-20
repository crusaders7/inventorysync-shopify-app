'use client';

import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { AuthState, CustomField, Store } from '@/types';

interface AppState {
  auth: AuthState;
  store?: Store;
  customFields: CustomField[];
  isLoading: boolean;
  error?: string;
}

type Action =
  | { type: 'SET_AUTH'; payload: AuthState }
  | { type: 'SET_STORE'; payload: Store }
  | { type: 'SET_CUSTOM_FIELDS'; payload: CustomField[] }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'CLEAR_ERROR' };

const initialState: AppState = {
  auth: {
    isAuthenticated: false
  },
  customFields: [],
  isLoading: false
};

const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<Action>;
}>({ state: initialState, dispatch: () => null });

function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_AUTH':
      return { ...state, auth: action.payload };
    case 'SET_STORE':
      return { ...state, store: action.payload };
    case 'SET_CUSTOM_FIELDS':
      return { ...state, customFields: action.payload };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'CLEAR_ERROR':
      return { ...state, error: undefined };
    default:
      return state;
  }
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  useEffect(() => {
    // Check authentication status
    const isAuthenticated = localStorage.getItem('shopify_authenticated') === 'true';
    const shopDomain = localStorage.getItem('shopDomain');
    
    if (isAuthenticated && shopDomain) {
      dispatch({
        type: 'SET_AUTH',
        payload: {
          isAuthenticated: true,
          shopDomain
        }
      });

      // Fetch store data
      fetch(`/api/auth/store?shop=${shopDomain}`)
        .then(res => res.json())
        .then(data => {
          if (data.store) {
            dispatch({ type: 'SET_STORE', payload: data.store });
          }
        })
        .catch(error => {
          console.error('Failed to fetch store data:', error);
          dispatch({ type: 'SET_ERROR', payload: 'Failed to fetch store data' });
        });
    }
  }, []);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
