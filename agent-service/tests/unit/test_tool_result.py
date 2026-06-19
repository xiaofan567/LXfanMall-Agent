"""Tool result store tests — mutual exclusion logic.

Source: app/agent/tool_result.py

Key behavior: tools in different _MUTEX_GROUPS clear each other.
  - search_products (GROUP A) ↔ get_recommendations/get_hot/get_new (GROUP B)
  - get_user_orders (GROUP C) ↔ get_order_detail (GROUP D)
"""

import pytest

from app.agent.tool_result import ToolResultStore, set_current_request_id


class TestToolResultStore:
    def setup_method(self):
        self.store = ToolResultStore()
        set_current_request_id("test-req-001")

    # ── basic store and retrieve ───────────────────────────────

    def test_store_and_get(self):
        self.store.store("search_products", [{"id": 1, "name": "test"}])
        result = self.store.get_and_clear("test-req-001")
        assert len(result) == 1
        assert result[0]["tool"] == "search_products"
        assert result[0]["data"] == [{"id": 1, "name": "test"}]

    def test_get_and_clear_deletes_data(self):
        self.store.store("search_products", [{"id": 1}])
        self.store.get_and_clear("test-req-001")
        # second call should return empty
        assert self.store.get_and_clear("test-req-001") == []

    def test_get_unknown_request_returns_empty(self):
        assert self.store.get_and_clear("nonexistent-id") == []

    # ── no request id = skip storage ───────────────────────────

    def test_empty_request_id_skips_storage(self):
        set_current_request_id("")
        self.store.store("search_products", [{"id": 1}])
        assert self.store.get_and_clear("") == []

    # ── mutual exclusion: search ↔ recommend ───────────────────

    def test_search_clears_recommend(self):
        """Storing search_products should clear get_recommendations."""
        self.store.store("get_recommendations", [{"id": 1}])
        self.store.store("search_products", [{"id": 2}])
        result = self.store.get_and_clear("test-req-001")
        tools = [r["tool"] for r in result]
        assert "search_products" in tools
        assert "get_recommendations" not in tools

    def test_recommend_clears_search(self):
        """Storing get_recommendations should clear search_products."""
        self.store.store("search_products", [{"id": 1}])
        self.store.store("get_recommendations", [{"id": 2}])
        result = self.store.get_and_clear("test-req-001")
        tools = [r["tool"] for r in result]
        assert "get_recommendations" in tools
        assert "search_products" not in tools

    def test_multiple_recommend_tools_coexist(self):
        """Tools within the same group (recommend) should coexist."""
        self.store.store("get_recommendations", [{"id": 1}])
        self.store.store("get_hot_products", [{"id": 2}])
        self.store.store("get_new_products", [{"id": 3}])
        result = self.store.get_and_clear("test-req-001")
        tools = [r["tool"] for r in result]
        assert len(tools) == 3
        assert "get_recommendations" in tools
        assert "get_hot_products" in tools
        assert "get_new_products" in tools

    # ── mutual exclusion: order_list ↔ order_detail ────────────

    def test_order_list_clears_order_detail(self):
        """Storing get_user_orders should clear get_order_detail."""
        self.store.store("get_order_detail", {"id": 100})
        self.store.store("get_user_orders", [{"id": 1}, {"id": 2}])
        result = self.store.get_and_clear("test-req-001")
        tools = [r["tool"] for r in result]
        assert "get_user_orders" in tools
        assert "get_order_detail" not in tools

    def test_order_detail_clears_order_list(self):
        """Storing get_order_detail should clear get_user_orders."""
        self.store.store("get_user_orders", [{"id": 1}])
        self.store.store("get_order_detail", {"id": 100})
        result = self.store.get_and_clear("test-req-001")
        tools = [r["tool"] for r in result]
        assert "get_order_detail" in tools
        assert "get_user_orders" not in tools

    # ── non-mutex tools coexist ────────────────────────────────

    def test_non_mutex_tools_coexist(self):
        """Tools not in any mutex group should coexist with everything."""
        self.store.store("search_products", [{"id": 1}])
        self.store.store("get_logistics", {"tracking": "123"})
        self.store.store("get_addresses", [{"id": 1}])
        result = self.store.get_and_clear("test-req-001")
        tools = [r["tool"] for r in result]
        assert "search_products" in tools
        assert "get_logistics" in tools
        assert "get_addresses" in tools

    # ── independent requests ───────────────────────────────────

    def test_different_requests_are_independent(self):
        """Data for different request_ids should not interfere."""
        set_current_request_id("req-A")
        self.store.store("search_products", [{"id": 1}])

        set_current_request_id("req-B")
        self.store.store("get_recommendations", [{"id": 2}])

        result_a = self.store.get_and_clear("req-A")
        result_b = self.store.get_and_clear("req-B")

        assert len(result_a) == 1 and result_a[0]["tool"] == "search_products"
        assert len(result_b) == 1 and result_b[0]["tool"] == "get_recommendations"
