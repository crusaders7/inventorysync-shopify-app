import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function authMiddleware(request: NextRequest) {
  // Skip auth check for public routes
  if (
    request.nextUrl.pathname.startsWith('/_next') ||
    request.nextUrl.pathname.startsWith('/api/auth') ||
    request.nextUrl.pathname === '/install' ||
    request.nextUrl.pathname === '/login'
  ) {
    return NextResponse.next();
  }

  // Check for authentication
  const shopDomain = cookies().get('shopDomain')?.value;
  const isAuthenticated = cookies().get('shopify_authenticated')?.value === 'true';

  if (!isAuthenticated && !shopDomain) {
    // Redirect to install page for non-authenticated requests
    return NextResponse.redirect(new URL('/install', request.url));
  }

  // For API routes, return 401 instead of redirecting
  if (request.nextUrl.pathname.startsWith('/api/') && !isAuthenticated) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  return NextResponse.next();
}
