import { NextRequest, NextResponse } from 'next/server';

export const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function forwardToBackend(
  request: NextRequest,
  endpoint: string,
  options: RequestInit = {}
) {
  try {
    const url = `${BACKEND_URL}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (request.headers.get('authorization')) {
      headers['Authorization'] = request.headers.get('authorization')!;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
