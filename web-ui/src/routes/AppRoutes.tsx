import React from 'react';
import { Routes, Route } from 'react-router-dom';

// 导入页面组件
import { KnowledgeGraphView } from '../pages/KnowledgeGraph/KnowledgeGraphView';
import { Dashboard } from '../pages/Dashboard/Dashboard';
import { EnterpriseArchitectureOverview } from '../pages/EnterpriseArchitecture/Overview';
import { ArchitectureRelationships } from '../pages/EnterpriseArchitecture/Relationships';
import { ComponentShowcase } from '../pages/Components/ComponentShowcase';
// 这些组件已迁移到 Next.js App Router，不再需要
// import { KnowledgeBaseDetail } from '../pages/KnowledgeBase/KnowledgeBaseDetail';
// import { DocumentDetail } from '../pages/Document/DocumentDetail';

// 如果已有其他页面，在这里导入
// import { ChatInterface } from '../pages/Chat/ChatInterface';
// import { LoginForm } from '../pages/Auth/LoginForm';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* 仪表板 */}
      <Route path="/dashboard" element={<Dashboard />} />

      {/* 知识图谱 */}
      <Route path="/knowledge-graph" element={<KnowledgeGraphView />} />

      {/* 企业架构 */}
      <Route path="/enterprise-architecture" element={<EnterpriseArchitectureOverview />} />
      <Route
        path="/enterprise-architecture/relationships"
        element={<ArchitectureRelationships />}
      />

      {/* 组件展示 */}
      <Route path="/components" element={<ComponentShowcase />} />

      {/* 知识库 - 已迁移到 Next.js App Router */}
      {/* <Route path="/knowledge-bases/:id" element={<KnowledgeBaseDetail />} /> */}

      {/* 文档 - 已迁移到 Next.js App Router */}
      {/* <Route path="/documents/:id" element={<DocumentDetail />} /> */}

      {/* 默认路由 - 可以重定向到仪表板 */}
      <Route path="/" element={<Dashboard />} />
    </Routes>
  );
};
