# 检查元数据质量（是否包含增强字段）
Write-Host "`n检查元数据质量..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

$totalChecked = 0
$hasAbapDict = 0
$hasBusinessTerms = 0
$hasSemanticRels = 0
$hasClassification = 0

# 检查不同类型的资产
$classifications = @("sap_master_data_customer", "sap_master_data_vendor", "sap_transaction_sales_order", "sap_odata_entity")

foreach ($classification in $classifications) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8005/api/data-assets?classification=$classification&limit=5" -TimeoutSec 10 -ErrorAction Stop
        $assets = $response.Content | ConvertFrom-Json
        
        foreach ($asset in $assets) {
            $totalChecked++
            
            # 检查ABAP字典信息
            if ($asset.schema_info -and $asset.schema_info.abap_dictionary) {
                $hasAbapDict++
            }
            
            # 检查业务术语
            if ($asset.metadata -and $asset.metadata.business_terms) {
                $hasBusinessTerms++
            }
            
            # 检查语义关系
            if ($asset.metadata -and $asset.metadata.semantic_relationships) {
                $hasSemanticRels++
            }
            
            # 检查分类
            if ($asset.classification) {
                $hasClassification++
            }
        }
    } catch {
        Write-Host "无法检查分类 $classification" -ForegroundColor Yellow
    }
}

Write-Host "`n检查结果 (检查了 $totalChecked 个资产):" -ForegroundColor Cyan
Write-Host "  包含ABAP字典信息: $hasAbapDict/$totalChecked ($([math]::Round($hasAbapDict/$totalChecked*100, 1))%)" -ForegroundColor $(if ($hasAbapDict -gt 0) { "Green" } else { "Yellow" })
Write-Host "  包含业务术语: $hasBusinessTerms/$totalChecked ($([math]::Round($hasBusinessTerms/$totalChecked*100, 1))%)" -ForegroundColor $(if ($hasBusinessTerms -gt 0) { "Green" } else { "Yellow" })
Write-Host "  包含语义关系: $hasSemanticRels/$totalChecked ($([math]::Round($hasSemanticRels/$totalChecked*100, 1))%)" -ForegroundColor $(if ($hasSemanticRels -gt 0) { "Green" } else { "Yellow" })
Write-Host "  包含分类: $hasClassification/$totalChecked ($([math]::Round($hasClassification/$totalChecked*100, 1))%)" -ForegroundColor $(if ($hasClassification -gt 0) { "Green" } else { "Yellow" })

Write-Host "`n建议:" -ForegroundColor Cyan
if ($hasAbapDict -eq 0 -or $hasBusinessTerms -eq 0 -or $hasSemanticRels -eq 0) {
    Write-Host "  [WARN] 现有元数据缺少增强字段，建议重新构建以包含:" -ForegroundColor Yellow
    if ($hasAbapDict -eq 0) { Write-Host "    - ABAP字典信息" -ForegroundColor Yellow }
    if ($hasBusinessTerms -eq 0) { Write-Host "    - 业务术语映射" -ForegroundColor Yellow }
    if ($hasSemanticRels -eq 0) { Write-Host "    - 语义关系" -ForegroundColor Yellow }
    Write-Host "`n  运行: python build_complete_enhanced_metadata.py" -ForegroundColor Cyan
} else {
    Write-Host "  [OK] 现有元数据包含所有增强字段，符合新标准" -ForegroundColor Green
    Write-Host "  可以直接测试任务编排功能" -ForegroundColor Green
}


