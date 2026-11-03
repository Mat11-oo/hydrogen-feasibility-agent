import Link from 'next/link';
import { ArrowLeft, Construction } from 'lucide-react';
export function StageNotice({ title, description }: { title: string; description: string }) {
  return <div className="page-content notice-page"><Link className="text-link" href="/"><ArrowLeft size={16}/>返回我的报告</Link><section className="notice-card"><span className="empty-symbol"><Construction size={28}/></span><span className="section-kicker">当前为代表页预览</span><h1>{title}</h1><p>{description}</p><p className="notice-small">下一阶段对接真实操作；当前不会提交或修改报告。</p></section></div>;
}
