import type { Metadata } from 'next';
import { AppShell } from '@/components/app-shell';
import './globals.css';
export const metadata: Metadata = { title: '我的报告 · 可研报告', description: '整理项目资料，构建可研报告大纲。' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body><AppShell>{children}</AppShell></body></html>;
}
