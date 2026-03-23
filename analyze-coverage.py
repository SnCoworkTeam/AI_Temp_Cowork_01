#!/usr/bin/env python3
"""分析测试覆盖率"""
import json
import sys

with open('/tmp/coverage.json', 'r') as f:
    data = json.load(f)

files = data.get('files', {})
low_coverage = []

for file_path, info in files.items():
    summary = info.get('summary', {})
    percent = summary.get('percent_covered', 0)
    if percent < 80:
        file_name = file_path.replace('/app/src/', '')
        low_coverage.append((file_name, percent))

low_coverage.sort(key=lambda x: x[1])

print("Low coverage files (< 80%):")
for file_name, percent in low_coverage[:30]:
    print(f"{percent:.1f}% - {file_name}")

total = data.get('totals', {})
print(f"\nTotal coverage: {total.get('percent_covered', 0):.1f}%")

