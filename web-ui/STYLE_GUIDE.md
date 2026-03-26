# LuminaOS 平台样式指南

## 配色方案

### 主色（科技蓝）
- **主色**: `#2563eb`
- **用途**: 主要按钮、链接、重要信息
- **Tailwind类**: `bg-primary`, `text-primary`, `border-primary`

### 辅色（活力绿）
- **辅色**: `#10b981`
- **用途**: 成功状态、确认操作、积极反馈
- **Tailwind类**: `bg-secondary`, `text-secondary`, `border-secondary`

### 强调色（警示黄）
- **强调色**: `#f59e0b`
- **用途**: 警告信息、重要提示、需要关注的内容
- **Tailwind类**: `bg-accent`, `text-accent`, `border-accent`

## 字体

### 标题字体（思源黑体 Bold）
```tsx
<h1 className="font-title font-bold">标题</h1>
```

### 正文字体（思源黑体 Regular）
```tsx
<p className="font-body">正文内容</p>
```

### 代码字体（JetBrains Mono）
```tsx
<code className="font-code">代码内容</code>
```

## 动画效果

### 淡入动画
```tsx
<div className="animate-fade-in">内容</div>
```

### 滑入动画
```tsx
<div className="animate-slide-in">内容</div>
```

### 慢速脉冲
```tsx
<div className="animate-pulse-slow">内容</div>
```

## 视觉元素

### 卡片阴影
```tsx
<div className="card-elevated p-4 rounded-lg">
  卡片内容
</div>
```

### 渐变背景
```tsx
<div className="gradient-primary text-white p-4 rounded-lg">
  主色渐变
</div>

<div className="gradient-secondary text-white p-4 rounded-lg">
  辅色渐变
</div>

<div className="gradient-accent text-white p-4 rounded-lg">
  强调色渐变
</div>
```

### 品牌按钮
```tsx
<button className="btn-primary px-4 py-2 rounded-lg">
  主要按钮
</button>

<button className="btn-secondary px-4 py-2 rounded-lg">
  次要按钮
</button>

<button className="btn-accent px-4 py-2 rounded-lg">
  强调按钮
</button>
```

## 数据可视化

### 图表容器
```tsx
<div className="data-chart">
  {/* 图表内容 */}
</div>
```

## 使用示例

### 信息卡片
```tsx
<div className="card-elevated p-6 rounded-lg bg-card animate-fade-in">
  <h2 className="font-title font-bold text-xl text-foreground mb-4">
    标题
  </h2>
  <p className="font-body text-mutedForeground">
    内容描述
  </p>
  <div className="mt-4 flex gap-2">
    <button className="btn-primary px-4 py-2 rounded-lg">
      操作
    </button>
  </div>
</div>
```

### 数据统计卡片
```tsx
<div className="card-elevated p-6 rounded-lg bg-gradient-primary text-white animate-slide-in">
  <div className="flex items-center justify-between">
    <div>
      <p className="text-sm opacity-90">总用户数</p>
      <p className="text-3xl font-title font-bold mt-2">1,234</p>
    </div>
    <div className="text-4xl">📊</div>
  </div>
</div>
```

### 警告提示
```tsx
<div className="bg-accent/10 border border-accent rounded-lg p-4 animate-fade-in">
  <div className="flex items-center gap-2">
    <span className="text-accent text-xl">⚠️</span>
    <p className="font-body text-foreground">
      这是一个警告提示
    </p>
  </div>
</div>
```

### 成功提示
```tsx
<div className="bg-secondary/10 border border-secondary rounded-lg p-4 animate-fade-in">
  <div className="flex items-center gap-2">
    <span className="text-secondary text-xl">✓</span>
    <p className="font-body text-foreground">
      操作成功完成
    </p>
  </div>
</div>
```



















