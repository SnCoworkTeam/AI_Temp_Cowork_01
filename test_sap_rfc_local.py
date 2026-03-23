"""
本地测试通过 RFC 连接 SAP ERP (S4 HANA) 的脚本。
使用的连接参数与 mcp-gateway/src/tools/sap_erp_table_tool.py 中的默认值保持一致，
也可以通过环境变量覆盖：
  SAP_USER / SAP_PASSWORD / SAP_HOST / SAP_SYSNR / SAP_CLIENT

注意：
- 需要已正确安装 SAP NWRFC SDK，并设置 SAPNWRFC_HOME 与 PATH 指向 SDK 的 lib 目录
- 需要已安装 pyrfc：pip install pyrfc
"""

import os
from pyrfc import Connection


def get_sap_config():
  """从环境变量或默认值获取 SAP 连接配置"""
  return {
    "user": os.getenv("SAP_USER", "admin"),
    "passwd": os.getenv("SAP_PASSWORD", "ad@kf29!()G"),
    "ashost": os.getenv("SAP_HOST", "10.24.49.128"),
    "sysnr": os.getenv("SAP_SYSNR", "00"),
    "client": os.getenv("SAP_CLIENT", "100"),
  }


def main():
  config = get_sap_config()
  print("使用 SAP 连接配置：")
  for k, v in config.items():
    # 密码不直接打印明文
    if k.lower() == "passwd":
      print(f"  {k} = {'*' * 8}")
    else:
      print(f"  {k} = {v}")

  print("\n尝试建立 RFC 连接...")
  conn = Connection(**config)
  print("✅ RFC 连接成功，开始 ping...")

  conn.ping()
  print("✅ ping 成功，准备测试 RFC_READ_TABLE 读取 BKPF 表前 5 行...\n")

  result = conn.call(
    "RFC_READ_TABLE",
    QUERY_TABLE="BKPF",
    DELIMITER="|",
    ROWCOUNT=5,
  )

  fields = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
  print(f"✅ RFC_READ_TABLE 调用成功，字段数: {len(fields)}")
  print("字段列表:", ", ".join(fields))

  data_rows = result.get("DATA", [])
  print(f"返回行数: {len(data_rows)}")
  for row in data_rows:
    print(row.get("WA", ""))

  conn.close()
  print("\n连接已关闭。测试完成。")


if __name__ == "__main__":
  main()




















