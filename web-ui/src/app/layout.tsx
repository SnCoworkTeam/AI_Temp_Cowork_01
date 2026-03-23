import type { Metadata } from 'next';
import { Noto_Sans_SC } from 'next/font/google';
import { JetBrains_Mono } from 'next/font/google';
import './globals.css';
import './message-styles.css';
import AuthProvider from '@/components/AuthProvider';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ConditionalNavbar } from '@/components/Layout/ConditionalNavbar';
import ApiFetchProxy from '@/components/ApiFetchProxy';

// 思源黑体 - 标题和正文
const notoSansSC = Noto_Sans_SC({
  weight: ['400', '700'],
  subsets: ['latin'],
  variable: '--font-noto-sans-sc',
  display: 'swap',
});

// JetBrains Mono - 代码
const jetBrainsMono = JetBrains_Mono({
  weight: ['400', '500', '600'],
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: '中化国际AIOS平台',
  description: '中化国际AIOS平台 - 业务流程自动化',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className={`${notoSansSC.variable} ${jetBrainsMono.variable} font-body`}>
        <ThemeProvider>
          <AuthProvider>
            <ApiFetchProxy />
            <div className="min-h-screen bg-background text-foreground flex flex-col">
              {/* 导航栏 - 只在非管理后台页面显示 */}
              <ConditionalNavbar />
              <main className="flex-1">{children}</main>
            </div>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
