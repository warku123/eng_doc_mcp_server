from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import os
import httpx

app = FastAPI()

# --- 配置与工具定义 ---
SERVER_INFO = {
    "name": "java-tron Developer Documentation & Chain Query",
    "version": "2.0.0",
}

# TRON RPC 配置
# 可以使用公共节点或私有节点
TRON_RPC_URL = os.getenv("TRON_RPC_URL", "https://api.trongrid.io")

# 将工具定义提取出来，以便在 tools/list 中复用
TOOLS_DEFINITION = [
    {
        "name": "SearchJavaTron",
        "description": "Search across the java-tron documentation to find the basic principles of java-tron, and how to deploy a java-tron node and interact with it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "A query to search the content with."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "SearchDevelopJavaTron",
        "description": "Search across the java-tron developer documentation to find how to deploy and interact with a java-tron node, and how to develop DApps based on java-tron.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "A query to search the content with."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "GetBlock",
        "description": "Query block information from the TRON blockchain by block number (height) or block hash. Returns block details including timestamp, transactions, witness address, etc.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "block_number": {
                    "type": "integer",
                    "description": "The block height/number to query. Use this OR block_hash, not both."
                },
                "block_hash": {
                    "type": "string",
                    "description": "The block hash (block ID) to query. Use this OR block_number, not both."
                },
                "detail": {
                    "type": "boolean",
                    "description": "If true, returns full transaction details. If false, only returns transaction hashes. Default: false",
                    "default": False
                }
            },
            "anyOf": [
                {"required": ["block_number"]},
                {"required": ["block_hash"]}
            ]
        }
    },
    {
        "name": "GetTransaction",
        "description": "Query transaction information from the TRON blockchain by transaction hash (ID). Returns transaction details including sender, receiver, amount, timestamp, confirmation status, etc.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tx_hash": {
                    "type": "string",
                    "description": "The transaction hash (ID) to query. Example: 'a1b2c3d4...' (64 hex characters)"
                }
            },
            "required": ["tx_hash"]
        }
    },
    {
        "name": "GetAccount",
        "description": "Query account information from the TRON blockchain by address. Returns balance, resources (bandwidth/energy), TRC-10 tokens, stake information, votes, and permissions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "The TRON address to query. Example: 'TNP2Xw...' (34 characters starting with 'T')"
                }
            },
            "required": ["address"]
        }
    },
    {
        "name": "GetAccountResource",
        "description": "Query account resource information from the TRON blockchain. Returns bandwidth, energy, and other resource details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "The TRON address to query. Example: 'TNP2Xw...' (34 characters starting with 'T')"
                }
            },
            "required": ["address"]
        }
    },
    {
        "name": "GetNowBlock",
        "description": "Get the latest block information from the TRON blockchain. Returns the most recent block details.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

INDEX_PATH = "./site/search/search_index.json"
BASE_URL = "https://tronprotocol.github.io/documentation-en/"

DEVELOP_INDEX_PATH = "./site/search/develop_search_index.json"
DEVELOP_BASE_URL = "https://developers.tron.network/"

@app.get("/mcp")
async def get_mcp_config():
    """供浏览器查看的静态配置说明"""
    return {
        "server": SERVER_INFO,
        "capabilities": {"tools": TOOLS_DEFINITION}
    }


@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """核心逻辑：处理 Cursor 的 JSON-RPC 指令"""
    try:
        body = await request.json()
        method = body.get("method")
        request_id = body.get("id")

        # 阶段 1: 握手初始化
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": SERVER_INFO,
                    "capabilities": {
                        "tools": {}  # 声明支持工具能力
                    }
                }
            }

        # 阶段 2: 告诉 Cursor 有哪些工具可用
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": TOOLS_DEFINITION
                }
            }

        # 阶段 3: 处理真正的工具调用执行
        if method == "tools/call":
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            result_text = ""
            
            if tool_name == "SearchJavaTron":
                query = arguments.get("query", "")
                result_text = perform_search(query, INDEX_PATH, BASE_URL)
            elif tool_name == "SearchDevelopJavaTron":
                query = arguments.get("query", "")
                result_text = perform_search(query, DEVELOP_INDEX_PATH, DEVELOP_BASE_URL)
            elif tool_name == "GetBlock":
                result_text = await get_block(
                    arguments.get("block_number"),
                    arguments.get("block_hash"),
                    arguments.get("detail", False)
                )
            elif tool_name == "GetTransaction":
                result_text = await get_transaction(arguments.get("tx_hash"))
            elif tool_name == "GetAccount":
                result_text = await get_account(arguments.get("address"))
            elif tool_name == "GetAccountResource":
                result_text = await get_account_resource(arguments.get("address"))
            elif tool_name == "GetNowBlock":
                result_text = await get_now_block()
            else:
                result_text = f"Unknown tool: {tool_name}"
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": result_text}]
                }
            }

        # 阶段 4: 确认初始化完成
        if method == "notifications/initialized":
            return JSONResponse(content={})

        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


def perform_search(query: str, index_path: str, base_url: str)):
    """搜索本地文档"""
    if not os.path.exists(index_path):
        return "Error: Index not found. Run 'mkdocs build'."
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 按空格分词，每个词都要在 title 或 text 里出现（放宽匹配）
    query_words = [w.strip() for w in query.lower().split() if len(w.strip()) > 1]
    if not query_words:
        query_words = [query.lower()]

    hits = []
    for doc in data['docs']:
        title_lower = doc['title'].lower()
        text_lower = doc.get('text', '').lower()
        # 所有词都在该 doc 中出现即算命中
        if all(word in title_lower or word in text_lower for word in query_words):
            excerpt = (doc.get('text') or '')[:200]
            hits.append(f"### {doc['title']}\nURL: {base_url}{doc['location']}\nExcerpt: {excerpt}...")
            if len(hits) >= 5:
                break

    return "\n\n".join(hits) if hits else "No relevant documentation found."


async def tron_rpc_request(endpoint: str, payload: dict = None, method: str = "POST") -> dict:
    """发送 TRON RPC 请求"""
    url = f"{TRON_RPC_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, timeout=30.0)
            else:
                response = await client.post(url, json=payload or {}, headers=headers, timeout=30.0)
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}


async def get_block(block_number: int = None, block_hash: str = None, detail: bool = False):
    """查询区块信息"""
    if block_hash:
        # 使用 block hash 查询
        result = await tron_rpc_request("/wallet/getblock", {"id_or_num": block_hash, "detail": detail})
    elif block_number is not None:
        # 使用 block number 查询
        result = await tron_rpc_request("/wallet/getblockbynum", {"num": block_number})
    else:
        return "Error: Either block_number or block_hash must be provided."
    
    if "error" in result:
        return f"Error querying block: {result['error']}"
    
    if not result or (isinstance(result, dict) and not result.get("block_header")):
        return "Block not found."
    
    # 格式化输出
    header = result.get("block_header", {}).get("raw_data", {})
    block_id = result.get("blockID", "N/A")
    
    formatted = f"""### Block Information

**Block Hash (ID):** `{block_id}`
**Block Number:** {header.get("number", "N/A")}
**Timestamp:** {header.get("timestamp", "N/A")} ({format_timestamp(header.get("timestamp"))})
**Witness Address:** `{header.get("witness_address", "N/A")}`
**Parent Hash:** `{header.get("parentHash", "N/A")}`
**Transaction Count:** {len(result.get("transactions", []))}
"""
    
    # 添加交易信息
    transactions = result.get("transactions", [])
    if transactions:
        formatted += "\n**Transactions:**\n"
        for i, tx in enumerate(transactions[:10]):  # 最多显示10个交易
            tx_id = tx.get("txID", "N/A")
            formatted += f"  {i+1}. `{tx_id}`\n"
        if len(transactions) > 10:
            formatted += f"  ... and {len(transactions) - 10} more transactions\n"
    
    return formatted


async def get_transaction(tx_hash: str):
    """查询交易信息"""
    if not tx_hash:
        return "Error: Transaction hash is required."
    
    # 获取交易基本信息
    result = await tron_rpc_request("/wallet/gettransactionbyid", {"value": tx_hash})
    
    if "error" in result:
        return f"Error querying transaction: {result['error']}"
    
    if not result or (isinstance(result, dict) and not result.get("raw_data")):
        return "Transaction not found."
    
    # 获取交易收据（包含费用等信息）
    receipt = await tron_rpc_request("/wallet/gettransactioninfobyid", {"value": tx_hash})
    
    raw_data = result.get("raw_data", {})
    contract = raw_data.get("contract", [{}])[0] if raw_data.get("contract") else {}
    parameter = contract.get("parameter", {}).get("value", {})
    
    # 格式化输出
    formatted = f"""### Transaction Information

**Transaction Hash:** `{tx_hash}`
**Type:** {contract.get("type", "N/A")}
**Timestamp:** {raw_data.get("timestamp", "N/A")} ({format_timestamp(raw_data.get("timestamp"))})
**Ref Block:** {raw_data.get("ref_block_bytes", "N/A")}
**Expiration:** {raw_data.get("expiration", "N/A")} ({format_timestamp(raw_data.get("expiration"))})
"""
    
    # 添加合约特定信息
    if "owner_address" in parameter:
        formatted += f"**From:** `{parameter.get('owner_address')}`\n"
    if "to_address" in parameter:
        formatted += f"**To:** `{parameter.get('to_address')}`\n"
    if "amount" in parameter:
        formatted += f"**Amount:** {parameter.get('amount', 0) / 1_000_000:.6f} TRX\n"
    
    # 添加收据信息
    if receipt and isinstance(receipt, dict):
        if "fee" in receipt:
            formatted += f"**Fee:** {receipt.get('fee', 0) / 1_000_000:.6f} TRX\n"
        if "blockNumber" in receipt:
            formatted += f"**Block Number:** {receipt.get('blockNumber')}\n"
        if "receipt" in receipt:
            formatted += f"**Result:** {receipt.get('receipt', {}).get('result', 'N/A')}\n"
        if "energy_usage" in receipt:
            formatted += f"**Energy Used:** {receipt.get('energy_usage')}\n"
        if "energy_fee" in receipt:
            formatted += f"**Energy Fee:** {receipt.get('energy_fee', 0) / 1_000_000:.6f} TRX\n"
    
    return formatted


async def get_account(address: str):
    """查询账户信息"""
    if not address:
        return "Error: Address is required."
    
    result = await tron_rpc_request("/wallet/getaccount", {"address": address, "visible": True})
    
    if "error" in result:
        return f"Error querying account: {result['error']}"
    
    if not result:
        return f"Account `{address}` not found or is inactive.\n\nNote: On TRON, accounts need to be activated by receiving at least 0.1 TRX or any TRC-10 token before they can be queried."
    
    # 格式化输出
    balance_sun = result.get("balance", 0)
    balance_trx = balance_sun / 1_000_000
    
    formatted = f"""### Account Information

**Address:** `{address}`
**Balance:** {balance_trx:.6f} TRX ({balance_sun} sun)
**Account Type:** {result.get("type", "Normal")}
**Create Time:** {format_timestamp(result.get("create_time"))}
**Latest Operation Time:** {format_timestamp(result.get("latest_opration_time"))}
"""
    
    # 添加 TRC-10 代币
    asset_issued = result.get("asset_issued_name")
    if asset_issued:
        formatted += f"\n**Issued Asset:** {bytes.fromhex(asset_issued).decode('utf-8', errors='ignore')}\n"
    
    assetV2 = result.get("assetV2", [])
    if assetV2:
        formatted += "\n**TRC-10 Tokens:**\n"
        for asset in assetV2:
            key = asset.get("key", "N/A")
            value = asset.get("value", 0)
            formatted += f"  - `{key}`: {value}\n"
    
    # 添加冻结资源信息
    frozenV2 = result.get("frozenV2", [])
    if frozenV2:
        formatted += "\n**Frozen Resources (Stake 2.0):**\n"
        for frozen in frozenV2:
            resource_type = frozen.get("type", "UNKNOWN")
            amount = frozen.get("amount", 0)
            formatted += f"  - {resource_type}: {amount / 1_000_000:.6f} TRX\n"
    
    # 添加投票信息
    votes = result.get("votes", [])
    if votes:
        formatted += "\n**Votes:**\n"
        for vote in votes:
            vote_address = vote.get("vote_address", "N/A")
            vote_count = vote.get("vote_count", 0)
            formatted += f"  - `{vote_address}`: {vote_count} votes\n"
    
    # 添加权限信息
    owner_permission = result.get("owner_permission", {})
    if owner_permission:
        formatted += f"\n**Owner Permission Threshold:** {owner_permission.get('threshold', 0)}\n"
    
    return formatted


async def get_account_resource(address: str):
    """查询账户资源信息"""
    if not address:
        return "Error: Address is required."
    
    result = await tron_rpc_request("/wallet/getaccountresource", {"address": address, "visible": True})
    
    if "error" in result:
        return f"Error querying account resource: {result['error']}"
    
    # 格式化输出
    formatted = f"""### Account Resource Information

**Address:** `{address}`

#### Bandwidth (Free & Staked)
- **Free Net Used:** {result.get("freeNetUsed", 0)} / {result.get("freeNetLimit", 0)}
- **Net Used:** {result.get("NetUsed", 0)}
- **Net Limit:** {result.get("NetLimit", 0)}
- **Total Net Limit:** {result.get("TotalNetLimit", 0)}
- **Total Net Weight:** {result.get("TotalNetWeight", 0)}

#### Energy (For Smart Contracts)
- **Energy Used:** {result.get("EnergyUsed", 0)}
- **Energy Limit:** {result.get("EnergyLimit", 0)}
- **Total Energy Limit:** {result.get("TotalEnergyLimit", 0)}
- **Total Energy Weight:** {result.get("TotalEnergyWeight", 0)}
"""
    
    # 添加 Stake 2.0 资源信息
    if "tronPowerLimit" in result:
        formatted += f"\n#### Tron Power\n- **Tron Power Limit:** {result.get('tronPowerLimit', 0)}\n"
    
    if "delegatedBandwidthUsed" in result:
        formatted += f"\n#### Delegated Resources\n- **Delegated Bandwidth Used:** {result.get('delegatedBandwidthUsed', 0)} / {result.get('delegatedBandwidthLimit', 0)}\n"
    
    if "delegatedEnergyUsed" in result:
        formatted += f"- **Delegated Energy Used:** {result.get('delegatedEnergyUsed', 0)} / {result.get('delegatedEnergyLimit', 0)}\n"
    
    return formatted


async def get_now_block():
    """获取最新区块"""
    result = await tron_rpc_request("/wallet/getnowblock", {})
    
    if "error" in result:
        return f"Error querying latest block: {result['error']}"
    
    if not result or (isinstance(result, dict) and not result.get("block_header")):
        return "Failed to get latest block."
    
    header = result.get("block_header", {}).get("raw_data", {})
    block_id = result.get("blockID", "N/A")
    
    formatted = f"""### Latest Block

**Block Hash (ID):** `{block_id}`
**Block Number:** {header.get("number", "N/A")}
**Timestamp:** {header.get("timestamp", "N/A")} ({format_timestamp(header.get("timestamp"))})
**Witness Address:** `{header.get("witness_address", "N/A")}`
**Parent Hash:** `{header.get("parentHash", "N/A")}`
**Version:** {header.get("version", "N/A")}
**Transaction Count:** {len(result.get("transactions", []))}
"""
    
    return formatted


def format_timestamp(timestamp_ms):
    """将毫秒时间戳格式化为可读格式"""
    if not timestamp_ms:
        return "N/A"
    from datetime import datetime
    try:
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(timestamp_ms)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
