"""Phase 3 快速验证脚本 — 不需要启动 agent-service。

用法：
  cd /mnt/d/claude/mall/agent-service
  python3 tests/test_phase3_smoke.py

验证内容：
  1. Redis db3 连接
  2. Session 存储（序列化/反序列化/滑动 TTL）
  3. 用户画像 CRUD + merge 逻辑
  4. 画像格式化输出
"""

import asyncio
import json
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import redis.asyncio as aioredis


async def test_redis_connection():
    """验证 Redis db3 连接。"""
    print("=" * 50)
    print("1. Redis db3 连接测试")
    print("=" * 50)

    r = aioredis.from_url("redis://localhost:6379/3")
    pong = await r.ping()
    assert pong, "Redis PING 失败"
    print("   ✅ Redis db3 连接正常")

    # 清理测试 key
    await r.flushdb()
    print("   ✅ db3 已清空（测试前清理）")
    await r.aclose()


async def test_session_store():
    """验证 RedisSessionStore 核心功能。"""
    print("\n" + "=" * 50)
    print("2. Session 存储测试")
    print("=" * 50)

    from langchain_core.messages import AIMessage, HumanMessage

    # 需要设置环境变量
    import os
    os.environ.setdefault("LLM_API_KEY", "test")
    os.environ.setdefault("JWT_SECRET", "test")

    from app.agent.session import RedisSessionStore

    store = RedisSessionStore()

    # 测试 1: 空 session 返回空列表
    history = await store.get_history("test-empty")
    assert history == [], f"空 session 应返回 []，实际返回 {history}"
    print("   ✅ 空 session 返回空列表")

    # 测试 2: 添加消息并读取
    await store.add_message("test-1", HumanMessage(content="你好"))
    await store.add_message("test-1", AIMessage(content="你好！有什么可以帮您的吗？"))
    history = await store.get_history("test-1")
    assert len(history) == 2, f"应有 2 条消息，实际 {len(history)}"
    assert isinstance(history[0], HumanMessage)
    assert isinstance(history[1], AIMessage)
    assert history[0].content == "你好"
    print("   ✅ 消息添加和读取正常")

    # 测试 3: get_raw_history_dicts
    dicts = await store.get_raw_history_dicts("test-1")
    assert len(dicts) == 2
    assert dicts[0] == {"role": "user", "content": "你好"}
    assert dicts[1] == {"role": "assistant", "content": "你好！有什么可以帮您的吗？"}
    print("   ✅ get_raw_history_dicts 格式正确")

    # 测试 4: 滑动 TTL（检查 key 存在且有 TTL）
    key = store._make_key("test-1")
    ttl = await store.redis.ttl(key)
    assert ttl > 0, f"应有正 TTL，实际 {ttl}"
    assert ttl <= store.ttl, f"TTL 应 <= {store.ttl}，实际 {ttl}"
    print(f"   ✅ 滑动 TTL 正常（剩余 {ttl}s）")

    # 测试 5: clear
    await store.clear("test-1")
    history = await store.get_history("test-1")
    assert history == [], "clear 后应返回空"
    print("   ✅ clear 正常")

    # 测试 6: max_turns 限制
    for i in range(25):
        await store.add_message("test-limit", HumanMessage(content=f"消息 {i}"))
        await store.add_message("test-limit", AIMessage(content=f"回复 {i}"))
    history = await store.get_history("test-limit")
    max_msgs = store.max_turns * 2  # 20 * 2 = 40
    assert len(history) <= max_msgs, f"应 <= {max_msgs} 条，实际 {len(history)}"
    print(f"   ✅ max_turns 限制正常（{len(history)} 条 / 上限 {max_msgs}）")

    # 清理
    await store.clear("test-limit")
    print("   ✅ 所有 session 测试通过")


async def test_user_profile_store():
    """验证 UserProfileStore CRUD + merge。"""
    print("\n" + "=" * 50)
    print("3. 用户画像存储测试")
    print("=" * 50)

    import os
    os.environ.setdefault("LLM_API_KEY", "test")
    os.environ.setdefault("JWT_SECRET", "test")

    from app.memory.user_profile import UserProfileStore

    store = UserProfileStore()

    # 测试 1: 空画像返回 None
    profile = await store.get_profile("test-user")
    assert profile is None, f"空画像应返回 None，实际 {profile}"
    print("   ✅ 空画像返回 None")

    # 测试 2: 保存和读取
    test_profile = {
        "preferred_categories": ["手机", "耳机"],
        "price_range": {"min": 1000, "max": 5000},
        "brand_preferences": ["索尼"],
    }
    await store.save_profile("test-user", test_profile)
    loaded = await store.get_profile("test-user")
    assert loaded is not None
    assert loaded["preferred_categories"] == ["手机", "耳机"]
    assert loaded["updated_at"] is not None  # save_profile 自动添加
    print("   ✅ 保存和读取正常")

    # 测试 3: merge 逻辑
    new_data = {
        "preferred_categories": ["耳机", "笔记本"],  # 耳机重复
        "price_range": {"min": 2000, "max": 3000},  # 交集
        "brand_preferences": ["苹果"],
        "disliked": ["廉价感"],
    }
    merged = store._merge(test_profile, new_data)

    # 列表去重合并
    assert "手机" in merged["preferred_categories"]
    assert "耳机" in merged["preferred_categories"]
    assert "笔记本" in merged["preferred_categories"]
    assert len(merged["preferred_categories"]) == 3  # 去重后 3 个
    print("   ✅ 列表合并去重正常")

    # 价格取交集
    assert merged["price_range"]["min"] == 2000  # max(1000, 2000)
    assert merged["price_range"]["max"] == 3000  # min(5000, 3000)
    print("   ✅ 价格范围取交集正常")

    # 新增字段
    assert merged["disliked"] == ["廉价感"]
    print("   ✅ 新增字段正常")

    # 测试 4: format_for_prompt
    formatted = store.format_for_prompt(loaded)
    assert "【用户偏好（自动学习）】" in formatted
    assert "手机" in formatted
    assert "索尼" in formatted
    print("   ✅ format_for_prompt 格式正确")
    print(f"\n   格式化输出预览：")
    for line in formatted.split("\n"):
        print(f"   {line}")

    # 测试 5: 删除
    deleted = await store.delete_profile("test-user")
    assert deleted, "删除应返回 True"
    profile = await store.get_profile("test-user")
    assert profile is None
    print("   ✅ 删除正常")

    # 测试 6: _parse_json 兼容 markdown 代码块
    json_str = '```json\n{"preferred_categories": ["手机"]}\n```'
    parsed = store._parse_json(json_str)
    assert parsed == {"preferred_categories": ["手机"]}
    print("   ✅ _parse_json 兼容 markdown 代码块")

    print("   ✅ 所有画像测试通过")


async def main():
    print("🧪 Phase 3 快速验证\n")

    try:
        await test_redis_connection()
        await test_session_store()
        await test_user_profile_store()

        # 最终清理
        r = aioredis.from_url("redis://localhost:6379/3")
        await r.flushdb()
        await r.aclose()

        print("\n" + "=" * 50)
        print("🎉 所有测试通过！Phase 3 基础功能正常。")
        print("=" * 50)
        print("\n下一步：启动 agent-service 测试 API 端点")
        print("  uvicorn app.main:app --reload --port 8000")
        print("  然后用 curl 测试：")
        print('  curl http://localhost:8000/api/v1/user/profile -H "Authorization: Bearer <token>"')

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
