'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/AuthGuard';
import ErrorMessage from '@/components/ErrorMessage';
import { Button } from '@/components/UI/Button';
import { Input } from '@/components/UI/Input';
import { Card } from '@/components/UI/Card';
import { Save, X, ArrowLeft } from 'lucide-react';
import { getAIScenario, updateAIScenario } from '@/lib/api/aiScenarios';

export default function EditAIScenarioPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const router = useRouter();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<'draft' | 'submitted'>('draft');

  const [form, setForm] = useState({
    domain: '',
    categoriesText: '',
    app_company: '',
    platform: '',
    pain_points: '',
    problems_to_solve: '',
    expected_outcomes: '',
    implementation_approach: '',
    technical_route: '',
    plan_schedule: '',
  });

  const parseCategories = () =>
    form.categoriesText
      .split(/[\n,，/、]+/g)
      .map((s) => s.trim())
      .filter(Boolean);

  useEffect(() => {
    const load = async () => {
      if (!id) return;
      try {
        setLoading(true);
        setError(null);
        const s = await getAIScenario(id);
        setStatus(s.status);
        setForm({
          domain: s.domain || '',
          categoriesText: (s.categories || []).join('\n'),
          app_company: s.app_company || '',
          platform: s.platform || '',
          pain_points: s.pain_points || '',
          problems_to_solve: s.problems_to_solve || '',
          expected_outcomes: s.expected_outcomes || '',
          implementation_approach: s.implementation_approach || '',
          technical_route: s.technical_route || '',
          plan_schedule: s.plan_schedule || '',
        });
        try {
          sessionStorage.setItem(`ai_scenario_name_${s.id}`, `${s.domain}`);
        } catch {}
      } catch (e: any) {
        setError(e?.message || '加载失败');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const disabled = status !== 'draft';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      await updateAIScenario(id, {
        domain: form.domain,
        categories: parseCategories(),
        app_company: form.app_company || undefined,
        platform: form.platform || undefined,
        pain_points: form.pain_points,
        problems_to_solve: form.problems_to_solve,
        expected_outcomes: form.expected_outcomes,
        implementation_approach: form.implementation_approach,
        technical_route: form.technical_route || undefined,
        plan_schedule: form.plan_schedule,
      });
      router.push(`/ai-scenarios/${id}`);
    } catch (e: any) {
      setError(e?.message || '保存失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <div className="space-y-6 max-w-5xl mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">编辑场景</h1>
            <p className="text-sm text-mutedForeground mt-1">
              {disabled ? '该场景已提交，当前仅支持查看' : '编辑草稿内容，保存后可继续上传附件并提交'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={() => router.push(`/ai-scenarios/${id}`)}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回详情
            </Button>
            <Button variant="secondary" onClick={() => router.back()}>
              <X className="w-4 h-4 mr-2" />
              取消
            </Button>
          </div>
        </div>

        {error && <ErrorMessage message={error} type="error" onClose={() => setError(null)} />}

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card className="p-6 space-y-4">
            <h2 className="text-lg font-semibold text-foreground">课题情况简介</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">场景领域 *</label>
                <Input
                  value={form.domain}
                  onChange={(e) => setForm((p) => ({ ...p, domain: e.target.value }))}
                  required
                  disabled={disabled}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">应用企业</label>
                <Input
                  value={form.app_company}
                  onChange={(e) => setForm((p) => ({ ...p, app_company: e.target.value }))}
                  disabled={disabled}
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">所属类别（用逗号/换行分隔） *</label>
                <textarea
                  className="w-full min-h-[80px] rounded-md border border-border bg-background px-3 py-2 text-sm disabled:opacity-60"
                  value={form.categoriesText}
                  onChange={(e) => setForm((p) => ({ ...p, categoriesText: e.target.value }))}
                  required
                  disabled={disabled}
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">承建平台</label>
                <Input
                  value={form.platform}
                  onChange={(e) => setForm((p) => ({ ...p, platform: e.target.value }))}
                  disabled={disabled}
                />
              </div>
            </div>
          </Card>

          <Card className="p-6 space-y-4">
            <h2 className="text-lg font-semibold text-foreground">内容描述</h2>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">背景（场景痛点） *</label>
                <textarea
                  className="w-full min-h-[110px] rounded-md border border-border bg-background px-3 py-2 text-sm disabled:opacity-60"
                  value={form.pain_points}
                  onChange={(e) => setForm((p) => ({ ...p, pain_points: e.target.value }))}
                  required
                  disabled={disabled}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">拟解决的问题 *</label>
                <textarea
                  className="w-full min-h-[110px] rounded-md border border-border bg-background px-3 py-2 text-sm disabled:opacity-60"
                  value={form.problems_to_solve}
                  onChange={(e) => setForm((p) => ({ ...p, problems_to_solve: e.target.value }))}
                  required
                  disabled={disabled}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">预期成果 *</label>
                <textarea
                  className="w-full min-h-[110px] rounded-md border border-border bg-background px-3 py-2 text-sm disabled:opacity-60"
                  value={form.expected_outcomes}
                  onChange={(e) => setForm((p) => ({ ...p, expected_outcomes: e.target.value }))}
                  required
                  disabled={disabled}
                />
              </div>
            </div>
          </Card>

          <Card className="p-6 space-y-4">
            <h2 className="text-lg font-semibold text-foreground">工作思路及内容</h2>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">实现方式 *</label>
                <textarea
                  className="w-full min-h-[140px] rounded-md border border-border bg-background px-3 py-2 text-sm disabled:opacity-60"
                  value={form.implementation_approach}
                  onChange={(e) => setForm((p) => ({ ...p, implementation_approach: e.target.value }))}
                  required
                  disabled={disabled}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">技术路线</label>
                <textarea
                  className="w-full min-h-[90px] rounded-md border border-border bg-background px-3 py-2 text-sm disabled:opacity-60"
                  value={form.technical_route}
                  onChange={(e) => setForm((p) => ({ ...p, technical_route: e.target.value }))}
                  disabled={disabled}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">计划安排 *</label>
                <textarea
                  className="w-full min-h-[90px] rounded-md border border-border bg-background px-3 py-2 text-sm disabled:opacity-60"
                  value={form.plan_schedule}
                  onChange={(e) => setForm((p) => ({ ...p, plan_schedule: e.target.value }))}
                  required
                  disabled={disabled}
                />
              </div>
            </div>
          </Card>

          <div className="flex items-center justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => router.push(`/ai-scenarios/${id}`)}>
              取消
            </Button>
            <Button type="submit" disabled={loading || disabled}>
              <Save className="w-4 h-4 mr-2" />
              {loading ? '保存中...' : '保存'}
            </Button>
          </div>
        </form>
      </div>
    </AuthGuard>
  );
}

