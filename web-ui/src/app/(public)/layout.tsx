/**
 * 公共路由布局
 * 用于不需要认证的页面（登录、回调等）
 */
export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
