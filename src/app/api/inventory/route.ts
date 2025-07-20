import { NextRequest } from 'next/server';
import { forwardToBackend } from '../base';

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const shopDomain = url.searchParams.get('shop');
  return forwardToBackend(request, `/api/inventory/${shopDomain}`);
}

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const shopDomain = url.searchParams.get('shop');
  return forwardToBackend(request, `/api/inventory/${shopDomain}`, {
    method: 'POST',
    body: request.body
  });
}

export async function PUT(request: NextRequest) {
  const url = new URL(request.url);
  const shopDomain = url.searchParams.get('shop');
  const itemId = url.searchParams.get('id');
  return forwardToBackend(request, `/api/inventory/${shopDomain}/${itemId}`, {
    method: 'PUT',
    body: request.body
  });
}
