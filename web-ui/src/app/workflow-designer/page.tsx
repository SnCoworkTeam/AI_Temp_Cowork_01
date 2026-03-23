'use client';

import { WorkflowDesigner } from '@/components/WorkflowDesigner';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

function WorkflowDesignerContent() {
  const searchParams = useSearchParams();
  const workflowId = searchParams.get('id') || undefined;

  return (
    <div className="h-screen w-screen">
      <WorkflowDesigner
        workflowId={workflowId}
        onSave={(id) => {
          console.log('Workflow saved:', id);
          // 可以在这里添加导航逻辑
        }}
      />
    </div>
  );
}

export default function WorkflowDesignerPage() {
  return (
    <Suspense
      fallback={<div className="h-screen w-screen flex items-center justify-center">加载中...</div>}
    >
      <WorkflowDesignerContent />
    </Suspense>
  );
}
