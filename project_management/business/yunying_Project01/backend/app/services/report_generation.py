from app.schemas.report import Report, ReportCreate
import uuid
import pandas as pd
from app.core.config import settings
from .llm_service import llm_service
import traceback
from datetime import datetime
import os
import concurrent.futures

def log_error(msg):
    with open("backend_error.log", "a", encoding='utf-8') as f:
        f.write(f"{datetime.now()}: {msg}\n")

class ReportGenerationService:
    def generate_report(self, report_in: ReportCreate, data_service, report_id=None, progress_callback=None) -> Report:
        log_error("Generating report with LLM analysis...")
        try:
            if not report_id:
                report_id = str(uuid.uuid4())
                
            input_file = os.path.join(settings.UPLOAD_DIR, "data_file.xlsx")
            
            if not os.path.exists(input_file):
                log_error(f"File not found: {input_file}")
                raise FileNotFoundError("Data file not found. Please upload first.")

            # Read Excel file
            log_error(f"Reading Excel file: {input_file}")
            df = pd.read_excel(input_file, engine='openpyxl')
            
            # Clean data: Drop rows where all columns are NaN
            df = df.dropna(how='all')
            # Also drop rows where '产品名称' might be empty if that's a key field
            if '产品名称' in df.columns:
                df = df.dropna(subset=['产品名称'])
                
            # Calculate Week-over-Week ratios
            def calculate_wow(current, previous):
                try:
                    if pd.isna(current) or pd.isna(previous) or previous == 0:
                        return None
                    return (current - previous) / previous
                except:
                    return None

            # Helper to format percentage, returning empty string for None
            def format_percentage(val):
                if val is None or pd.isna(val):
                    return ""
                return f"{val:.2%}"

            # 咨询价周环比
            if '本周资讯价格' in df.columns and '上周资讯价格' in df.columns:
                df['咨询价周环比'] = df.apply(lambda row: calculate_wow(row['本周资讯价格'], row['上周资讯价格']), axis=1)
                df['咨询价周环比'] = df['咨询价周环比'].apply(format_percentage)

            # 销售价周环比
            if '本周销售价格' in df.columns and '上周销售价格' in df.columns:
                df['销售价周环比'] = df.apply(lambda row: calculate_wow(row['本周销售价格'], row['上周销售价格']), axis=1)
                df['销售价周环比'] = df['销售价周环比'].apply(format_percentage)

            # 采购价周环比
            if '本周采购价格' in df.columns and '上周采购价格' in df.columns:
                df['采购价周环比'] = df.apply(lambda row: calculate_wow(row['本周采购价格'], row['上周采购价格']), axis=1)
                df['采购价周环比'] = df['采购价周环比'].apply(format_percentage)

            log_error(f"Excel read successfully. Valid Rows: {len(df)}")
            
            # Initial progress update
            if progress_callback:
                progress_callback(0, len(df))
            
            # Use sequential processing to avoid "main thread is not in main loop" errors
            # caused by some library interaction in the threaded environment
            results = {}
            log_error("Starting sequential LLM analysis for each row...")
            
            completed_count = 0
            total_count = len(df)
            
            for index, row in df.iterrows():
                try:
                    # Convert row to string representation for the prompt
                    row_str = row.to_string()
                    
                    product_name = row.get('产品名称', f'Product {index}')
                    
                    # Add custom prompt if provided
                    user_instruction = ""
                    if report_in.custom_prompt:
                        user_instruction = f"用户额外指示：{report_in.custom_prompt}"
                    
                    prompt = f"""
                    请根据以下单一产品的价格数据，生成一段简短的市场概述（Market Overview）。
                    
                    产品数据：
                    {row_str}
                    
                    {user_instruction}
                    
                    分析要求：
                    1. 简要分析本周与上周的价格变化（资讯、销售、采购）。
                    2. 给出该产品的市场走势判断（涨/跌/平）。
                    3. 字数控制在50-100字以内。
                    4. 请直接输出分析内容，不要包含"市场概述："等前缀。
                    """
                    
                    analysis = llm_service.generate_analysis(prompt)
                    results[index] = analysis
                except Exception as e:
                    log_error(f"Error analyzing row {index}: {str(e)}")
                    results[index] = "分析失败"
                
                completed_count += 1
                
                if progress_callback:
                    progress_callback(completed_count, total_count)
                    
                if completed_count % 5 == 0:
                    log_error(f"Progress: {completed_count}/{total_count}")

            # Assign results back to DataFrame in correct order
            df['市场概述'] = [results.get(i, "") for i in range(len(df))]
            
            log_error("All rows analyzed.")

            # Reorder columns:
            # 咨询价周环比 -> after 上周资讯价格
            # 销售价周环比 -> after 上周销售价格
            # 采购价周环比 -> after 上周采购价格
            
            columns_to_move = ['咨询价周环比', '销售价周环比', '采购价周环比']
            # Get current columns as a list
            current_cols = list(df.columns)
            
            # Identify base columns (excluding the ones we want to move if they exist)
            base_cols = [c for c in current_cols if c not in columns_to_move]
            
            final_order = []
            for col in base_cols:
                final_order.append(col)
                if col == '上周资讯价格' and '咨询价周环比' in df.columns:
                    final_order.append('咨询价周环比')
                elif col == '上周销售价格' and '销售价周环比' in df.columns:
                    final_order.append('销售价周环比')
                elif col == '上周采购价格' and '采购价周环比' in df.columns:
                    final_order.append('采购价周环比')
            
            # Apply new column order
            df = df[final_order]

            # Save generated report
            # Format: report_YYYYMMDD_HHMMSS.xlsx
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"report_{timestamp}.xlsx"
            output_path = os.path.join(settings.REPORT_DIR, output_filename)
            log_error(f"Saving report to: {output_path}")
            df.to_excel(output_path, index=False)
            
            # Convert to HTML for preview (limit to 20 rows for preview)
            html_preview = df.head(20).to_html(classes="min-w-full divide-y divide-gray-200", border=0)
            
            return Report(
                id=report_id,
                title=report_in.title,
                period_start=report_in.period_start,
                period_end=report_in.period_end,
                created_at=datetime.now(),
                status="completed",
                progress=100,
                total_rows=total_count,
                processed_rows=total_count,
                html_content=html_preview,
                file_path=output_filename, 
                price_analysis=[], 
                supply_demand_analysis=[],
                profit_analysis=[]
            )
        except Exception as e:
            log_error(f"Error in generate_report: {str(e)}")
            log_error(traceback.format_exc())
            raise e

report_generation_service = ReportGenerationService()
