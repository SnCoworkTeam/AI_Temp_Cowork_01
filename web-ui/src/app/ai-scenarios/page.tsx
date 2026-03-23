'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/AuthGuard';
import ErrorMessage from '@/components/ErrorMessage';
import { Button } from '@/components/UI/Button';
import { Input } from '@/components/UI/Input';
import { Card } from '@/components/UI/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/UI/Table';
import { Plus, Search, RefreshCw, Eye, Pencil, Trash2, Send } from 'lucide-react';
import {
  AIScenario,
  AIScenarioStatus,
  deleteAIScenario,
  listAIScenarios,
  submitAIScenario,
} from '@/lib/api/aiScenarios';

export default function AIScenariosPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<AIScenario[]>([]);
  const [total, setTotal] = useState(0);

  const [page, setPage] = useState(1);
  const pageSize = 10;

  const [keyword, setKeyword] = useState('');
  const [status, setStatus] = useState<AIScenarioStatus | ''>('');
  const [domain, setDomain] = useState('');

  const renderStatus = (s: AIScenarioStatus) =>
    s === 'draft' ? (
      <span className="px-2 py-1 text-xs rounded bg-amber-50 text-amber-700 border border-amber-200">
        草稿
      </span>
    ) : (
      <span className="px-2 py-1 text-xs rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
        已提交
      </span>
    );

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listAIScenarios({
        page,
        page_size: pageSize,
        keyword: keyword || undefined,
        status: status || undefined,
        domain: domain || undefined,
      });
      setItems(res.items || []);
      setTotal(res.total || 0);
    } catch (e: any) {
      setError(e?.message || '加载场景列表失败');
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, status]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <AuthGuard>
      <div className="space-y-6 max-w-6xl mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">场景库</h1>
            <p className="text-sm text-mutedForeground mt-1">收集与管理 AI 应用场景（V1）</p>
          </div>
          <Button onClick={() => router.push('/ai-scenarios/create')}>
            <Plus className="w-4 h-4 mr-2" />
            新建场景
          </Button>
        </div>

        {error && <ErrorMessage message={error} type="error" onClose={() => setError(null)} />}

        <Card className="p-4">
          <div className="flex flex-col md:flex-row gap-3 md:items-center md:justify-between">
            <div className="flex flex-col md:flex-row gap-3 md:items-center">
              <div className="w-full md:w-80">
                <Input
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="关键字搜索（痛点/问题/成果/实现方式等）"
                />
              </div>
              <div className="w-full md:w-56">
                <Input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="场景领域（可选）" />
              </div>
              <select
                className="h-10 px-3 rounded-md border border-border bg-background text-sm"
                value={status}
                onChange={(e) => {
                  setPage(1);
                  setStatus(e.target.value as any);
                }}
              >
                <option value="">全部状态</option>
                <option value="draft">草稿</option>
                <option value="submitted">已提交</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                onClick={() => {
                  setPage(1);
                  load();
                }}
              >
                <Search className="w-4 h-4 mr-2" />
                搜索
              </Button>
              <Button variant="secondary" onClick={load}>
                <RefreshCw className="w-4 h-4 mr-2" />
                刷新
              </Button>
            </div>
          </div>
        </Card>

        <Card className="p-0 overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow hover={false}>
                <TableHead>场景领域</TableHead>
                <TableHead>所属类别</TableHead>
                <TableHead>应用企业</TableHead>
                <TableHead>承建平台</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>更新时间</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow hover={false}>
                  <TableCell colSpan={7} className="text-center text-mutedForeground">
                    加载中...
                  </TableCell>
                </TableRow>
              ) : items.length === 0 ? (
                <TableRow hover={false}>
                  <TableCell colSpan={7} className="text-center text-mutedForeground">
                    暂无场景数据
                  </TableCell>
                </TableRow>
              ) : (
                items.map((row) => (
                  <TableRow key={row.id} hover={true}>
                    <TableCell>{row.domain}</TableCell>
                    <TableCell className="max-w-[320px] truncate">
                      {(row.categories || []).join(' / ') || '-'}
                    </TableCell>
                    <TableCell>{row.app_company || '-'}</TableCell>
                    <TableCell>{row.platform || '-'}</TableCell>
                    <TableCell>{renderStatus(row.status)}</TableCell>
                    <TableCell>{new Date(row.updated_at).toLocaleString()}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => router.push(`/ai-scenarios/${row.id}`)}
                          title="查看"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => router.push(`/ai-scenarios/${row.id}/edit`)}
                          title="编辑"
                          disabled={row.status !== 'draft'}
                        >
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={async () => {
                            if (!confirm('确定提交该场景吗？提交后将不可编辑。')) return;
                            try {
                              setLoading(true);
                              await submitAIScenario(row.id);
                              await load();
                            } catch (e: any) {
                              setError(e?.message || '提交失败');
                            } finally {
                              setLoading(false);
                            }
                          }}
                          title="提交"
                          disabled={row.status !== 'draft'}
                        >
                          <Send className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={async () => {
                            if (!confirm('确定删除该草稿吗？此操作不可撤销。')) return;
                            try {
                              setLoading(true);
                              await deleteAIScenario(row.id);
                              await load();
                            } catch (e: any) {
                              setError(e?.message || '删除失败');
                            } finally {
                              setLoading(false);
                            }
                          }}
                          title="删除"
                          disabled={row.status !== 'draft'}
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
          <div className="flex items-center justify-between px-4 py-3 border-t border-border text-sm text-mutedForeground">
            <div>
              共 <span className="text-foreground font-medium">{total}</span> 条
            </div>
            <div className="flex items-center gap-2">
              <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                上一页
              </Button>
              <span>
                {page} / {totalPages}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                下一页
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </AuthGuard>
  );
}

