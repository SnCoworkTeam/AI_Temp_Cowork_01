/**
 * 返回 OpenCode 独立地址（从服务端环境变量读取，无需重新构建前端即可生效）
 */
import { NextResponse } from 'next/server';

export async function GET() {
  const url = process.env.NEXT_PUBLIC_OPENCODE_URL || '';
  return NextResponse.json({ url });
}
