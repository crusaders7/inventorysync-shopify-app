import { NextRequest } from 'next/server';
import { forwardToBackend } from '../base';

export async function GET(request: NextRequest) {
  return forwardToBackend(request, '/api/v1/auth/status');
}

export async function POST(request: NextRequest) {
  return forwardToBackend(request, '/api/v1/auth/install', {
    method: 'POST',
    body: request.body
  });
}
