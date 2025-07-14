import React, { lazy, Suspense } from 'react';
import { Spinner, Frame, Layout, SkeletonBodyText } from '@shopify/polaris';

/**
 * Create a lazy loaded component with loading state
 * @param {Function} importFunc - Dynamic import function
 * @param {Object} options - Options for loading behavior
 */
export function lazyLoadComponent(importFunc, options = {}) {
  const {
    fallback = <DefaultLoadingFallback />,
    delay = 200,
    errorBoundary = true
  } = options;

  const LazyComponent = lazy(importFunc);

  return function LazyLoadedComponent(props) {
    if (errorBoundary) {
      return (
        <ErrorBoundary>
          <Suspense fallback={fallback}>
            <LazyComponent {...props} />
          </Suspense>
        </ErrorBoundary>
      );
    }

    return (
      <Suspense fallback={fallback}>
        <LazyComponent {...props} />
      </Suspense>
    );
  };
}

/**
 * Default loading fallback component
 */
function DefaultLoadingFallback() {
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '200px' 
    }}>
      <Spinner accessibilityLabel="Loading content" size="large" />
    </div>
  );
}

/**
 * Page-level loading skeleton
 */
export function PageLoadingSkeleton() {
  return (
    <Frame>
      <Layout>
        <Layout.Section>
          <SkeletonBodyText lines={3} />
        </Layout.Section>
        <Layout.Section>
          <SkeletonBodyText lines={5} />
        </Layout.Section>
      </Layout>
    </Frame>
  );
}

/**
 * Error boundary for lazy loaded components
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Lazy loading error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ 
          padding: '20px', 
          textAlign: 'center',
          color: '#ff6b6b'
        }}>
          <h2>Something went wrong loading this component</h2>
          <p>Please refresh the page to try again.</p>
          {process.env.NODE_ENV === 'development' && (
            <details style={{ marginTop: '20px', textAlign: 'left' }}>
              <summary>Error details</summary>
              <pre>{this.state.error?.toString()}</pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Preload a lazy component
 */
export function preloadComponent(importFunc) {
  const componentPromise = importFunc();
  componentPromise.catch(() => {
    // Silently catch to avoid unhandled promise rejection
  });
  return componentPromise;
}

/**
 * Route-based code splitting helper
 */
export function lazyLoadRoute(path) {
  return lazyLoadComponent(
    () => import(`../pages/${path}`),
    {
      fallback: <PageLoadingSkeleton />,
      errorBoundary: true
    }
  );
}

/**
 * Intersection Observer based lazy loading
 */
export function useLazyLoad(ref, callback, options = {}) {
  React.useEffect(() => {
    if (!ref.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            callback();
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px',
        ...options
      }
    );

    observer.observe(ref.current);

    return () => {
      observer.disconnect();
    };
  }, [ref, callback, options]);
}
