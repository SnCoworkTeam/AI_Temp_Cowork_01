/**
 * 协同界面页面
 */
'use client';

import { useState } from 'react';
import { CollaborativeInterface } from '@/components/CollaborativeInterface';
import { Input } from '@/components/UI/Input';
import { Button } from '@/components/UI/Button';

export default function CollaborativePage() {
  const [userInput, setUserInput] = useState('');
  const [submittedInput, setSubmittedInput] = useState('');

  const handleSubmit = () => {
    if (userInput.trim()) {
      setSubmittedInput(userInput);
    }
  };

  const handlePlanAssembled = (plan: any) => {
    console.log('执行计划已组装:', plan);
  };

  const handlePlanExecuted = (result: any) => {
    console.log('执行结果:', result);
    alert(`执行完成！状态: ${result.status}`);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">协同工作流界面</h1>

        <div className="mb-6">
          <div className="flex gap-2">
            <Input
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              placeholder="输入您的需求，例如：创建采购订单"
              className="flex-1"
            />
            <Button onClick={handleSubmit}>提交</Button>
          </div>
        </div>

        {submittedInput && (
          <CollaborativeInterface
            userInput={submittedInput}
            onPlanAssembled={handlePlanAssembled}
            onPlanExecuted={handlePlanExecuted}
          />
        )}
      </div>
    </div>
  );
}
