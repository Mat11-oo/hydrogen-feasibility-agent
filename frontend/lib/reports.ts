export type Report = {
  id: number;
  title: string;
  target_words: number;
  user_requirements: string;
  status: string;
  created_at: string;
};

export class ApiError extends Error {
  constructor(public code: string, message: string) { super(message); }
}

export function parseReports(value: unknown): Report[] {
  if (!Array.isArray(value)) throw new ApiError('invalid_response', '报告数据格式异常，请稍后重试');
  return value.map((item: unknown) => {
    if (typeof item !== 'object' || item === null) throw new ApiError('invalid_response', '报告数据格式异常，请稍后重试');
    const row = item as Record<string, unknown>;
    if (typeof row.id !== 'number' || !Number.isSafeInteger(row.id) || row.id < 1 ||
        typeof row.title !== 'string' || typeof row.status !== 'string' ||
        typeof row.target_words !== 'number' || !Number.isFinite(row.target_words) ||
        typeof row.user_requirements !== 'string' || typeof row.created_at !== 'string' ||
        !Number.isFinite(Date.parse(row.created_at))) {
      throw new ApiError('invalid_response', '报告数据格式异常，请稍后重试');
    }
    return { id: row.id, title: row.title, target_words: row.target_words, user_requirements: row.user_requirements, status: row.status, created_at: row.created_at };
  });
}

export async function fetchReports(signal?: AbortSignal): Promise<Report[]> {
  let response: Response;
  try {
    response = await fetch('/api/v1/reports', { cache: 'no-store', signal });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError('network_error', '暂时无法连接服务，请检查后重试');
  }
  if (!response.ok) {
    throw new ApiError(`http_${response.status}`, response.status === 503 || response.status === 504
      ? '报告服务暂时不可用，请稍后重试' : '读取报告失败，请重试');
  }
  try { return parseReports(await response.json()); }
  catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('invalid_response', '报告数据格式异常，请稍后重试');
  }
}

export function reportStatus(status: string): string {
  return status === 'outline_pending' ? '待确认大纲' : '状态待确认';
}

export function formatDate(value: string): string {
  // SQLite本地存储的无时区时间由后端以UTC写入。
  const date = new Date(/(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`);
  return new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' }).format(date);
}
