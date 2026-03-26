'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGuard } from '@/components/AuthGuard';
import ErrorMessage from '@/components/ErrorMessage';
import { Button } from '@/components/UI/Button';
import { Input } from '@/components/UI/Input';
import { Card } from '@/components/UI/Card';
import { createAIScenario } from '@/lib/api/aiScenarios';
import { Save, X } from 'lucide-react';

export default function CreateAIScenarioPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const created = await createAIScenario({
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
      // 用于面包屑展示（可选）
      try {
        sessionStorage.setItem(`ai_scenario_name_${created.id}`, `${created.domain}`);
      } catch {}
      router.push(`/ai-scenarios/${created.id}/edit`);
    } catch (e: any) {
      setError(e?.message || '创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <div className="space-y-6 max-w-5xl mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">新建场景</h1>
            <p className="text-sm text-mutedForeground mt-1">先创建为草稿，后续可上传附件与提交</p>
          </div>
          <Button variant="secondary" onClick={() => router.back()}>
            <X className="w-4 h-4 mr-2" />
            返回
          </Button>
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
                  placeholder="如：营销服务"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">应用企业</label>
                <Input
                  value={form.app_company}
                  onChange={(e) => setForm((p) => ({ ...p, app_company: e.target.value }))}
                  placeholder="如：化工事业部-工程事业部"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">所属类别（用逗号/换行分隔） *</label>
                <textarea
                  className="w-full min-h-[80px] rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={form.categoriesText}
                  onChange={(e) => setForm((p) => ({ ...p, categoriesText: e.target.value }))}
                  placeholder="如：数据分析、根因分析及操作指导、预测与决策"
                  required
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">承建平台</label>
                <Input
                  value={form.platform}
                  onChange={(e) => setForm((p) => ({ ...p, platform: e.target.value }))}
                  placeholder="如：中国中化人工智能平台"
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
                  className="w-full min-h-[110px] rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={form.pain_points}
                  onChange={(e) => setForm((p) => ({ ...p, pain_points: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">拟解决的问题 *</label>
                <textarea
                  className="w-full min-h-[110px] rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={form.problems_to_solve}
                  onChange={(e) => setForm((p) => ({ ...p, problems_to_solve: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">预期成果 *</label>
                <textarea
                  className="w-full min-h-[110px] rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={form.expected_outcomes}
                  onChange={(e) => setForm((p) => ({ ...p, expected_outcomes: e.target.value }))}
                  required
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
                  className="w-full min-h-[140px] rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={form.implementation_approach}
                  onChange={(e) => setForm((p) => ({ ...p, implementation_approach: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">技术路线</label>
                <textarea
                  className="w-full min-h-[90px] rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={form.technical_route}
                  onChange={(e) => setForm((p) => ({ ...p, technical_route: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">计划安排 *</label>
                <textarea
                  className="w-full min-h-[90px] rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={form.plan_schedule}
                  onChange={(e) => setForm((p) => ({ ...p, plan_schedule: e.target.value }))}
                  required
                />
              </div>
            </div>
          </Card>

          <div className="flex items-center justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => router.push('/ai-scenarios')}>
              取消
            </Button>
            <Button type="submit" disabled={loading}>
              <Save className="w-4 h-4 mr-2" />
              {loading ? '保存中...' : '保存草稿'}
            </Button>
          </div>
        </form>
      </div>
    </AuthGuard>
  );
}

