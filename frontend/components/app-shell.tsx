'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef } from 'react';
import { ArrowUpRight, BookOpen, Files, FolderOpen, Menu, Plus, X } from 'lucide-react';

function Navigation() {
  const path = usePathname();
  return <>
    <Link className="brand" href="/" aria-label="可研报告首页"><span className="brand-mark"><BookOpen size={23} strokeWidth={1.5}/></span><span>可研报告<span className="brand-caption">RESEARCH WORKSPACE</span></span></Link>
    <Link className="new-report" href="/reports/new"><Plus size={17}/>创建报告<ArrowUpRight size={14}/></Link>
    <div className="nav-label">工作空间</div>
    <nav aria-label="主导航">
      <Link className={`nav-link ${!path.startsWith('/documents') ? 'active' : ''}`} href="/" aria-current={path === '/' ? 'page' : undefined}><Files size={18}/>我的报告</Link>
      <Link className={`nav-link ${path.startsWith('/documents') ? 'active' : ''}`} href="/documents" aria-current={path.startsWith('/documents') ? 'page' : undefined}><FolderOpen size={18}/>资料库</Link>
    </nav>
    <div className="sidebar-bottom"><span className="workspace-avatar">研</span><div>个人工作空间<span>本地使用</span></div><span className="local-dot" aria-hidden="true"/></div>
  </>;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const path = usePathname();
  function closeMenu() { dialog.current?.close(); menuButton.current?.focus(); }
  useEffect(() => { dialog.current?.close(); }, [path]);
  return <>
    <a className="skip-link" href="#main-content">跳至主要内容</a>
    <aside className="sidebar"><Navigation/></aside>
    <div className="workspace">
      <header className="workspace-topbar">
        <button ref={menuButton} className="icon-button mobile-menu" aria-label="打开导航" aria-haspopup="dialog" onClick={() => dialog.current?.showModal()}><Menu size={21}/></button>
        <span className="breadcrumb">工作空间<span>/</span><span>{path.startsWith('/documents') ? '资料库' : '我的报告'}</span></span>
        <span className="topbar-note"><span className="local-dot"/>本地工作空间</span>
      </header>
      <main id="main-content" tabIndex={-1}>{children}</main>
      <footer className="workspace-footer"><span>可研报告工作空间</span><span>仅供本地使用</span></footer>
    </div>
    <dialog ref={dialog} className="mobile-dialog" aria-label="工作空间导航" onClose={() => menuButton.current?.focus()} onClick={(event) => { if (event.target === dialog.current) closeMenu(); }}>
      <div className="mobile-dialog-inner"><button className="icon-button close-menu" aria-label="关闭导航" onClick={closeMenu}><X size={20}/></button><Navigation/></div>
    </dialog>
  </>;
}
