import { describe, expect, it, vi } from 'vitest';
import { fetchReports, parseReports, reportStatus, formatDate } from '@/lib/reports';
const row = { id: 1, title: '测试', target_words: 12000, user_requirements: '', status: 'outline_pending', created_at: '2026-11-03T08:00:00' };
describe('报告契约', () => {
  it('接受后端数组和空列表', () => { expect(parseReports([row])).toEqual([row]); expect(parseReports([])).toEqual([]); });
  it.each([{}, [null], [{...row, id: '1'}], [{...row, created_at: 'bad'}], [{...row, target_words: null}]])('异常返回不被当成空列表', (value) => { expect(() => parseReports(value)).toThrow('数据格式异常'); });
  it('未知状态不能被当成成功', () => { expect(reportStatus('unknown')).toBe('状态待确认'); expect(reportStatus('outline_pending')).toBe('待确认大纲'); });
  it('无时区UTC时间按上海时区显示', () => { expect(formatDate('2026-11-03T20:00:00')).toBe('2026/11/04'); });
  it('服务失败不回显内部响应', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('private-error', {status:503})));
    await expect(fetchReports()).rejects.toThrow('服务暂时不可用');
  });
});
