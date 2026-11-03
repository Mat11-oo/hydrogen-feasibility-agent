import type { NextRequest } from 'next/server';
import { forwardRead } from './lib/backend-proxy';
export function proxy(request: NextRequest) { return forwardRead(request); }
export const config = { matcher: '/api/:path*' };
