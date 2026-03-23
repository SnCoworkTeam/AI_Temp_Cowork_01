import requests
import sys

try:
    r = requests.get("http://localhost:8004/api/documents?page=1&page_size=1000", timeout=5)
    if r.status_code == 200:
        data = r.json()
        total = data.get("total", 0)
        docs = data.get("documents", [])
        
        sap_processed = 0
        sap_processing = 0
        sap_failed = 0
        
        for d in docs:
            m = d.get("metadata", {})
            cat = d.get("category", "")
            tags = d.get("tags", [])
            t = str(m.get("type", ""))
            
            if "sap" in cat.lower() or any("sap" in str(tag).lower() for tag in tags) or "data_asset" in t.lower() or "business_entity" in t.lower():
                s = d.get("status", "")
                if s == "processed":
                    sap_processed += 1
                elif s == "processing":
                    sap_processing += 1
                elif s == "failed":
                    sap_failed += 1
        
        print(f"Total documents: {total}")
        print(f"SAP processed: {sap_processed}")
        print(f"SAP processing: {sap_processing}")
        print(f"SAP failed: {sap_failed}")
        print(f"Progress: {sap_processed}/109022 ({sap_processed/109022*100:.2f}%)")
    else:
        print(f"Error: HTTP {r.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

