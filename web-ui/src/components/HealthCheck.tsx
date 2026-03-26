'use client';

interface HealthCheckProps {
  services: Record<string, boolean>;
}

export function HealthCheck({ services }: HealthCheckProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">服务状态</h2>
      <div className="space-y-2">
        {Object.entries(services).map(([name, status]) => (
          <div key={name} className="flex items-center justify-between">
            <span className="text-gray-700 capitalize">{name}</span>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                status ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}
            >
              {status ? '运行中' : '离线'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
