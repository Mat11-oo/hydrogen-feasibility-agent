import { expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { ReportsView } from '@/components/reports-view';
const row = {id:1,title:'氢能示范项目',target_words:12000,user_requirements:'',status:'outline_pending',created_at:'2026-11-03T08:00:00'};
it('加载时不先显示空列表', () => { vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {}))); render(<ReportsView/>); expect(screen.getByRole('status')).toHaveTextContent('正在读取'); expect(screen.queryByText('第一份报告，从这里开始')).toBeNull(); });
it('成功空列表显示创建入口', async () => { vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('[]'))); render(<ReportsView/>); expect(await screen.findByText('第一份报告，从这里开始')).toBeInTheDocument(); });
it('读取错误后可手动恢复', async () => { const fetcher=vi.fn().mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(new Response(JSON.stringify([row]))); vi.stubGlobal('fetch',fetcher); render(<ReportsView/>); await screen.findByRole('alert'); fireEvent.click(screen.getByRole('button',{name:'重新加载'})); expect(await screen.findByText(row.title)).toBeInTheDocument(); });
it('展示真实结果并可筛选后清空', async () => { vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify([row])))); render(<ReportsView/>); expect(await screen.findByText(row.title)).toBeInTheDocument(); fireEvent.change(screen.getByLabelText('搜索报告名称'),{target:{value:'不存在'}}); expect(screen.getByText('没有找到匹配的报告')).toBeInTheDocument(); fireEvent.click(screen.getAllByRole('button',{name:'清空搜索'})[0]); expect(screen.getByText(row.title)).toBeInTheDocument(); });
