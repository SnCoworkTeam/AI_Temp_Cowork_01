#!/usr/bin/env python3
"""测试 LangGraph 导入"""
import sys

print("Testing LangGraph import...")
try:
    from langgraph.graph import StateGraph, END
    print("✓ LangGraph import successful")
    print(f"  StateGraph: {StateGraph}")
    print(f"  END: {END}")
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    print(f"✗ LangGraph import failed: {e}")
    LANGGRAPH_AVAILABLE = False
    sys.exit(1)

print("\nTesting LangChain OpenAI...")
try:
    from langchain_openai import ChatOpenAI
    print("✓ LangChain OpenAI import successful")
except ImportError as e:
    print(f"✗ LangChain OpenAI import failed: {e}")
    sys.exit(1)

print("\nAll imports successful!")











































