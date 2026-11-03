import { StageNotice } from '@/components/stage-notice';
export default async function OutlinePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <StageNotice title="报告大纲" description={`报告 #${/^\d+$/.test(id) ? id : '未知'} 的大纲编辑将在下一阶段接入；已有后端数据保持原样。`}/>;
}
