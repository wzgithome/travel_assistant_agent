"""
轻量 RAG 知识库工具。

语料(data/knowledge/*.json)是长期稳定的旅行知识(景点历史文化、美食特色、避坑贴士等),
通过 embedding 检索最相关的 top-k 条返回给模型,补充模型自身记忆的不足。
实时数据(天气/交通/酒店等)仍由对应实时工具负责,本工具不替代它们。

Embedding 复用现有 DashScope 配置(OPENAI_API_KEY2 / OPENAI_BASE_URL2),
模型 text-embedding-v4,无需新增密钥或依赖。
"""
import json
import math
import os

from openai import OpenAI

from config.settings import API_KEY, BASE_URL
from utils.tokenizer import _truncate_observation

EMBEDDING_MODEL = "text-embedding-v4"
DIMENSIONS = 1024

_KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "knowledge")
_INDEX_FILE = os.path.join(os.path.dirname(_KNOWLEDGE_DIR), "knowledge_embeddings.json")

_index_cache: list[dict] | None = None


def _embed(texts: list[str]) -> list[list[float]]:
    """批量获取文本向量(OpenAI 兼容接口),返回顺序与输入一致。
    DashScope 单次请求最多 10 条,超限自动分批。"""
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    results: list[list[float]] = []
    for i in range(0, len(texts), 10):
        batch = texts[i:i + 10]
        resp = client.embeddings.create(model=EMBEDDING_MODEL, input=batch, dimensions=DIMENSIONS)
        if len(resp.data) != len(batch):
            raise RuntimeError(f"embedding 返回数量不一致: 期望 {len(batch)}, 实际 {len(resp.data)}")
        results.extend(d.embedding for d in resp.data)
    return results


def _normalize(vec: list[float]) -> list[float]:
    """向量归一化,归一化后余弦相似度 = 点积"""
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec]


def _load_corpus_chunks() -> list[dict]:
    """读取 data/knowledge/ 下所有语料文件"""
    chunks = []
    if not os.path.isdir(_KNOWLEDGE_DIR):
        return chunks
    for fname in sorted(os.listdir(_KNOWLEDGE_DIR)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(_KNOWLEDGE_DIR, fname), encoding="utf-8") as f:
            data = json.load(f)
        for c in data.get("chunks", []):
            chunks.append({
                "city": data["city"],
                "aliases": data.get("aliases", []),
                "category": c.get("category", ""),
                "title": c.get("title", ""),
                "content": c.get("content", ""),
            })
    return chunks


def _index_stale() -> bool:
    """任一语料文件比索引缓存新(或缓存不存在)时视为过期"""
    if not os.path.exists(_INDEX_FILE):
        return True
    if not os.path.isdir(_KNOWLEDGE_DIR):
        return True
    index_mtime = os.path.getmtime(_INDEX_FILE)
    return any(
        os.path.getmtime(os.path.join(_KNOWLEDGE_DIR, f)) > index_mtime
        for f in os.listdir(_KNOWLEDGE_DIR) if f.endswith(".json")
    )


def _build_index() -> list[dict]:
    """为全部语料生成向量并落盘缓存"""
    chunks = _load_corpus_chunks()
    if not chunks:
        return []
    print(f"📚 正在构建知识库索引({len(chunks)} 条语料, 模型 {EMBEDDING_MODEL})...")
    vecs = _embed([f"{c['city']} {c['title']} {c['content']}" for c in chunks])
    for c, vec in zip(chunks, vecs):
        c["vec"] = _normalize(vec)
    os.makedirs(os.path.dirname(_INDEX_FILE), exist_ok=True)
    with open(_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump({"chunks": chunks}, f, ensure_ascii=False)
    print("✅ 知识库索引构建完成")
    return chunks


def _load_index() -> list[dict]:
    """懒加载索引:内存缓存 → 磁盘缓存 → 自动重建"""
    global _index_cache
    if _index_cache is not None:
        return _index_cache
    if not _index_stale():
        try:
            with open(_INDEX_FILE, encoding="utf-8") as f:
                _index_cache = json.load(f)["chunks"]
            return _index_cache
        except (json.JSONDecodeError, KeyError, OSError):
            pass
    _index_cache = _build_index()
    return _index_cache


def _cosine(a: list[float], b: list[float]) -> float:
    """余弦相似度(向量已归一化,即点积)"""
    return sum(x * y for x, y in zip(a, b))


def get_knowledge(city: str, topic: str = "") -> str:
    """
    查询该城市的历史文化、景点介绍、美食特色、避坑经验等稳定知识。
    检索语料库中与该城市和主题最相关的资料,作为回答的依据补充。

    Args:
        city: 城市名
        topic: 查询主题(如"故宫历史"、"特色美食"),可留空
    """
    chunks = _load_index()
    city = (city or "").strip()
    topic = (topic or "").strip()

    candidates = [
        c for c in chunks
        if city and (city == c["city"] or city in c["aliases"] or c["city"] in city)
    ]
    if not candidates:
        return f"📚 知识库暂无 {city or '该城市'} 的稳定资料,请通过其他实时工具获取信息。"

    try:
        qvec = _normalize(_embed([f"{city} {topic}".strip()])[0])
    except Exception as e:
        return f"错误：知识库检索失败（{e}），请改用其他工具获取信息。"

    ranked = sorted(candidates, key=lambda c: _cosine(qvec, c["vec"]), reverse=True)
    lines = [f"📚 {city}知识库:"]
    for c in ranked[:3]:
        lines.append(f"◆ {c['title']}（{c['category']}）：{c['content']}")
    return _truncate_observation("\n".join(lines))
