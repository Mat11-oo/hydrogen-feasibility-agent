export async function forwardRead(request: Request, backendUrl = process.env.BACKEND_URL): Promise<Response> {
  const failure = (status: number, code: string, message: string) => Response.json({ error: { code, message } }, { status });
  if (!['GET', 'HEAD'].includes(request.method)) return failure(405, 'method_not_allowed', '当前入口仅支持读取');
  if (!backendUrl) return failure(503, 'backend_unconfigured', '服务暂时不可用');
  let target: URL;
  try {
    const base = new URL(backendUrl);
    if (!['http:', 'https:'].includes(base.protocol)) throw new Error();
    const incoming = new URL(request.url);
    target = new URL(base.origin);
    target.pathname = incoming.pathname;
    target.search = incoming.search;
  } catch { return failure(503, 'backend_unconfigured', '服务暂时不可用'); }
  try {
    const result = await fetch(target, {
      method: request.method,
      headers: { accept: 'application/json' },
      cache: 'no-store',
      redirect: 'error',
      signal: AbortSignal.timeout(15_000),
    });
    if (!result.ok) return failure(result.status, `upstream_${result.status}`, '读取失败，请稍后重试');
    return new Response(request.method === 'HEAD' ? null : result.body, {
      status: result.status,
      headers: { 'content-type': result.headers.get('content-type') || 'application/json', 'cache-control': 'no-store' },
    });
  } catch { return failure(503, 'backend_unavailable', '服务暂时不可用'); }
}
