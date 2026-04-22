#!/usr/bin/env python3
"""Test mem0 on the first query from LongMemEval dataset."""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Monkey patch sqlite3 with pysqlite3 for Qdrant local storage
# This fixes the "no such table: pragma_compile_options" error
try:
    import pysqlite3 as sqlite3_module
    sys.modules["sqlite3"] = sqlite3_module
except ImportError:
    pass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import cmemory components
from cmemory.engines.mem0_engine import Mem0Engine
from cmemory.evaluation.qa_evaluator import QAEvaluator
from cmemory.evaluation.judge import LLMJudge


def load_dataset():
    """Load LongMemEval dataset."""
    dataset_path = Path(__file__).parent.parent / "datasets" / "LongMemEval" / "longmemeval_oracle.json"
    with open(dataset_path, "r") as f:
        data = json.load(f)
    return data


def get_first_query(data):
    """Get the first query from the dataset."""
    return data[0]


def format_session_messages(session):
    """Format a session's messages for adding to memory."""
    messages = []
    for msg in session:
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })
    return messages


def run_mem0_test():
    """Run mem0 test on the first query."""
    print("=" * 60)
    print("Mem0 测试 - LongMemEval 数据集第一个Query")
    print("=" * 60)

    # Load dataset
    data = load_dataset()
    first_query = get_first_query(data)

    print(f"\n[1] 数据集信息:")
    print(f"    Question ID: {first_query['question_id']}")
    print(f"    Question Type: {first_query['question_type']}")
    print(f"    Question: {first_query['question']}")
    print(f"    Expected Answer: {first_query['answer']}")
    print(f"    Question Date: {first_query['question_date']}")

    # Initialize Mem0 engine
    print(f"\n[2] 初始化 Mem0 Engine...")

    # Clean up previous test data
    storage_path = Path(__file__).parent.parent / ".memory_data" / "mem0_test"
    if storage_path.exists():
        import shutil
        shutil.rmtree(storage_path)

    engine = Mem0Engine(
        user_id="test_user_mem0",
        config={
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "mem0_test_collection",
                    "embedding_model_dims": int(os.getenv("EMBEDDING_DIMS", "1536")),
                    "path": str(storage_path),
                    "on_disk": True,
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                },
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": os.getenv("QA_MODEL", "gpt-4o-mini"),
                },
            },
        },
    )

    # Stage 1: Memory Construction - Add haystack sessions to Mem0
    print(f"\n[3] Stage 1: 记忆构建 (Memory Construction)")
    print(f"    添加 {len(first_query['haystack_sessions'])} 个会话到 Mem0...")

    stored_memories = []
    add_times = []

    for i, session in enumerate(first_query['haystack_sessions']):
        session_id = first_query['haystack_session_ids'][i]
        print(f"\n    --- Session {i+1}: {session_id} ---")
        print(f"    Messages count: {len(session)}")

        session_start = time.time()
        session_memories = []

        for msg in session:
            content = msg['content']
            role = msg['role']
            has_answer = msg.get('has_answer', False)

            # Parse timestamp from haystack_dates if available
            if i < len(first_query['haystack_dates']):
                date_str = first_query['haystack_dates'][i]
                # Parse date string like "2023/04/10 (Mon) 17:50"
                try:
                    ts = datetime.strptime(date_str.split('(')[0].strip() + " " + date_str.split()[-1], "%Y/%m/%d %H:%M")
                except:
                    ts = datetime.now()
            else:
                ts = datetime.now()

            # Add to Mem0
            memory_id = engine.add(
                content=content,
                role=role,
                timestamp=ts,
                metadata={
                    "session_id": session_id,
                    "has_answer": has_answer,
                },
            )

            session_memories.append({
                "memory_id": memory_id,
                "content": content[:100] + "..." if len(content) > 100 else content,
                "role": role,
                "has_answer": has_answer,
            })

        session_time = time.time() - session_start
        add_times.append(session_time)

        print(f"    Session {i+1} 处理时间: {session_time:.2f}s")
        stored_memories.extend(session_memories)

    engine.save()
    print(f"\n    总计存储记忆数: {len(stored_memories)}")
    print(f"    总构建时间: {sum(add_times):.2f}s")

    # Get all stored memories
    print(f"\n[4] Mem0 存储后的记忆列表:")
    all_memories = engine._memory_client.get_all(filters={"user_id": engine.user_id})

    if isinstance(all_memories, dict):
        memories_list = all_memories.get("results", [])
    else:
        memories_list = all_memories if all_memories else []

    print(f"    Mem0 存储记忆总数: {len(memories_list)}")

    for i, mem in enumerate(memories_list):
        content_preview = mem.get("memory", "")[:150] + "..." if len(mem.get("memory", "")) > 150 else mem.get("memory", "")
        print(f"\n    Memory {i+1}:")
        print(f"      ID: {mem.get('id', 'unknown')}")
        print(f"      Content: {content_preview}")
        print(f"      Metadata: {mem.get('metadata', {})}")

    # Stage 2: Memory Retrieval
    print(f"\n[5] Stage 2: 记忆检索 (Memory Retrieval)")
    question = first_query['question']
    print(f"    Query: {question}")

    retrieval_start = time.time()
    retrieved = engine.search(question, limit=10)
    retrieval_time = time.time() - retrieval_start

    print(f"\n    检索结果 (共 {len(retrieved)} 条):")
    retrieved_memories = []

    for i, result in enumerate(retrieved):
        content_preview = result['content'][:150] + "..." if len(result['content']) > 150 else result['content']
        print(f"\n    Retrieved {i+1}:")
        print(f"      Score: {result['score']:.4f}")
        print(f"      Memory ID: {result['memory_id']}")
        print(f"      Content: {content_preview}")
        print(f"      Metadata: {result.get('metadata', {})}")
        retrieved_memories.append({
            "score": result['score'],
            "memory_id": result['memory_id'],
            "content": result['content'],
            "metadata": result.get('metadata', {}),
        })

    print(f"\n    检索时间: {retrieval_time:.2f}s")

    # Stage 3: QA Evaluation
    print(f"\n[6] Stage 3: QA 评估")

    # Format context for QA
    if not retrieved:
        context = "No relevant memories found."
    else:
        lines = ["Retrieved memories:"]
        for i, mem in enumerate(retrieved, 1):
            lines.append(f"{i}. {mem['content']} (score: {mem['score']:.2f})")
        context = "\n".join(lines)

    print(f"    Context 长度: {len(context)} 字符")

    # Initialize QA evaluator and judge
    qa_evaluator = QAEvaluator(
        model=os.getenv("QA_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
    )

    judge = LLMJudge(
        model=os.getenv("JUDGE_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
    )

    # Generate answer
    print(f"\n    生成回答...")
    qa_start = time.time()
    generated_answer = qa_evaluator.generate_answer(question, context)
    qa_time = time.time() - qa_start

    print(f"\n    Mem0 生成的回答:")
    print(f"    {generated_answer}")
    print(f"    QA 时间: {qa_time:.2f}s")

    # Judge the answer
    print(f"\n    Judge 评估...")
    judge_start = time.time()
    is_correct, reasoning = judge.evaluate(question, (first_query['answer'],), generated_answer)
    judge_time = time.time() - judge_start

    print(f"\n    Judge 结果: {'正确' if is_correct else '错误'}")
    print(f"    Judge 理由: {reasoning}")
    print(f"    Judge 时间: {judge_time:.2f}s")

    # Engine stats
    print(f"\n[7] Engine 统计信息:")
    stats = engine.get_stats()
    print(f"    Tokens:")
    print(f"      Prompt: {stats['tokens']['prompt']}")
    print(f"      Completion: {stats['tokens']['completion']}")
    print(f"      Total: {stats['tokens']['total']}")
    print(f"    API Calls:")
    print(f"      Add: {stats['api_calls']['add']}")
    print(f"      Search: {stats['api_calls']['search']}")
    print(f"    Time:")
    print(f"      Add: {stats['time_seconds']['add']:.2f}s")
    print(f"      Search: {stats['time_seconds']['search']:.2f}s")
    print(f"      Total: {stats['time_seconds']['total']:.2f}s")
    print(f"    Memory Count: {stats['memory']['count']}")

    # Compile all results
    results = {
        "query_info": {
            "question_id": first_query['question_id'],
            "question_type": first_query['question_type'],
            "question": first_query['question'],
            "expected_answer": first_query['answer'],
            "question_date": first_query['question_date'],
            "haystack_session_count": len(first_query['haystack_sessions']),
        },
        "memory_construction": {
            "total_messages_added": len(stored_memories),
            "sessions_added": len(first_query['haystack_sessions']),
            "total_time_seconds": sum(add_times),
            "stored_memories_preview": stored_memories[:20],  # First 20 for preview
        },
        "mem0_stored_memories": {
            "total_count": len(memories_list),
            "memories": [
                {
                    "id": mem.get("id"),
                    "content": mem.get("memory", ""),
                    "metadata": mem.get("metadata", {}),
                }
                for mem in memories_list
            ],
        },
        "memory_retrieval": {
            "query": question,
            "retrieval_time_seconds": retrieval_time,
            "retrieved_count": len(retrieved),
            "retrieved_memories": retrieved_memories,
        },
        "qa_evaluation": {
            "context": context,
            "generated_answer": generated_answer,
            "qa_time_seconds": qa_time,
        },
        "judge_evaluation": {
            "is_correct": is_correct,
            "reasoning": reasoning,
            "judge_time_seconds": judge_time,
        },
        "engine_stats": stats,
        "total_evaluation_time": sum(add_times) + retrieval_time + qa_time + judge_time,
    }

    # Clean up
    print(f"\n[8] 清理...")
    engine.clear()

    print(f"\n" + "=" * 60)
    print(f"测试完成!")
    print(f"=" * 60)

    return results


def save_results_to_md(results):
    """Save results to markdown file."""
    md_path = Path(__file__).parent.parent / "docs" / "mem0_longmemeval_first_query_result.md"

    md_content = f"""# Mem0 测试结果 - LongMemEval 数据集第一个 Query

测试日期: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 1. Query 信息

| 字段 | 值 |
|------|-----|
| Question ID | `{results['query_info']['question_id']}` |
| Question Type | `{results['query_info']['question_type']}` |
| Question Date | `{results['query_info']['question_date']}` |
| Haystack Session Count | `{results['query_info']['haystack_session_count']}` |

### 问题内容

**Question:**

> {results['query_info']['question']}

**Expected Answer:**

> {results['query_info']['expected_answer']}

---

## 2. 记忆构建阶段 (Memory Construction)

### 构建统计

| 指标 | 值 |
|------|-----|
| 添加的消息总数 | `{results['memory_construction']['total_messages_added']}` |
| 添加的会话数 | `{results['memory_construction']['sessions_added']}` |
| 构建总时间 | `{results['memory_construction']['total_time_seconds']:.2f}s` |

### 添加的消息预览 (前20条)

```json
{json.dumps(results['memory_construction']['stored_memories_preview'], indent=2, ensure_ascii=False)}
```

---

## 3. Mem0 存储后的记忆

### 存储统计

| 指标 | 值 |
|------|-----|
| 存储记忆总数 | `{results['mem0_stored_memories']['total_count']}` |

### Mem0 存储的记忆详情

```json
{json.dumps(results['mem0_stored_memories']['memories'], indent=2, ensure_ascii=False)}
```

---

## 4. 记忆检索阶段 (Memory Retrieval)

### 检索统计

| 指标 | 值 |
|------|-----|
| 检索 Query | `{results['memory_retrieval']['query']}` |
| 检索时间 | `{results['memory_retrieval']['retrieval_time_seconds']:.2f}s` |
| 检索结果数 | `{results['memory_retrieval']['retrieved_count']}` |

### 检索结果详情

```json
{json.dumps(results['memory_retrieval']['retrieved_memories'], indent=2, ensure_ascii=False)}
```

---

## 5. QA 评估阶段

### QA 统计

| 挀标 | 值 |
|------|-----|
| QA 时间 | `{results['qa_evaluation']['qa_time_seconds']:.2f}s` |

### 使用的 Context

```
{results['qa_evaluation']['context']}
```

### Mem0 生成的回答

> {results['qa_evaluation']['generated_answer']}

---

## 6. Judge 评估结果

| 挀标 | 值 |
|------|-----|
| 是否正确 | **{results['judge_evaluation']['is_correct']}** |
| Judge 时间 | `{results['judge_evaluation']['judge_time_seconds']:.2f}s` |

### Judge 理由

> {results['judge_evaluation']['reasoning']}

---

## 7. Engine 统计信息

### Token 消耗

| 类型 | 数量 |
|------|------|
| Prompt Tokens | `{results['engine_stats']['tokens']['prompt']}` |
| Completion Tokens | `{results['engine_stats']['tokens']['completion']}` |
| Total Tokens | `{results['engine_stats']['tokens']['total']}` |

### API 调用次数

| 操作 | 次数 |
|------|------|
| Add Calls | `{results['engine_stats']['api_calls']['add']}` |
| Search Calls | `{results['engine_stats']['api_calls']['search']}` |

### 时间消耗

| 操作 | 时间 |
|------|------|
| Add Time | `{results['engine_stats']['time_seconds']['add']:.2f}s` |
| Search Time | `{results['engine_stats']['time_seconds']['search']:.2f}s` |
| Total Time | `{results['engine_stats']['time_seconds']['total']:.2f}s` |

### Memory 统计

| 挀标 | 值 |
|------|-----|
| Memory Count | `{results['engine_stats']['memory']['count']}` |
| Storage Size | `{results['engine_stats']['memory']['storage_bytes']} bytes` |

---

## 8. 总结

### 总体结果

| 挀标 | 值 |
|------|-----|
| **最终判定** | **{'✅ 正确' if results['judge_evaluation']['is_correct'] else '❌ 错误'}** |
| 总评估时间 | `{results['total_evaluation_time']:.2f}s` |

### 问题回顾

**Question:** {results['query_info']['question']}

**Expected Answer:** {results['query_info']['expected_answer']}

**Generated Answer:** {results['qa_evaluation']['generated_answer']}

---

## 附录: 完整原始结果 JSON

```json
{json.dumps(results, indent=2, ensure_ascii=False)}
```

---
"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n结果已保存到: {md_path}")
    return md_path


if __name__ == "__main__":
    results = run_mem0_test()
    save_results_to_md(results)