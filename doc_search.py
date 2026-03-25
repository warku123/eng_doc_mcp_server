"""文档搜索模块 - 提供三层降级搜索策略"""
import os
import json
import httpx
from typing import List, Dict, Any, Optional

from index_fetcher import fetch_all_docs
from config import (
    get_doc_source_config,
    get_general_config,
    get_max_limit
)


def perform_search(query: str, index_path: str, base_url: str, limit: int = 5) -> str:
    """搜索本地 MkDocs 索引 - 基于分数的匹配"""
    if not os.path.exists(index_path):
        return f"Error: Index not found at {index_path}. Run 'mkdocs build'."
    
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 按空格分词
    query_words = [w.strip() for w in query.lower().split() if len(w.strip()) > 1]
    if not query_words:
        query_words = [query.lower()]

    hits = []
    for doc in data['docs']:
        title_lower = doc['title'].lower()
        text_lower = doc.get('text', '').lower()
        
        # 分数匹配：标题命中 +3，内容命中 +1
        score = 0
        for word in query_words:
            if word in title_lower:
                score += 3
            if word in text_lower:
                score += 1
        
        if score > 0:
            excerpt = (doc.get('text') or '')[:200]
            hits.append((score, doc['title'], doc['location'], excerpt))
    
    # 按分数排序
    hits.sort(key=lambda x: x[0], reverse=True)
    
    if not hits:
        return "No relevant documentation found."
    
    # 取前 limit 个结果
    results = []
    for score, title, location, excerpt in hits[:limit]:
        results.append(f"### {title}\nURL: {base_url}{location}\nExcerpt: {excerpt}...")
    
    return "\n\n".join(results)


async def search_via_local_cache(
    query: str,
    limit: int,
    source_name: str = 'tron_developers',
    config_path: str = "./docs_config.yaml"
) -> str:
    """通过本地缓存搜索（备用方案）"""
    docs = await fetch_all_docs(source_name, config_path)
    
    if not docs:
        return "Error: Failed to load documentation cache."
    
    # 获取配置中的 base_url
    config = get_doc_source_config(source_name, config_path)
    base_url = config.get('base_url', 'https://developers.tron.network/')
    
    # 搜索逻辑
    query_words = [w.strip().lower() for w in query.split() if len(w.strip()) > 1]
    if not query_words:
        query_words = [query.lower()]
    
    hits = []
    for doc in docs:
        title_lower = doc['title'].lower()
        text_lower = doc['text'].lower()
        
        score = 0
        for word in query_words:
            if word in title_lower:
                score += 3
            if word in text_lower:
                score += 1
        
        if score > 0:
            hits.append((score, doc))
    
    # 按分数排序
    hits.sort(key=lambda x: x[0], reverse=True)
    
    if not hits:
        return "No relevant documentation found."
    
    results = []
    for score, doc in hits[:limit]:
        excerpt = doc['text'][:200]
        url = f"{base_url.rstrip('/')}{doc['location']}"
        results.append(f"### {doc['title']}\nURL: {url}\nExcerpt: {excerpt}...")
    
    return f"## TRON Developer Docs Results ({len(results)} found, via local cache)\n\n" + "\n\n".join(results)


async def search_via_readme_api(
    query: str,
    limit: int,
    config_path: str = "./docs_config.yaml"
) -> str:
    """通过 ReadMe 原生搜索 API 搜索（无需身份验证）"""
    # 获取 API 配置
    config = get_doc_source_config('tron_developers', config_path)
    api_config = config.get('api_config', {})
    endpoint = api_config.get('endpoint')
    
    if not endpoint:
        return "Error: API endpoint not configured."
    
    params = {"query": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(endpoint, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        total = data.get("total", 0)
        hits = data.get("data", [])
        
        if not hits:
            return f"No results found for '{query}'."
        
        results = []
        for hit in hits[:limit]:
            title = hit.get("title", "Untitled")
            url = hit.get("url", {}).get("full", "")
            if not url:
                url = f"https://developers.tron.network{hit.get('url', {}).get('relative', '')}"
            
            # 从 highlights 提取摘要
            highlights = hit.get("highlights", [])
            excerpt_parts = []
            for h in highlights:
                if h.get("type") == "text":
                    excerpt_parts.append(h.get("value", ""))
            excerpt = " ".join(excerpt_parts)[:300]
            
            results.append(f"### {title}\nURL: {url}\nExcerpt: {excerpt}...")
        
        return f"## TRON Developer Docs Results ({min(len(hits), limit)} of {total} found)\n\n" + "\n\n".join(results)


async def search_docs_three_tier(
    source_name: str,
    query: str,
    limit: int = 5,
    config_path: str = "./docs_config.yaml"
) -> str:
    """
    统一的三层文档搜索函数
    
    Args:
        source_name: 文档源名称（如 'java_tron', 'tron_developers'）
        query: 搜索关键词
        limit: 返回结果数量
        config_path: 配置文件路径
    """
    if not query.strip():
        return "Error: Query is required."
    
    # 加载配置
    config = get_doc_source_config(source_name, config_path)
    limit = min(max(limit, 1), get_max_limit(config_path))
    
    strategy = config.get('search_strategy', {})
    index_path = config.get('index_path', '')
    base_url = config.get('base_url', '')
    
    errors = []
    
    # 第1层：MkDocs 本地索引搜索
    if strategy.get('enable_mkdocs', False):
        if os.path.exists(index_path):
            try:
                result = perform_search(query, index_path, base_url, limit)
                if result and not result.startswith("Error") and result != "No relevant documentation found.":
                    return result
            except Exception as e:
                errors.append(f"MkDocs index: {str(e)}")
        else:
            errors.append(f"MkDocs index: File not found at {index_path}")
    
    # 第2层：本地缓存搜索
    if strategy.get('enable_cache', False):
        try:
            return await search_via_local_cache(query, limit, source_name, config_path)
        except Exception as e:
            errors.append(f"Local cache: {str(e)}")
    
    # 第3层：ReadMe API 实时搜索
    if strategy.get('enable_api', False):
        try:
            return await search_via_readme_api(query, limit, config_path)
        except Exception as e:
            errors.append(f"ReadMe API: {str(e)}")
    
    # 所有方案都失败
    if errors:
        return f"Error searching documentation. All methods failed: {'; '.join(errors)}"
    return "No relevant documentation found."
