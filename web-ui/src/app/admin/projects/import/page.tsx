'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, FileSpreadsheet, CheckCircle, XCircle } from 'lucide-react';
import { getAccessToken } from '@/lib/auth';

export default function ImportProjectPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string; data?: any } | null>(
    null
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      const apiUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://43.143.139.197:8080';
      const token = getAccessToken();

      const response = await fetch(`${apiUrl}/api/v1/projects/import/excel`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setResult({
          success: true,
          message: `成功导入 ${data.created || 0} 个项目（共找到 ${data.total_found || 0} 个）`,
          data,
        });
        setTimeout(() => {
          router.push('/admin/projects');
        }, 2000);
      } else {
        setResult({
          success: false,
          message: data.detail || '导入失败',
        });
      }
    } catch (error) {
      setResult({
        success: false,
        message: `导入失败: ${error}`,
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-6 py-5 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900">导入Excel项目</h1>
          <p className="text-sm text-gray-600 mt-1">
            上传2025项目周月进度报告.xlsx文件，系统将自动解析并创建项目
          </p>
        </div>
        <div className="p-6 space-y-6">
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-blue-400 hover:bg-blue-50/50 transition-all duration-200">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
              <FileSpreadsheet className="h-8 w-8 text-blue-600" />
            </div>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer inline-block">
              <span className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 inline-flex items-center gap-2 font-medium shadow-sm">
                <Upload className="h-4 w-4" />
                选择Excel文件
              </span>
            </label>
            {file && (
              <p className="mt-4 text-sm text-gray-600 font-medium">
                已选择: <span className="text-blue-600">{file.name}</span>
              </p>
            )}
          </div>

          {result && (
            <div
              className={`p-4 rounded-lg flex items-center gap-3 ${
                result.success
                  ? 'bg-gradient-to-r from-green-50 to-emerald-50 text-green-800 border border-green-200'
                  : 'bg-gradient-to-r from-red-50 to-rose-50 text-red-800 border border-red-200'
              }`}
            >
              <div
                className={`p-1.5 rounded-full ${result.success ? 'bg-green-100' : 'bg-red-100'}`}
              >
                {result.success ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600" />
                )}
              </div>
              <span className="font-medium">{result.message}</span>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={() => router.back()}
              className="px-6 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-medium shadow-sm"
            >
              取消
            </button>
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-md hover:shadow-lg flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  上传中...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  开始导入
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
