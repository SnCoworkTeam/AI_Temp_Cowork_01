/**
 * 健康检查API路由
 */
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    service: 'web-ui',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
  });
}
