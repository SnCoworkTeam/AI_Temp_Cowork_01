'use client';

import { useEffect, useState } from 'react';
import {
  ServiceMonitoringData,
  getMCPGatewayMonitoring,
  getWorkflowEngineMonitoring,
  getAuthServiceMonitoring,
} from '@/lib/api/monitoring';
import { ServiceStatus } from '@/components/ServiceStatus';
import Link from 'next/link';

const MONITORING_URLS = {
  mcpGateway: '/api/mcp/monitoring',
  workflowEngine: '/api/v1/monitoring',
  authService: '/api/auth-monitoring',
};

export default function ServicesMonitoringPage() {
  const [services, setServices] = useState<ServiceMonitoringData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchServices = async () => {
    try {
      setLoading(true);
      const [mcpGateway, workflowEngine, authService] = await Promise.allSettled([
        getMCPGatewayMonitoring(),
        getWorkflowEngineMonitoring(),
        getAuthServiceMonitoring(),
      ]);

      const servicesData: ServiceMonitoringData[] = [];
      if (mcpGateway.status === 'fulfilled') {
        servicesData.push(mcpGateway.value);
      }
      if (workflowEngine.status === 'fulfilled') {
        servicesData.push(workflowEngine.value);
      }
      if (authService.status === 'fulfilled') {
        servicesData.push(authService.value);
      }

      setServices(servicesData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setServices([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();
    const interval = setInterval(fetchServices, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading && services.length === 0) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            <div className="h-64 bg-gray-200 rounded"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* 页面标题和导航 */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <Link href="/admin/monitoring" className="text-blue-600 hover:text-blue-800">
              ← 返回总览
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">服务状态监控</h1>
          </div>
          <button
            onClick={fetchServices}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            刷新
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-red-500 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* 服务状态列表 */}
      <div className="space-y-6">
        {services.map((service) => (
          <ServiceStatus
            key={service.service_name}
            serviceName={service.service_name}
            monitoringUrl={
              service.service_name === 'mcp-gateway'
                ? MONITORING_URLS.mcpGateway
                : service.service_name === 'workflow-engine'
                  ? MONITORING_URLS.workflowEngine
                  : MONITORING_URLS.authService
            }
            refreshInterval={5000}
          />
        ))}
      </div>
    </div>
  );
}
