'use client';

import React, { useState } from 'react';
import { DataBrowser } from '@/components/Database/DataBrowser';
import { QueryExecutor } from '@/components/Database/QueryExecutor';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/UI/Tabs';

export default function DatabaseTablesPage() {
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('browser');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">数据表管理</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">浏览和管理数据库表结构及数据</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList>
          <TabsTrigger value="browser">数据浏览器</TabsTrigger>
          <TabsTrigger value="query">SQL查询</TabsTrigger>
        </TabsList>
        <TabsContent value="browser">
          <DataBrowser
            onSelectTable={setSelectedTable}
            onViewData={(tableName) => {
              // 切换到查询标签并自动填充表名
              setSelectedTable(tableName);
              setActiveTab('query');
            }}
          />
        </TabsContent>
        <TabsContent value="query">
          <QueryExecutor initialTable={selectedTable} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
