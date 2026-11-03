import { expect, it, vi } from 'vitest';
import { forwardRead } from '@/lib/backend-proxy';
it('缺配置返回统一503', async () => { const response = await forwardRead(new Request('http://local/api/v1/reports'), ''); expect(response.status).toBe(503); expect((await response.json()).error.code).toBe('backend_unconfigured'); });
it('拒绝写请求', async () => { const response = await forwardRead(new Request('http://local/api/v1/reports', {method:'POST'}), 'http://127.0.0.1:8000'); expect(response.status).toBe(405); });
it('只把固定目标和公开请求头交给上游', async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response('[]', {headers:{'content-type':'application/json'}})); vi.stubGlobal('fetch',fetcher);
  const response = await forwardRead(new Request('http://local/api/v1/reports?a=1', {headers:{'x-client-ip':'spoofed','authorization':'private'}}),'http://127.0.0.1:8000');
  expect(await response.json()).toEqual([]); expect(String(fetcher.mock.calls[0][0])).toBe('http://127.0.0.1:8000/api/v1/reports?a=1'); expect(fetcher.mock.calls[0][1].headers).toEqual({accept:'application/json'});
});
it('上游异常不泄露内部详情', async () => { vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new Error('private'))); const response=await forwardRead(new Request('http://local/api/v1/reports'),'http://127.0.0.1:8000'); expect(response.status).toBe(503); expect(await response.text()).not.toContain('private'); });
