'use client';
export default function ErrorPage({ reset }: { reset: () => void }) { return <div className="page-content empty-state" role="alert"><h1>页面暂时无法显示</h1><p>已有报告仍保存在本地，请重新加载。</p><button className="button button-outline" onClick={reset}>重新加载</button></div>; }
