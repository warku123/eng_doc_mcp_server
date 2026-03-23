import httpx
import json
import asyncio

# 配置测试目标
TARGET_URL = "http://localhost:8001/mcp"


async def test_search_developer_docs_basic():
    """测试基本的开发者文档搜索"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 SearchTronDeveloperDocs (基本搜索) ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-devdocs-001",
            "method": "tools/call",
            "params": {
                "name": "SearchTronDeveloperDocs",
                "arguments": {
                    "query": "getting started",
                    "limit": 3
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            print("✅ SearchTronDeveloperDocs 成功!")
            content = result.get("result", {}).get("content", [{}])[0].get("text", "")
            print("返回结果:")
            print("-" * 50)
            print(content[:800] + "..." if len(content) > 800 else content)
            print("-" * 50)
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_search_developer_docs_smart_contract():
    """测试智能合约相关搜索"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 SearchTronDeveloperDocs (智能合约搜索) ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-devdocs-002",
            "method": "tools/call",
            "params": {
                "name": "SearchTronDeveloperDocs",
                "arguments": {
                    "query": "smart contract deploy",
                    "limit": 5
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            print("✅ 智能合约搜索成功!")
            content = result.get("result", {}).get("content", [{}])[0].get("text", "")
            print("返回结果:")
            print("-" * 50)
            print(content[:800] + "..." if len(content) > 800 else content)
            print("-" * 50)
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_search_developer_docs_wallet():
    """测试钱包集成相关搜索"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 SearchTronDeveloperDocs (钱包集成搜索) ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-devdocs-003",
            "method": "tools/call",
            "params": {
                "name": "SearchTronDeveloperDocs",
                "arguments": {
                    "query": "TronLink wallet integration"
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            print("✅ 钱包集成搜索成功!")
            content = result.get("result", {}).get("content", [{}])[0].get("text", "")
            print("返回结果:")
            print("-" * 50)
            print(content[:800] + "..." if len(content) > 800 else content)
            print("-" * 50)
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_search_developer_docs_resource():
    """测试资源模型相关搜索"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 SearchTronDeveloperDocs (资源模型搜索) ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-devdocs-004",
            "method": "tools/call",
            "params": {
                "name": "SearchTronDeveloperDocs",
                "arguments": {
                    "query": "bandwidth energy resource model"
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            print("✅ 资源模型搜索成功!")
            content = result.get("result", {}).get("content", [{}])[0].get("text", "")
            print("返回结果:")
            print("-" * 50)
            print(content[:800] + "..." if len(content) > 800 else content)
            print("-" * 50)
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_search_developer_docs_empty_query():
    """测试空查询的处理"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 SearchTronDeveloperDocs (空查询) ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-devdocs-005",
            "method": "tools/call",
            "params": {
                "name": "SearchTronDeveloperDocs",
                "arguments": {
                    "query": ""
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            print("✅ 空查询处理完成!")
            content = result.get("result", {}).get("content", [{}])[0].get("text", "")
            print("返回结果:")
            print("-" * 50)
            print(content)
            print("-" * 50)
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_tools_list_includes_new_tool():
    """验证 tools/list 包含新添加的工具"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 tools/list 包含 SearchTronDeveloperDocs ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-list-001",
            "method": "tools/list",
            "params": {}
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            tools = result.get("result", {}).get("tools", [])
            tool_names = [t.get("name") for t in tools]
            
            if "SearchTronDeveloperDocs" in tool_names:
                print("✅ SearchTronDeveloperDocs 已在工具列表中!")
                # 显示工具定义
                for tool in tools:
                    if tool.get("name") == "SearchTronDeveloperDocs":
                        print("工具定义:")
                        print(json.dumps(tool, indent=2, ensure_ascii=False))
            else:
                print("❌ SearchTronDeveloperDocs 不在工具列表中")
                print(f"可用工具: {tool_names}")
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_search_direct_readme_api():
    """直接测试 ReadMe 原生搜索 API（不经过 MCP 服务器）"""
    print("=== 直接测试 ReadMe 原生搜索 API ===")
    
    search_url = "https://developers.tron.network/tron/api-next/v2/search"
    
    # 不指定 version，让服务器自动返回最新版本
    params = {
        "query": "API"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(search_url, params=params, headers=headers, timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                hits = data.get("data", [])
                print(f"✅ ReadMe API 调用成功! 共 {total} 个结果，显示前 {min(3, len(hits))} 个:")
                for hit in hits[:3]:
                    title = hit.get("title", "Untitled")
                    url = hit.get("url", {}).get("full", "")
                    print(f"  - {title}: {url}")
            else:
                print(f"❌ ReadMe API 失败: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ ReadMe API 调用异常: {e}")
    print()


async def test_developer_docs():
    """运行所有开发者文档测试"""
    print("🚀 开始测试 TRON 开发者文档搜索功能\n")
    print(f"目标地址: {TARGET_URL}")
    print("=" * 60)
    
    # 先验证工具是否已注册
    await test_tools_list_includes_new_tool()
    
    # 测试各种搜索场景
    await test_search_developer_docs_basic()
    await test_search_developer_docs_smart_contract()
    await test_search_developer_docs_wallet()
    await test_search_developer_docs_resource()
    await test_search_developer_docs_empty_query()
    
    # 直接测试 ReadMe 原生搜索 API
    await test_search_direct_readme_api()
    
    print("=" * 60)
    print("✅ 所有开发者文档测试完成!")


if __name__ == "__main__":
    asyncio.run(test_developer_docs())
