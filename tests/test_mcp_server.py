import httpx
import json
import asyncio

# 配置测试目标
TARGET_URL = "http://localhost:8001/mcp"


async def test_get_config():
    """测试 GET 请求获取配置"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 GET 请求 (获取服务器配置) ===")
        response = await client.get(TARGET_URL)
        if response.status_code == 200:
            print("✅ GET 成功!")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ GET 失败: {response.status_code}")
        print()


async def test_search_docs():
    """测试文档搜索"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 SearchJavaTron (文档搜索) ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-search-001",
            "method": "tools/call",
            "params": {
                "name": "SearchJavaTron",
                "arguments": {
                    "query": "private network"
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            print("✅ SearchJavaTron 成功!")
            content = result.get("result", {}).get("content", [{}])[0].get("text", "")
            print("返回结果:")
            print("-" * 30)
            print(content[:500] + "..." if len(content) > 500 else content)
            print("-" * 30)
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_get_now_block():
    """测试获取最新区块"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 GetNowBlock (获取最新区块) ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-block-001",
            "method": "tools/call",
            "params": {
                "name": "GetNowBlock",
                "arguments": {}
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            print("✅ GetNowBlock 成功!")
            content = result.get("result", {}).get("content", [{}])[0].get("text", "")
            print(content)
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_get_block_by_number():
    """测试按区块号查询"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 GetBlock (按区块号查询) ===")
        # 查询第 100 个区块（创世区块之后的一个比较早的区块）
        payload = {
            "jsonrpc": "2.0",
            "id": "test-block-002",
            "method": "tools/call",
            "params": {
                "name": "GetBlock",
                "arguments": {
                    "block_number": 100
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            print("✅ GetBlock (by number) 成功!")
            content = result.get("result", {}).get("content", [{}])[0].get("text", "")
            print(content)
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_get_account():
    """测试查询账户"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 GetAccount (查询账户) ===")
        # TRON 基金会的一个地址
        payload = {
            "jsonrpc": "2.0",
            "id": "test-account-001",
            "method": "tools/call",
            "params": {
                "name": "GetAccount",
                "arguments": {
                    "address": "TA1EfN5K1vtEbPjApHnui7evdLP3fT7z3B"
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            print("✅ GetAccount 成功!")
            content = result.get("result", {}).get("content", [{}])[0].get("text", "")
            print(content)
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_get_account_resource():
    """测试查询账户资源"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 GetAccountResource (查询账户资源) ===")
        payload = {
            "jsonrpc": "2.0",
            "id": "test-resource-001",
            "method": "tools/call",
            "params": {
                "name": "GetAccountResource",
                "arguments": {
                    "address": "TA1EfN5K1vtEbPjApHnui7evdLP3fT7z3B"
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            print("✅ GetAccountResource 成功!")
            content = result.get("result", {}).get("content", [{}])[0].get("text", "")
            print(content)
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_get_transaction():
    """测试查询交易"""
    async with httpx.AsyncClient() as client:
        print("=== 测试 GetTransaction (查询交易) ===")
        # 这是一个示例交易哈希，可能已不存在
        # 实际使用时应该用 GetNowBlock 获取的区块中的交易
        payload = {
            "jsonrpc": "2.0",
            "id": "test-tx-001",
            "method": "tools/call",
            "params": {
                "name": "GetTransaction",
                "arguments": {
                    "tx_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
                }
            }
        }
        
        response = await client.post(TARGET_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            print("✅ GetTransaction 成功!")
            content = result.get("result", {}).get("content", [{}])[0].get("text", "")
            print(content)
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
        print()


async def test_mcp_server():
    """运行所有测试"""
    print("🚀 开始测试 MCP 服务器\n")
    print(f"目标地址: {TARGET_URL}\n")
    print("=" * 50)
    
    await test_get_config()
    await test_search_docs()
    await test_get_now_block()
    await test_get_block_by_number()
    await test_get_account()
    await test_get_account_resource()
    await test_get_transaction()
    
    print("✅ 所有测试完成!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
