'use client'

import { useMemo } from 'react'
import { 
  BarChart3, 
  Search, 
  FileText, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle,
  Settings,
  Rocket,
  TrendingUp,
  Lightbulb,
  Target,
  Database,
  Building2,
  Users,
  Layers
} from 'lucide-react'

interface MessageContentProps {
  content: string
  isOwnMessage?: boolean
}

/**
 * 美化的消息内容组件
 * 支持Markdown格式、代码高亮、链接识别等
 */
export function MessageContent({ content, isOwnMessage = false }: MessageContentProps) {
  const formattedContent = useMemo(() => {
    if (!content) return ''
    
    let formatted = content
    
    // 1. 处理代码块（```code```）
    formatted = formatted.replace(
      /```(\w+)?\n([\s\S]*?)```/g,
      (match, lang, code) => {
        const language = lang || 'text'
        return `<pre class="code-block"><code class="language-${language}">${escapeHtml(code.trim())}</code></pre>`
      }
    )
    
    // 2. 处理行内代码（`code`）
    formatted = formatted.replace(
      /`([^`]+)`/g,
      '<code class="inline-code">$1</code>'
    )
    
    // 3. 处理链接（http:// 或 https://）
    formatted = formatted.replace(
      /(https?:\/\/[^\s]+)/g,
      '<a href="$1" target="_blank" rel="noopener noreferrer" class="message-link">$1</a>'
    )
    
    // 4. 处理粗体（**text**）
    formatted = formatted.replace(
      /\*\*(.+?)\*\*/g,
      '<strong>$1</strong>'
    )
    
    // 5. 处理斜体（*text*）
    formatted = formatted.replace(
      /(?<!\*)\*([^*]+?)\*(?!\*)/g,
      '<em>$1</em>'
    )
    
    // 6. 处理列表（- item 或 * item）- 改进列表解析，支持有序列表
    // 先处理无序列表（- item 或 * item）
    formatted = formatted.replace(
      /^[\-\*]\s+(.+)$/gm,
      '<li class="message-list-item">$1</li>'
    )
    
    // 处理有序列表（1. item），但排除已经被处理为关键发现项的行（包含 "-" 分隔符的）
    // 注意：关键发现项的处理在列表处理之前，所以这里不会匹配到它们
    formatted = formatted.replace(
      /^(\d+)\.\s+(.+)$/gm,
      (match, num, content) => {
        // 如果内容已经被处理为关键发现项，跳过
        if (content.includes('key-finding-item')) {
          return match
        }
        return `<li class="message-list-item message-list-ordered">${content}</li>`
      }
    )
    
    // 如果包含列表项，包装在ul/ol中（改进：按段落分组）
    if (formatted.includes('<li')) {
      // 将连续的列表项分组
      formatted = formatted.replace(
        /(<li[^>]*>.*?<\/li>)(?:\s*(?:<br\s*\/?>)?\s*(<li[^>]*>.*?<\/li>))*/g,
        (match) => {
          // 检查是否包含有序列表项
          const hasOrdered = match.includes('message-list-ordered')
          const listTag = hasOrdered ? 'ol' : 'ul'
          return `<${listTag} class="message-list ${hasOrdered ? 'message-list-ordered' : ''}">${match}</${listTag}>`
        }
      )
    }
    
    // 7. 处理标题（# title）- 支持状态图标和特殊格式
    formatted = formatted.replace(/^###\s+(.+)$/gm, '<h3 class="message-h3">$1</h3>')
    formatted = formatted.replace(/^##\s+(.+)$/gm, '<h2 class="message-h2">$1</h2>')
    formatted = formatted.replace(/^#\s+(.+)$/gm, '<h1 class="message-h1">$1</h1>')
    
    // 处理状态图标和特殊标记（在表格处理之前，避免影响表格解析）
    // 将emoji替换为SVG图标（使用lucide-react图标的SVG路径）
    formatted = formatted.replace(/✅/g, '<span class="status-icon status-success"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></span>')
    formatted = formatted.replace(/❌/g, '<span class="status-icon status-error"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg></span>')
    formatted = formatted.replace(/⚠️/g, '<span class="status-icon status-warning"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg></span>')
    formatted = formatted.replace(/📊/g, '<span class="status-icon status-info"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg></span>')
    formatted = formatted.replace(/🔍/g, '<span class="status-icon status-info"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></span>')
    formatted = formatted.replace(/🛠️/g, '<span class="status-icon status-info"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg></span>')
    formatted = formatted.replace(/📋/g, '<span class="status-icon status-info"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/></svg></span>')
    formatted = formatted.replace(/🚀/g, '<span class="status-icon status-success"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg></span>')
    formatted = formatted.replace(/📈/g, '<span class="status-icon status-success"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg></span>')
    formatted = formatted.replace(/💡/g, '<span class="status-icon status-info"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" x2="12" y1="2" y2="3"/><line x1="12" x2="12" y1="21" y2="22"/><line x1="4.22" x2="5.64" y1="4.22" y2="5.64"/><line x1="18.36" x2="19.78" y1="18.36" y2="19.78"/><line x1="2" x2="3" y1="12" y2="12"/><line x1="21" x2="22" y1="12" y2="12"/><line x1="4.22" x2="5.64" y1="19.78" y2="18.36"/><line x1="18.36" x2="19.78" y1="5.64" y2="4.22"/><circle cx="12" cy="12" r="5"/></svg></span>')
    formatted = formatted.replace(/🎯/g, '<span class="status-icon status-success"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg></span>')
    formatted = formatted.replace(/📚/g, '<span class="status-icon status-info"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg></span>')
    formatted = formatted.replace(/🏢/g, '<span class="status-icon status-info"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg></span>')
    formatted = formatted.replace(/🧹/g, '<span class="status-icon status-info"><svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg></span>')
    
    // 处理特殊格式的文本块（如 "任务状态: ❌ 部分失败"）- 使用更精确的正则
    formatted = formatted.replace(/(任务状态|执行状态|状态|成功智能体|核心问题)[：:]\s*([^\n<]+)/g, (match, label, status) => {
      const trimmedStatus = status.trim()
      const statusClass = trimmedStatus.includes('✅') || trimmedStatus.includes('成功') ? 'status-success' : 
                         trimmedStatus.includes('❌') || trimmedStatus.includes('失败') ? 'status-error' : 
                         trimmedStatus.includes('⚠️') || trimmedStatus.includes('警告') ? 'status-warning' : 'status-info'
      return `<span class="status-badge ${statusClass}">${label}：${trimmedStatus}</span>`
    })
    
    // 处理分析报告中的特殊区块（如 "总体状态： ❌ 执行失败"）
    formatted = formatted.replace(/(总体状态|失败原因|恢复建议|执行概况|关键洞察|改进建议)[：:]\s*([^\n<]+)/g, (match, label, value) => {
      const trimmedValue = value.trim()
      const valueClass = trimmedValue.includes('✅') || trimmedValue.includes('成功') ? 'status-success' : 
                        trimmedValue.includes('❌') || trimmedValue.includes('失败') ? 'status-error' : 
                        trimmedValue.includes('⚠️') || trimmedValue.includes('警告') ? 'status-warning' : 'status-info'
      return `<div class="analysis-field"><span class="analysis-label">${label}：</span><span class="analysis-value ${valueClass}">${trimmedValue}</span></div>`
    })
    
    // 处理分析报告中的关键信息行（如 "1. 工具缺失 - 数据查询工具未找到"）
    // 注意：这个处理需要在列表处理之前，避免被列表处理覆盖
    // 使用更精确的正则，确保匹配 "数字. 标题 - 描述" 格式
    formatted = formatted.replace(/^(\d+)\.\s+([^-\n]+?)\s*-\s*([^\n]+)$/gm, (match, num, title, desc) => {
      // 确保标题和描述都不为空
      const trimmedTitle = title.trim()
      const trimmedDesc = desc.trim()
      if (trimmedTitle && trimmedDesc) {
        return `<div class="key-finding-item"><span class="key-finding-number">${num}.</span><span class="key-finding-title">${trimmedTitle}</span><span class="key-finding-desc"> - ${trimmedDesc}</span></div>`
      }
      return match
    })
    
    // 处理状态图标开头的区块标题（如 "✅ 已具备的能力:" 或 "❌ 缺失的能力:"）
    // 匹配格式：图标 + 空格 + 文本 + 冒号（中文或英文）
    formatted = formatted.replace(/^(✅|❌|⚠️|📊|🔍|🛠️|📋|🚀|📈|💡|🎯)\s+([^：:\n]+)[：:]\s*$/gm, '<div class="status-section-header"><span class="status-icon-inline">$1</span><span class="status-section-title">$2</span></div>')
    
    // 处理状态图标后的列表内容（如 "✅ 已具备的能力:\n- item1\n- item2"）
    // 将状态区块标题和后续内容组合在一起
    formatted = formatted.replace(/(<div class="status-section-header">[\s\S]*?<\/div>)([\s\S]*?)(?=<div class="status-section-header">|<h[1-3]|##|###|$)/g, (match, header, content) => {
      // 清理内容前后的空白
      const trimmedContent = content.trim()
      if (trimmedContent) {
        // 检查内容中是否有列表项或其他内容
        if (trimmedContent.includes('<li') || trimmedContent.match(/^[\-\*]\s+/m) || trimmedContent.length > 0) {
          // 包装在状态区块内容中
          return `${header}<div class="status-section-content">${trimmedContent}</div>`
        }
      }
      return header
    })
    
    // 8. 处理表格（| col1 | col2 |）- 改进表格解析
    // 使用正则表达式匹配表格块
    const tableBlockRegex = /(\|.+\|\n(?:\|.+\|\n?)+)/g
    formatted = formatted.replace(tableBlockRegex, (tableBlock) => {
      const lines = tableBlock.trim().split('\n').filter(line => line.trim())
      if (lines.length < 2) return tableBlock // 至少需要表头和数据行
      
      let headerRow: string[] | null = null
      const dataRows: string[] = []
      let foundSeparator = false
      
      for (const line of lines) {
        const cells = line.split('|').map(c => c.trim()).filter(c => c)
        if (cells.length === 0) continue
        
        // 检查是否是分隔行
        const isSeparator = cells.every(cell => /^:?-+:?$/.test(cell))
        if (isSeparator) {
          foundSeparator = true
          continue
        }
        
        if (!headerRow) {
          // 第一行作为表头
          headerRow = cells
        } else {
          // 数据行
          dataRows.push(line)
        }
      }
      
      // 如果有表头和数据行，构建表格
      if (headerRow && dataRows.length > 0) {
        const headerCells = headerRow.map(cell => `<th>${escapeHtml(cell)}</th>`).join('')
        const bodyRows = dataRows.map(row => {
          const cells = row.split('|').map(c => c.trim()).filter(c => c)
          return `<tr>${cells.map(cell => `<td>${escapeHtml(cell)}</td>`).join('')}</tr>`
        }).join('')
        return `<table class="message-table"><thead><tr>${headerCells}</tr></thead><tbody>${bodyRows}</tbody></table>`
      }
      
      return tableBlock // 如果无法解析，返回原文本
    })
    
    // 9. 处理换行（保留换行，但避免在已处理的块元素后添加）
    // 不要在已处理的块元素（标题、列表、表格等）后添加换行
    formatted = formatted.replace(/\n/g, '<br />')
    
    // 清理多余的换行（在块元素之间）
    formatted = formatted.replace(/(<\/h[1-3]>)\s*<br\s*\/?>\s*(<h[1-3])/g, '$1$2')
    formatted = formatted.replace(/(<\/table>)\s*<br\s*\/?>\s*(<table)/g, '$1$2')
    formatted = formatted.replace(/(<\/ul>|<\/ol>)\s*<br\s*\/?>\s*(<ul|<ol)/g, '$1$2')
    formatted = formatted.replace(/(<\/div>)\s*<br\s*\/?>\s*(<div)/g, '$1$2')
    
    return formatted
  }, [content])
  
  return (
    <div 
      className={`message-content ${isOwnMessage ? 'message-content-own' : 'message-content-ai'}`}
      dangerouslySetInnerHTML={{ __html: formattedContent }}
    />
  )
}

/**
 * HTML转义函数
 */
function escapeHtml(text: string): string {
  if (typeof window === 'undefined') {
    // 服务端渲染时使用简单转义
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
  }
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

