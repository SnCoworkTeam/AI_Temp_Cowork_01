'use client';

import { usePathname } from 'next/navigation';
import { Navbar } from './Navbar';

export function ConditionalNavbar() {
  const pathname = usePathname();

  // 如果是管理后台页面，不显示导航栏（管理后台布局有自己的导航栏）
  const isAdminPage = pathname?.startsWith('/admin');

  // 如果是登录页面，不显示导航栏
  const isLoginPage = pathname === '/login';

  if (isAdminPage || isLoginPage) {
    return null;
  }

  return <Navbar />;
}
