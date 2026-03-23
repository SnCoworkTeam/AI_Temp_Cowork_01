import React, { useState, useEffect } from 'react';
import { uploadFile, generateReport, getReport, Report } from '../api/client';
import { useNavigate } from 'react-router-dom';

const UploadPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState<{ current: number; total: number; percent: number } | null>(null);
  const navigate = useNavigate();
  const [status, setStatus] = useState<boolean>(false);
  const [customPrompt, setCustomPrompt] = useState<string>('');

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setLoading(true);
      setStatus(false); // Reset status
      try {
        await uploadFile(e.target.files[0], 'data_file');
        setStatus(true);
        alert("文件上传成功！"); // Explicit feedback
      } catch (error: any) {
        console.error(error);
        setStatus(false);
        if (error.response && error.response.status === 404) {
          alert('上传失败：找不到上传接口 (404)。请确认后端服务已启动。');
        } else {
          alert('上传失败：' + (error.message || '未知错误'));
        }
      } finally {
        setLoading(false);
        // Clear the input value so the same file can be selected again if needed
        e.target.value = ''; 
      }
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setProgress({ current: 0, total: 0, percent: 0 });
    try {
      const today = new Date().toISOString().split('T')[0];
      // Start generation task
      const initialReport = await generateReport({
        title: '《行业产品报告》',
        period_start: today,
        period_end: today,
        custom_prompt: customPrompt
      });

      // Poll for progress
      const reportId = initialReport.id;
      const pollInterval = setInterval(async () => {
        try {
          const report = await getReport(reportId);
          
          if (report.status === 'completed') {
            clearInterval(pollInterval);
            navigate(`/reports/${report.id}`);
          } else if (report.status === 'failed') {
            clearInterval(pollInterval);
            setGenerating(false);
            alert('生成报告失败，请检查后端日志');
          } else {
            // Update progress
            setProgress({
              current: report.processed_rows || 0,
              total: report.total_rows || 0,
              percent: report.progress || 0
            });
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 2000); // Check every 2 seconds

    } catch (error) {
      console.error(error);
      alert('无法启动生成任务');
      setGenerating(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">数据上传</h1>
      <div className="bg-white p-8 rounded-lg shadow-sm border">
        <h2 className="text-lg font-semibold mb-4">上传综合数据文件</h2>
        <p className="text-gray-500 mb-4 text-sm">
          请上传包含以下列的 Excel/CSV 文件：本周资讯价格、上周资讯价格、本周销售价格、上周销售价格、本周采购价格、上周采购价格
        </p>
        <div className="flex items-center justify-center w-full">
          <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <svg className="w-8 h-8 mb-4 text-gray-500" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/>
              </svg>
              <p className="mb-2 text-sm text-gray-500"><span className="font-semibold">点击上传</span> 或拖拽文件</p>
              <p className="text-xs text-gray-500">支持 .xlsx, .csv</p>
            </div>
            <input 
              type="file" 
              className="hidden" 
              onChange={handleUpload}
              accept=".xlsx,.xls,.csv"
              disabled={loading} 
            />
          </label>
        </div>
        {status && <p className="text-green-600 mt-4 text-center font-medium">文件上传成功！</p>}
      </div>

      <div className="mt-6 bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-lg font-semibold mb-2">分析提示词（可选）</h2>
        <p className="text-gray-500 mb-2 text-sm">
          您可以输入额外的指示来引导 AI 进行分析，例如："请重点关注销售价格的变化" 或 "语气要更加专业"。
        </p>
        <textarea
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          rows={3}
          placeholder="请输入关键提示词..."
          value={customPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
        />
      </div>
      
      <div className="mt-8 flex flex-col items-end">
        {generating && progress && (
          <div className="w-full mb-4">
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-blue-700">正在生成报告...</span>
              <span className="text-sm font-medium text-blue-700">{progress.percent}% ({progress.current}/{progress.total})</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div className="bg-blue-600 h-2.5 rounded-full transition-all duration-500" style={{ width: `${progress.percent}%` }}></div>
            </div>
          </div>
        )}
        
        <button
          onClick={handleGenerate}
          disabled={!status || generating}
          className={`px-6 py-2 rounded-lg text-white font-medium ${
            status ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'
          }`}
        >
          {generating ? '生成中...' : '生成报告'}
        </button>
      </div>
    </div>
  );
};

export default UploadPage;
