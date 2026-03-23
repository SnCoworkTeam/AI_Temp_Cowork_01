from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime

def create_functional_document():
    document = Document()

    # Title
    heading = document.add_heading('行业产品报告生成系统 - 功能说明文档', 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

    document.add_paragraph(f'文档生成日期: {datetime.now().strftime("%Y-%m-%d")}')

    # 1. 系统概述
    document.add_heading('1. 系统概述', level=1)
    p = document.add_paragraph('本系统旨在自动化生成行业产品市场分析报告。通过上传包含产品价格数据的 Excel 文件，系统自动调用大语言模型（LLM）对每个产品的市场行情进行智能分析，并生成包含详细数据和分析结论的综合报告。')

    # 2. 核心功能流程
    document.add_heading('2. 核心功能流程', level=1)
    
    # 2.1 数据上传
    document.add_heading('2.1 数据上传', level=2)
    document.add_paragraph('用户通过 Web 界面上传本地 Excel (.xlsx) 或 CSV 文件。')
    document.add_paragraph('支持的文件字段包括：', style='List Bullet')
    document.add_paragraph('产品名称', style='List Bullet')
    document.add_paragraph('本周资讯价格、上周资讯价格', style='List Bullet')
    document.add_paragraph('本周销售价格、上周销售价格', style='List Bullet')
    document.add_paragraph('本周采购价格、上周采购价格', style='List Bullet')
    document.add_paragraph('系统会自动校验文件格式，并在上传成功后给出提示。')

    # 2.2 智能报告生成
    document.add_heading('2.2 智能报告生成', level=2)
    document.add_paragraph('点击“生成报告”后，系统执行以下自动化处理：')
    document.add_paragraph('数据清洗：自动剔除空行和无效数据。', style='List Bullet')
    document.add_paragraph('环比计算：自动计算咨询价、销售价、采购价的周环比变化率。', style='List Bullet')
    document.add_paragraph('AI 智能分析：针对每一行产品数据，调用配置的大语言模型（如 Qwen-72B），生成个性化的“市场概述”。分析内容涵盖价格波动趋势（涨/跌/平）及简要市场判断。', style='List Bullet')
    document.add_paragraph('进度实时展示：界面显示生成进度条及已处理行数，支持断点查看。', style='List Bullet')

    # 2.3 报告预览与下载
    document.add_heading('2.3 报告预览与下载', level=2)
    document.add_paragraph('生成完成后，自动跳转至预览页面。')
    document.add_paragraph('在线预览：以 Excel 表格样式在网页端直接展示报告内容。', style='List Bullet')
    document.add_paragraph('文件下载：支持将最终报告下载为 Excel 文件。', style='List Bullet')
    document.add_paragraph('文件名格式：自动命名为 report_YYYYMMDD_HHMMSS.xlsx，方便归档。', style='List Bullet')

    # 3. 输出文件规范
    document.add_heading('3. 输出文件规范', level=1)
    document.add_paragraph('生成的 Excel 报告包含经过重新编排的列，顺序如下：')
    cols = ['产品名称', '本周资讯价格', '上周资讯价格', '咨询价周环比', '本周销售价格', '上周销售价格', '销售价周环比', '本周采购价格', '上周采购价格', '采购价周环比', '市场概述 (AI生成)']
    for col in cols:
        document.add_paragraph(col, style='List Number')
    
    document.add_paragraph('注：若计算数据缺失，环比字段将显示为空白，保持版面整洁。')

    # 4. 技术特性
    document.add_heading('4. 技术特性', level=1)
    document.add_paragraph('内网适配：支持配置私有化 LLM API 地址，并针对内网环境优化了 SSL 证书验证。', style='List Bullet')
    document.add_paragraph('高并发/稳定性：采用顺序处理机制，确保在复杂网络环境下数据处理的稳定性。', style='List Bullet')
    document.add_paragraph('格式兼容：完全兼容 .xlsx 格式，解决旧版 xlrd 库的依赖问题。', style='List Bullet')

    # Save
    file_path = 'System_Functional_Document.docx'
    document.save(file_path)
    print(f"Document saved to {file_path}")

if __name__ == "__main__":
    create_functional_document()
