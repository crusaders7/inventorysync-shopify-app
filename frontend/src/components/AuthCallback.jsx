import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Banner, Card, Layout, Page, Spinner, Text } from '@shopify/polaris';

const AuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      // Get parameters from URL
      const shop = searchParams.get('shop');
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const hmac = searchParams.get('hmac');
      const timestamp = searchParams.get('timestamp');

      if (!shop || !code) {
        setError('Invalid callback parameters. Please try installing again.');
        setLoading(false);
        return;
      }

      try {
        // The backend should have already handled the OAuth callback
        // Check if we have a valid session
        const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/api/v1/auth/status`);
        const data = await response.json();

        if (data.configured && data.connected_stores > 0) {
          // Successfully authenticated, redirect to dashboard
          localStorage.setItem('shopify_authenticated', 'true');
          localStorage.setItem('shop_domain', shop);
          setTimeout(() => {
            navigate('/');
          }, 1500);
        } else {
          setError('Authentication failed. Please try installing again.');
          setLoading(false);
        }
      } catch (err) {
        console.error('Auth callback error:', err);
        setError('Failed to complete authentication. Please try again.');
        setLoading(false);
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return (
    <Page>
      <Layout>
        <Layout.Section>
          <div style={{ maxWidth: '600px', margin: '0 auto', paddingTop: '40px' }}>
            <Card sectioned>
              <div style={{ textAlign: 'center' }}>
                {loading ? (
                  <>
                    <Spinner size="large" />
                    <div style={{ marginTop: '20px' }}>
                      <Text variant="headingMd" as="h2">
                        Completing installation...
                      </Text>
                      <Text variant="bodyMd" color="subdued">
                        Please wait while we set up your store
                      </Text>
                    </div>
                  </>
                ) : error ? (
                  <Banner status="critical">
                    <Text variant="headingMd" as="h2">
                      Installation Error
                    </Text>
                    <p>{error}</p>
                  </Banner>
                ) : (
                  <Banner status="success">
                    <Text variant="headingMd" as="h2">
                      Installation Successful!
                    </Text>
                    <p>Redirecting to your dashboard...</p>
                  </Banner>
                )}
              </div>
            </Card>
          </div>
        </Layout.Section>
      </Layout>
    </Page>
  );
};

export default AuthCallback;