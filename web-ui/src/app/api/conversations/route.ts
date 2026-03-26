import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.search;
  const targetUrl = `${API_GATEWAY_URL}/api/conversations${searchParams}`;
  
  try {
    const response = await fetch(targetUrl, {
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        'Content-Type': 'application/json',
      },
    });
    
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ items: [], total: 0, message: 'Service unavailable' }, { status: 200 });
  }
}

export async function POST(request: NextRequest) {
  const targetUrl = `${API_GATEWAY_URL}/api/conversations`;
  
  try {
    const body = await request.json();
    const response = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Service unavailable' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  const searchParams = request.nextUrl.search;
  const targetUrl = `${API_GATEWAY_URL}/api/conversations${searchParams}`;
  
  try {
    const response = await fetch(targetUrl, {
      method: 'DELETE',
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        'Content-Type': 'application/json',
      },
    });
    
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Service unavailable' }, { status: 500 });
  }
}
