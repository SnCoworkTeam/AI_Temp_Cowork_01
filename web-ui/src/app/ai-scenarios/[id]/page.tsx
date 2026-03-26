'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/AuthGuard';
import ErrorMessage from '@/components/ErrorMessage';
import { Button } from '@/components/UI/Button';
import { Card } from '@/components/UI/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/UI/Table';
import { Pencil, Trash2, Upload, Download, Send, ArrowLeft } from 'lucide-react';
import {
  AIScenario,
  Attachment,
  deleteAIScenario,
  deleteAttachment,
  getAIScenario,
  getAttachmentDownloadUrl,
  listAttachments,
  submitAIScenario,
  uploadAttachments,
} from '@/lib/api/aiScenarios';

export default function AIScenarioDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const router = useRouter();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scenario, setScenario] = useState<AIScenario | null>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);

  const load = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const s = await getAIScenario(id);
      setScenario(s);
      try {
        sessionStorage.setItem(`ai_scenario_name_${s.id}`, `${s.domain}`);
      } catch {}
      const atts = await listAttachments(id);
      setAttachments(atts || []);
    } catch (e: any) {
      setError(e?.message || '加载详情失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const formatKb = (bytes: number) => `${Math.round((bytes / 1024) * 10) / 10} KB`;

  const handleUpload = async (files: FileList | null) => {
    if (!files || !id) return;
    try {
      setLoading(true);
      setError(null);
      await uploadAttachments(id, Array.from(files));
      await load();
    } catch (e: any) {
      setError(e?.message || '上传失败');
    } finally {
      setLoading(false);
    }
  };

  if (!scenario) {
    return (
      <AuthGuard>
        <div className="max-w-5xl mx-auto space-y-4">
          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={() => router.push('/ai-scenarios')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回列表
            </Button>
          </div>
          {error && <ErrorMessage message={error} type="error" onClose={() => setError(null)} />}
          <Card className="p-6">{loading ? '加载中...' : '未找到场景'}</Card>
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <div className="space-y-6 max-w-5xl mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">场景详情</h1>
            <p className="text-sm text-mutedForeground mt-1">
              状态：
              {scenario.status === 'draft' ? (
                <span className="ml-2 px-2 py-1 text-xs rounded bg-amber-50 text-amber-700 border border-amber-200">
                  草稿
                </span>
              ) : (
                <span className="ml-2 px-2 py-1 text-xs rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                  已提交
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={() => router.push('/ai-scenarios')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回
            </Button>
            <Button
              variant="secondary"
              onClick={() => router.push(`/ai-scenarios/${scenario.id}/edit`)}
              disabled={scenario.status !== 'draft'}
            >
              <Pencil className="w-4 h-4 mr-2" />
              编辑
            </Button>
            <Button
              variant="secondary"
              onClick={async () => {
                if (!confirm('确定提交该场景吗？提交后将不可编辑。')) return;
                try {
                  setLoading(true);
                  await submitAIScenario(scenario.id);
                  await load();
                } catch (e: any) {
                  setError(e?.message || '提交失败');
                } finally {
                  setLoading(false);
                }
              }}
              disabled={scenario.status !== 'draft'}
            >
              <Send className="w-4 h-4 mr-2" />
              提交
            </Button>
            <Button
              variant="destructive"
              onClick={async () => {
                if (!confirm('确定删除该草稿吗？此操作不可撤销。')) return;
                try {
                  setLoading(true);
                  await deleteAIScenario(scenario.id);
                  router.push('/ai-scenarios');
                } catch (e: any) {
                  setError(e?.message || '删除失败');
                } finally {
                  setLoading(false);
                }
              }}
              disabled={scenario.status !== 'draft'}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              删除
            </Button>
          </div>
        </div>

        {error && <ErrorMessage message={error} type="error" onClose={() => setError(null)} />}

        <Card className="p-6 space-y-4">
          <h2 className="text-lg font-semibold text-foreground">课题情况简介</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-mutedForeground">场景领域</div>
              <div className="text-foreground font-medium">{scenario.domain}</div>
            </div>
            <div>
              <div className="text-mutedForeground">应用企业</div>
              <div className="text-foreground font-medium">{scenario.app_company || '-'}</div>
            </div>
            <div className="md:col-span-2">
              <div className="text-mutedForeground">所属类别</div>
              <div className="text-foreground font-medium">{(scenario.categories || []).join(' / ') || '-'}</div>
            </div>
            <div className="md:col-span-2">
              <div className="text-mutedForeground">承建平台</div>
              <div className="text-foreground font-medium">{scenario.platform || '-'}</div>
            </div>
          </div>
        </Card>

        <Card className="p-6 space-y-4">
          <h2 className="text-lg font-semibold text-foreground">内容描述</h2>
          <div className="space-y-3 text-sm">
            <div>
              <div className="text-mutedForeground mb-1">背景（场景痛点）</div>
              <div className="whitespace-pre-wrap text-foreground">{scenario.pain_points}</div>
            </div>
            <div>
              <div className="text-mutedForeground mb-1">拟解决的问题</div>
              <div className="whitespace-pre-wrap text-foreground">{scenario.problems_to_solve}</div>
            </div>
            <div>
              <div className="text-mutedForeground mb-1">预期成果</div>
              <div className="whitespace-pre-wrap text-foreground">{scenario.expected_outcomes}</div>
            </div>
          </div>
        </Card>

        <Card className="p-6 space-y-4">
          <h2 className="text-lg font-semibold text-foreground">工作思路及内容</h2>
          <div className="space-y-3 text-sm">
            <div>
              <div className="text-mutedForeground mb-1">实现方式</div>
              <div className="whitespace-pre-wrap text-foreground">{scenario.implementation_approach}</div>
            </div>
            <div>
              <div className="text-mutedForeground mb-1">技术路线</div>
              <div className="whitespace-pre-wrap text-foreground">{scenario.technical_route || '-'}</div>
            </div>
            <div>
              <div className="text-mutedForeground mb-1">计划安排</div>
              <div className="whitespace-pre-wrap text-foreground">{scenario.plan_schedule}</div>
            </div>
          </div>
        </Card>

        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">附件/截图</h2>
            <label className="inline-flex items-center gap-2 text-sm">
              <input
                type="file"
                multiple
                className="hidden"
                disabled={scenario.status !== 'draft'}
                onChange={(e) => handleUpload(e.target.files)}
              />
              <Button variant="secondary" disabled={scenario.status !== 'draft' || loading}>
                <Upload className="w-4 h-4 mr-2" />
                上传附件
              </Button>
            </label>
          </div>

          <div className="text-xs text-mutedForeground">
            提示：V1 仅允许在“草稿”状态上传/删除附件；已提交后只允许下载查看。
          </div>

          <div className="overflow-hidden border border-border rounded-md">
            <Table>
              <TableHeader>
                <TableRow hover={false}>
                  <TableHead>文件名</TableHead>
                  <TableHead>大小</TableHead>
                  <TableHead>上传时间</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow hover={false}>
                    <TableCell colSpan={4} className="text-center text-mutedForeground">
                      加载中...
                    </TableCell>
                  </TableRow>
                ) : attachments.length === 0 ? (
                  <TableRow hover={false}>
                    <TableCell colSpan={4} className="text-center text-mutedForeground">
                      暂无附件
                    </TableCell>
                  </TableRow>
                ) : (
                  attachments.map((row) => (
                    <TableRow key={row.id} hover={true}>
                      <TableCell className="max-w-[360px] truncate">{row.file_name}</TableCell>
                      <TableCell>{formatKb(row.size)}</TableCell>
                      <TableCell>{new Date(row.created_at).toLocaleString()}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => window.open(getAttachmentDownloadUrl(row.id), '_blank')}
                            title="下载"
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            disabled={scenario.status !== 'draft'}
                            onClick={async () => {
                              if (!confirm('确定删除该附件吗？')) return;
                              try {
                                setLoading(true);
                                await deleteAttachment(row.id);
                                await load();
                              } catch (e: any) {
                                setError(e?.message || '删除附件失败');
                              } finally {
                                setLoading(false);
                              }
                            }}
                            title="删除"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </Card>
      </div>
    </AuthGuard>
  );
}

