'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ArrowRight, ArrowUpRight, FileText, FolderOpen, Plus, RefreshCw, Search, X, AlertCircle, AlignLeft, CalendarDays } from 'lucide-react';
import { fetchReports, formatDate, reportStatus, type Report } from '@/lib/reports';

type ViewState = { kind: 'loading' } | { kind: 'error'; message: string } | { kind: 'ready'; reports: Report[] };
export function ReportsView() {
  const [state, setState] = useState<ViewState>({ kind: 'loading' });
  const [query, setQuery] = useState('');
  const [requestKey, setRequestKey] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    fetchReports(controller.signal).then((reports) => {
      if (!controller.signal.aborted) setState({ kind: 'ready', reports });
    }).catch((error: unknown) => {
      if (!controller.signal.aborted) setState({ kind: 'error', message: error instanceof Error ? error.message : '读取报告失败，请重试' });
    });
    return () => controller.abort();
  }, [requestKey]);
  function retry() { setState({ kind: 'loading' }); setRequestKey((value) => value + 1); }
  const reports = state.kind === 'ready' ? state.reports : [];
  const filtered = reports.filter((report) => report.title.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
  return <div className="page-content">
    <div className="page-intro"><div><h1>我的报告<span className="title-period">.</span></h1><p>查看已有报告，或创建一份新的项目大纲。</p></div><Link className="button button-dark" href="/reports/new"><Plus size={17}/>创建报告</Link></div>
    <section className="start-panel" aria-labelledby="start-title">
      <div className="start-icon"><FileText size={30} strokeWidth={1.25}/></div>
      <div className="start-copy"><span className="section-kicker">开始一份新的研究</span><h2 id="start-title">从资料出发，搭好报告的骨架</h2><p>上传项目文件，创建报告，再逐章梳理关键论点与所需数据。</p><div className="workflow"><span><i>01</i>整理资料</span><span className="workflow-line"/><span><i>02</i>创建报告</span><span className="workflow-line"/><span><i>03</i>编辑大纲</span></div></div>
      <Link className="text-link" href="/documents">前往资料库<ArrowUpRight size={17}/></Link>
    </section>
    <section className="reports-section" aria-labelledby="reports-title">
      <div className="section-toolbar"><div className="section-heading"><h2 id="reports-title">全部报告</h2>{state.kind === 'ready' ? <span className="count">{reports.length}</span> : null}</div><div className="list-controls"><div className="search-field"><Search size={16} aria-hidden="true"/><label className="sr-only" htmlFor="report-search">搜索报告名称</label><input id="report-search" placeholder="搜索报告名称" value={query} onChange={(event) => setQuery(event.target.value)}/>{query ? <button aria-label="清空搜索" onClick={() => setQuery('')}><X size={14}/></button> : null}</div><button className="icon-button refresh-button" aria-label="刷新报告列表" onClick={retry} disabled={state.kind === 'loading'}><RefreshCw size={17}/></button></div></div>
      {state.kind === 'loading' ? <div className="loading-state" role="status"><div className="loading-line"/><span>正在读取报告…</span></div> : null}
      {state.kind === 'error' ? <div className="empty-state error-state" role="alert"><span className="empty-symbol"><AlertCircle size={27}/></span><h3>暂时没能读到报告</h3><p>{state.message}</p><button className="button button-outline" onClick={retry}><RefreshCw size={15}/>重新加载</button></div> : null}
      {state.kind === 'ready' && reports.length === 0 ? <div className="empty-state"><span className="empty-symbol"><FolderOpen size={30} strokeWidth={1.3}/></span><h3>第一份报告，从这里开始</h3><p>整理好项目资料后，创建报告并搭建大纲。</p><Link className="button button-outline" href="/reports/new"><Plus size={16}/>创建第一份报告</Link></div> : null}
      {state.kind === 'ready' && reports.length > 0 && filtered.length === 0 ? <div className="empty-state"><Search size={26}/><h3>没有找到匹配的报告</h3><p>试试其他关键词，或查看全部报告。</p><button className="button button-outline" onClick={() => setQuery('')}>清空搜索</button></div> : null}
      {state.kind === 'ready' && filtered.length > 0 ? <div className="report-grid">{filtered.map((report) => <Link className="report-card" href={`/reports/${report.id}/outline`} key={report.id}><div className="card-top"><span className="document-symbol"><FileText size={22} strokeWidth={1.4}/></span><span className={`status-pill ${report.status === 'outline_pending' ? '' : 'unknown-status'}`}><span/>{reportStatus(report.status)}</span></div><h3>{report.title}</h3><div className="report-meta"><span><CalendarDays size={13}/>{formatDate(report.created_at)}</span><span><AlignLeft size={13}/>{report.target_words.toLocaleString('zh-CN')} 字</span></div><div className="card-bottom"><span>查看报告</span><ArrowRight size={17}/></div></Link>)}</div> : null}
      <div className="list-footnote"><span>资料与大纲，保存在你的本地工作空间。</span>{state.kind === 'ready' ? <span aria-live="polite">共 {filtered.length} 份报告</span> : null}</div>
    </section>
  </div>;
}
