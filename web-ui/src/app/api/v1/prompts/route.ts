import { NextRequest, NextResponse } from 'next/server';

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.search;
  const path = request.nextUrl.pathname.replace('/api/v1/prompts', '');
  
  let targetUrl;
  if (path === '/categories/list') {
    targetUrl = `${API_GATEWAY_URL}/api/v1/prompts/categories/list${searchParams}`;
  } else {
    targetUrl = `${API_GATEWAY_URL}/api/v1/prompts${searchParams}`;
  }
  
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
    if (path === '/categories/list') {
      return NextResponse.json({ items: [] }, { status: 200 });
    }
    return NextResponse.json({ items: [], total: 0, message: 'Prompts service unavailable' }, { status: 200 });
  }
}

export async function POST(request: NextRequest) {
  const targetUrl = `${API_GATEWAY_URL}/api/v1/prompts`;
  
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
    return NextResponse.json({ error: 'Prompts service unavailable' }, { status: 500 });
  }
}
