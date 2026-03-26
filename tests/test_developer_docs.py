import httpx
import json
import asyncio
import os
import pytest

# 配置测试目标
TARGET_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp")


@pytest.mark.skipif(os.getenv("INTEGRATION_TEST") != "1", reason="需要启动 MCP 服务器 (INTEGRATION_TEST=1)")
@pytest.mark.asyncio
async def test_search_develop_java_tron_basic():
    """测试 SearchDevelopJavaTron 基本搜索"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 SearchDevelopJavaTron (基本搜索) ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-devdocs-001",
            "method": "tools/call",
            "params": {
                "name": "SearchDevelopJavaTron",
                "arguments": {
                    "query": "getting started",
                    "limit": 3
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        assert response.status_code == 200, f"请求失败: {response.status_code} - {response.text}"
        
        result = response.json()
        assert "result" in result, "响应中缺少 result 字段"
        assert "content" in result["result"], "响应中缺少 content 字段"
        
        content = result["result"]["content"][0].get("text", "")
        assert content, "搜索结果为空"
        assert not content.startswith("Error"), f"搜索返回错误: {content}"
        
        print("✅ SearchDevelopJavaTron 成功!")
        print("返回结果:")
        print("-" * 50)
        print(content[:800] + "..." if len(content) > 800 else content)
        print("-" * 50)
        print()


@pytest.mark.skipif(os.getenv("INTEGRATION_TEST") != "1", reason="需要启动 MCP 服务器 (INTEGRATION_TEST=1)")
@pytest.mark.asyncio
async def test_search_develop_java_tron_smart_contract():
    """测试 SearchDevelopJavaTron 智能合约搜索"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 SearchDevelopJavaTron (智能合约搜索) ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-devdocs-002",
            "method": "tools/call",
            "params": {
                "name": "SearchDevelopJavaTron",
                "arguments": {
                    "query": "smart contract deploy",
                    "limit": 5
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        assert response.status_code == 200, f"请求失败: {response.status_code} - {response.text}"
        
        result = response.json()
        assert "result" in result, "响应中缺少 result 字段"
        assert "content" in result["result"], "响应中缺少 content 字段"
        
        content = result["result"]["content"][0].get("text", "")
        assert content, "搜索结果为空"
        assert not content.startswith("Error"), f"搜索返回错误: {content}"
        
        print("✅ 智能合约搜索成功!")
        print(content[:800] + "..." if len(content) > 800 else content)
        print()


@pytest.mark.skipif(os.getenv("INTEGRATION_TEST") != "1", reason="需要启动 MCP 服务器 (INTEGRATION_TEST=1)")
@pytest.mark.asyncio
async def test_search_java_tron_basic():
    """测试 SearchJavaTron 基本搜索"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 SearchJavaTron (基本搜索) ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-javatron-001",
            "method": "tools/call",
            "params": {
                "name": "SearchJavaTron",
                "arguments": {
                    "query": "private network",
                    "limit": 3
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        assert response.status_code == 200, f"请求失败: {response.status_code} - {response.text}"
        
        result = response.json()
        assert "result" in result, "响应中缺少 result 字段"
        assert "content" in result["result"], "响应中缺少 content 字段"
        
        content = result["result"]["content"][0].get("text", "")
        assert content, "搜索结果为空"
        assert not content.startswith("Error"), f"搜索返回错误: {content}"
        
        print("✅ SearchJavaTron 成功!")
        print("返回结果:")
        print("-" * 50)
        print(content[:800] + "..." if len(content) > 800 else content)
        print("-" * 50)
        print()


@pytest.mark.skipif(os.getenv("INTEGRATION_TEST") != "1", reason="需要启动 MCP 服务器 (INTEGRATION_TEST=1)")
@pytest.mark.asyncio
async def test_tools_list_includes_doc_tools():
    """验证 tools/list 包含文档搜索工具"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 tools/list 包含文档搜索工具 ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-list-001",
            "method": "tools/list",
            "params": {}
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        assert response.status_code == 200, f"请求失败: {response.status_code} - {response.text}"
        
        result = response.json()
        tools = result.get("result", {}).get("tools", [])
        tool_names = [t.get("name") for t in tools]
        
        assert "SearchDevelopJavaTron" in tool_names, f"SearchDevelopJavaTron 不在工具列表中"
        assert "SearchJavaTron" in tool_names, f"SearchJavaTron 不在工具列表中"
        
        print("✅ 文档搜索工具已在工具列表中!")
        print(f"可用工具: {tool_names}")
        print()


async def run_developer_docs_tests():
    """运行所有开发者文档测试的入口函数"""
    print("🚀 开始测试 TRON 开发者文档搜索功能\n")
    print(f"目标地址: {TARGET_URL}")
    print("=" * 60)
    
    # 先验证工具是否已注册
    await test_tools_list_includes_doc_tools()
    
    # 测试 SearchDevelopJavaTron
    await test_search_develop_java_tron_basic()
    await test_search_develop_java_tron_smart_contract()
    
    # 测试 SearchJavaTron
    await test_search_java_tron_basic()
    
    print("=" * 60)
    print("✅ 所有开发者文档测试完成!")


if __name__ == "__main__":
    asyncio.run(run_developer_docs_tests())
