import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getReport, Report } from '../api/client';
import ReactECharts from 'echarts-for-react';

const ReportPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      getReport(id)
        .then(setReport)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) return <div className="p-8 text-center">加载中...</div>;
  if (!report) return <div className="p-8 text-center text-red-600">未找到报告</div>;

  const handleDownload = async () => {
    if (!report || !report.file_path) {
      alert('无法下载：报告文件路径为空');
      return;
    }

    try {
      // Fetch the file as a blob
      const response = await fetch(`http://localhost:8000/api/reports/download/${report.file_path}`);
      if (!response.ok) throw new Error('下载失败');
      const blob = await response.blob();

      // Try to use the File System Access API (showSaveFilePicker)
      // @ts-ignore
      if (window.showSaveFilePicker) {
        try {
          // @ts-ignore
          const handle = await window.showSaveFilePicker({
            suggestedName: report.file_path,
            types: [{
              description: 'Excel File',
              accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
            }],
          });
          const writable = await handle.createWritable();
          await writable.write(blob);
          await writable.close();
          return;
        } catch (err: any) {
          // User cancelled or error, fallback to default download if not aborted
          if (err.name === 'AbortError') return;
        }
      }

      // Fallback to <a> tag download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = report.file_path;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (error) {
      console.error(error);
      alert('下载出错');
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8 border-b pb-4 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{report.title}</h1>
          <p className="text-gray-500 mt-2">
            周期: {report.period_start} 至 {report.period_end}
          </p>
        </div>
        <button
          onClick={handleDownload}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          下载报告
        </button>
      </div>

      <div className="grid grid-cols-1 gap-8">
        <div className="bg-white p-6 rounded-lg shadow border">
          <h2 className="text-xl font-bold mb-4">报告预览</h2>
          <div className="overflow-x-auto excel-preview" dangerouslySetInnerHTML={{ __html: report.html_content || '' }} />
        </div>
      </div>
    </div>
  );
};

export default ReportPage;
