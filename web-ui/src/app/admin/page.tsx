import { redirect } from 'next/navigation';

export default function AdminIndexPage() {
  // 管理后台入口重定向到用户管理页
  redirect('/admin/users');
}

