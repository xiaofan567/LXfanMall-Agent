package com.macro.mall.model;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

public class UmsTokenUsageExample {
    protected String orderByClause;

    protected boolean distinct;

    protected List<Criteria> oredCriteria;

    public UmsTokenUsageExample() {
        oredCriteria = new ArrayList<>();
    }

    public void setOrderByClause(String orderByClause) {
        this.orderByClause = orderByClause;
    }

    public String getOrderByClause() {
        return orderByClause;
    }

    public void setDistinct(boolean distinct) {
        this.distinct = distinct;
    }

    public boolean isDistinct() {
        return distinct;
    }

    public List<Criteria> getOredCriteria() {
        return oredCriteria;
    }

    public void or(Criteria criteria) {
        oredCriteria.add(criteria);
    }

    public Criteria or() {
        Criteria criteria = createCriteriaInternal();
        oredCriteria.add(criteria);
        return criteria;
    }

    public Criteria createCriteria() {
        Criteria criteria = createCriteriaInternal();
        if (oredCriteria.size() == 0) {
            oredCriteria.add(criteria);
        }
        return criteria;
    }

    protected Criteria createCriteriaInternal() {
        Criteria criteria = new Criteria();
        return criteria;
    }

    public void clear() {
        oredCriteria.clear();
        orderByClause = null;
        distinct = false;
    }

    protected abstract static class GeneratedCriteria {
        protected List<Criterion> criteria;

        protected GeneratedCriteria() {
            super();
            criteria = new ArrayList<>();
        }

        public boolean isValid() {
            return criteria.size() > 0;
        }

        public List<Criterion> getAllCriteria() {
            return criteria;
        }

        public List<Criterion> getCriteria() {
            return criteria;
        }

        protected void addCriterion(String condition) {
            if (condition == null) {
                throw new RuntimeException("Value for condition cannot be null");
            }
            criteria.add(new Criterion(condition));
        }

        protected void addCriterion(String condition, Object value, String property) {
            if (value == null) {
                throw new RuntimeException("Value for " + property + " cannot be null");
            }
            criteria.add(new Criterion(condition, value));
        }

        protected void addCriterion(String condition, Object value1, Object value2, String property) {
            if (value1 == null || value2 == null) {
                throw new RuntimeException("Between values for " + property + " cannot be null");
            }
            criteria.add(new Criterion(condition, value1, value2));
        }

        public Criteria andIdIsNull() {
            addCriterion("id is null");
            return (Criteria) this;
        }

        public Criteria andIdIsNotNull() {
            addCriterion("id is not null");
            return (Criteria) this;
        }

        public Criteria andIdEqualTo(Long value) {
            addCriterion("id =", value, "id");
            return (Criteria) this;
        }

        public Criteria andIdNotEqualTo(Long value) {
            addCriterion("id <>", value, "id");
            return (Criteria) this;
        }

        public Criteria andIdGreaterThan(Long value) {
            addCriterion("id >", value, "id");
            return (Criteria) this;
        }

        public Criteria andIdGreaterThanOrEqualTo(Long value) {
            addCriterion("id >=", value, "id");
            return (Criteria) this;
        }

        public Criteria andIdLessThan(Long value) {
            addCriterion("id <", value, "id");
            return (Criteria) this;
        }

        public Criteria andIdLessThanOrEqualTo(Long value) {
            addCriterion("id <=", value, "id");
            return (Criteria) this;
        }

        public Criteria andIdIn(List<Long> values) {
            addCriterion("id in", values, "id");
            return (Criteria) this;
        }

        public Criteria andIdNotIn(List<Long> values) {
            addCriterion("id not in", values, "id");
            return (Criteria) this;
        }

        public Criteria andIdBetween(Long value1, Long value2) {
            addCriterion("id between", value1, value2, "id");
            return (Criteria) this;
        }

        public Criteria andIdNotBetween(Long value1, Long value2) {
            addCriterion("id not between", value1, value2, "id");
            return (Criteria) this;
        }

        public Criteria andUsernameIsNull() {
            addCriterion("username is null");
            return (Criteria) this;
        }

        public Criteria andUsernameIsNotNull() {
            addCriterion("username is not null");
            return (Criteria) this;
        }

        public Criteria andUsernameEqualTo(String value) {
            addCriterion("username =", value, "username");
            return (Criteria) this;
        }

        public Criteria andUsernameNotEqualTo(String value) {
            addCriterion("username <>", value, "username");
            return (Criteria) this;
        }

        public Criteria andUsernameGreaterThan(String value) {
            addCriterion("username >", value, "username");
            return (Criteria) this;
        }

        public Criteria andUsernameGreaterThanOrEqualTo(String value) {
            addCriterion("username >=", value, "username");
            return (Criteria) this;
        }

        public Criteria andUsernameLessThan(String value) {
            addCriterion("username <", value, "username");
            return (Criteria) this;
        }

        public Criteria andUsernameLessThanOrEqualTo(String value) {
            addCriterion("username <=", value, "username");
            return (Criteria) this;
        }

        public Criteria andUsernameLike(String value) {
            addCriterion("username like", value, "username");
            return (Criteria) this;
        }

        public Criteria andUsernameNotLike(String value) {
            addCriterion("username not like", value, "username");
            return (Criteria) this;
        }

        public Criteria andUsernameIn(List<String> values) {
            addCriterion("username in", values, "username");
            return (Criteria) this;
        }

        public Criteria andUsernameNotIn(List<String> values) {
            addCriterion("username not in", values, "username");
            return (Criteria) this;
        }

        public Criteria andUsernameBetween(String value1, String value2) {
            addCriterion("username between", value1, value2, "username");
            return (Criteria) this;
        }

        public Criteria andUsernameNotBetween(String value1, String value2) {
            addCriterion("username not between", value1, value2, "username");
            return (Criteria) this;
        }

        public Criteria andSessionIdIsNull() {
            addCriterion("session_id is null");
            return (Criteria) this;
        }

        public Criteria andSessionIdIsNotNull() {
            addCriterion("session_id is not null");
            return (Criteria) this;
        }

        public Criteria andSessionIdEqualTo(String value) {
            addCriterion("session_id =", value, "sessionId");
            return (Criteria) this;
        }

        public Criteria andSessionIdNotEqualTo(String value) {
            addCriterion("session_id <>", value, "sessionId");
            return (Criteria) this;
        }

        public Criteria andSessionIdGreaterThan(String value) {
            addCriterion("session_id >", value, "sessionId");
            return (Criteria) this;
        }

        public Criteria andSessionIdGreaterThanOrEqualTo(String value) {
            addCriterion("session_id >=", value, "sessionId");
            return (Criteria) this;
        }

        public Criteria andSessionIdLessThan(String value) {
            addCriterion("session_id <", value, "sessionId");
            return (Criteria) this;
        }

        public Criteria andSessionIdLessThanOrEqualTo(String value) {
            addCriterion("session_id <=", value, "sessionId");
            return (Criteria) this;
        }

        public Criteria andSessionIdLike(String value) {
            addCriterion("session_id like", value, "sessionId");
            return (Criteria) this;
        }

        public Criteria andSessionIdNotLike(String value) {
            addCriterion("session_id not like", value, "sessionId");
            return (Criteria) this;
        }

        public Criteria andSessionIdIn(List<String> values) {
            addCriterion("session_id in", values, "sessionId");
            return (Criteria) this;
        }

        public Criteria andSessionIdNotIn(List<String> values) {
            addCriterion("session_id not in", values, "sessionId");
            return (Criteria) this;
        }

        public Criteria andSessionIdBetween(String value1, String value2) {
            addCriterion("session_id between", value1, value2, "sessionId");
            return (Criteria) this;
        }

        public Criteria andSessionIdNotBetween(String value1, String value2) {
            addCriterion("session_id not between", value1, value2, "sessionId");
            return (Criteria) this;
        }

        public Criteria andIntentIsNull() {
            addCriterion("intent is null");
            return (Criteria) this;
        }

        public Criteria andIntentIsNotNull() {
            addCriterion("intent is not null");
            return (Criteria) this;
        }

        public Criteria andIntentEqualTo(String value) {
            addCriterion("intent =", value, "intent");
            return (Criteria) this;
        }

        public Criteria andIntentNotEqualTo(String value) {
            addCriterion("intent <>", value, "intent");
            return (Criteria) this;
        }

        public Criteria andIntentGreaterThan(String value) {
            addCriterion("intent >", value, "intent");
            return (Criteria) this;
        }

        public Criteria andIntentGreaterThanOrEqualTo(String value) {
            addCriterion("intent >=", value, "intent");
            return (Criteria) this;
        }

        public Criteria andIntentLessThan(String value) {
            addCriterion("intent <", value, "intent");
            return (Criteria) this;
        }

        public Criteria andIntentLessThanOrEqualTo(String value) {
            addCriterion("intent <=", value, "intent");
            return (Criteria) this;
        }

        public Criteria andIntentLike(String value) {
            addCriterion("intent like", value, "intent");
            return (Criteria) this;
        }

        public Criteria andIntentNotLike(String value) {
            addCriterion("intent not like", value, "intent");
            return (Criteria) this;
        }

        public Criteria andIntentIn(List<String> values) {
            addCriterion("intent in", values, "intent");
            return (Criteria) this;
        }

        public Criteria andIntentNotIn(List<String> values) {
            addCriterion("intent not in", values, "intent");
            return (Criteria) this;
        }

        public Criteria andIntentBetween(String value1, String value2) {
            addCriterion("intent between", value1, value2, "intent");
            return (Criteria) this;
        }

        public Criteria andIntentNotBetween(String value1, String value2) {
            addCriterion("intent not between", value1, value2, "intent");
            return (Criteria) this;
        }

        public Criteria andModelIsNull() {
            addCriterion("model is null");
            return (Criteria) this;
        }

        public Criteria andModelIsNotNull() {
            addCriterion("model is not null");
            return (Criteria) this;
        }

        public Criteria andModelEqualTo(String value) {
            addCriterion("model =", value, "model");
            return (Criteria) this;
        }

        public Criteria andModelNotEqualTo(String value) {
            addCriterion("model <>", value, "model");
            return (Criteria) this;
        }

        public Criteria andModelGreaterThan(String value) {
            addCriterion("model >", value, "model");
            return (Criteria) this;
        }

        public Criteria andModelGreaterThanOrEqualTo(String value) {
            addCriterion("model >=", value, "model");
            return (Criteria) this;
        }

        public Criteria andModelLessThan(String value) {
            addCriterion("model <", value, "model");
            return (Criteria) this;
        }

        public Criteria andModelLessThanOrEqualTo(String value) {
            addCriterion("model <=", value, "model");
            return (Criteria) this;
        }

        public Criteria andModelLike(String value) {
            addCriterion("model like", value, "model");
            return (Criteria) this;
        }

        public Criteria andModelNotLike(String value) {
            addCriterion("model not like", value, "model");
            return (Criteria) this;
        }

        public Criteria andModelIn(List<String> values) {
            addCriterion("model in", values, "model");
            return (Criteria) this;
        }

        public Criteria andModelNotIn(List<String> values) {
            addCriterion("model not in", values, "model");
            return (Criteria) this;
        }

        public Criteria andModelBetween(String value1, String value2) {
            addCriterion("model between", value1, value2, "model");
            return (Criteria) this;
        }

        public Criteria andModelNotBetween(String value1, String value2) {
            addCriterion("model not between", value1, value2, "model");
            return (Criteria) this;
        }

        public Criteria andPromptTokensIsNull() {
            addCriterion("prompt_tokens is null");
            return (Criteria) this;
        }

        public Criteria andPromptTokensIsNotNull() {
            addCriterion("prompt_tokens is not null");
            return (Criteria) this;
        }

        public Criteria andPromptTokensEqualTo(Integer value) {
            addCriterion("prompt_tokens =", value, "promptTokens");
            return (Criteria) this;
        }

        public Criteria andPromptTokensNotEqualTo(Integer value) {
            addCriterion("prompt_tokens <>", value, "promptTokens");
            return (Criteria) this;
        }

        public Criteria andPromptTokensGreaterThan(Integer value) {
            addCriterion("prompt_tokens >", value, "promptTokens");
            return (Criteria) this;
        }

        public Criteria andPromptTokensGreaterThanOrEqualTo(Integer value) {
            addCriterion("prompt_tokens >=", value, "promptTokens");
            return (Criteria) this;
        }

        public Criteria andPromptTokensLessThan(Integer value) {
            addCriterion("prompt_tokens <", value, "promptTokens");
            return (Criteria) this;
        }

        public Criteria andPromptTokensLessThanOrEqualTo(Integer value) {
            addCriterion("prompt_tokens <=", value, "promptTokens");
            return (Criteria) this;
        }

        public Criteria andPromptTokensIn(List<Integer> values) {
            addCriterion("prompt_tokens in", values, "promptTokens");
            return (Criteria) this;
        }

        public Criteria andPromptTokensNotIn(List<Integer> values) {
            addCriterion("prompt_tokens not in", values, "promptTokens");
            return (Criteria) this;
        }

        public Criteria andPromptTokensBetween(Integer value1, Integer value2) {
            addCriterion("prompt_tokens between", value1, value2, "promptTokens");
            return (Criteria) this;
        }

        public Criteria andPromptTokensNotBetween(Integer value1, Integer value2) {
            addCriterion("prompt_tokens not between", value1, value2, "promptTokens");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensIsNull() {
            addCriterion("completion_tokens is null");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensIsNotNull() {
            addCriterion("completion_tokens is not null");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensEqualTo(Integer value) {
            addCriterion("completion_tokens =", value, "completionTokens");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensNotEqualTo(Integer value) {
            addCriterion("completion_tokens <>", value, "completionTokens");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensGreaterThan(Integer value) {
            addCriterion("completion_tokens >", value, "completionTokens");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensGreaterThanOrEqualTo(Integer value) {
            addCriterion("completion_tokens >=", value, "completionTokens");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensLessThan(Integer value) {
            addCriterion("completion_tokens <", value, "completionTokens");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensLessThanOrEqualTo(Integer value) {
            addCriterion("completion_tokens <=", value, "completionTokens");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensIn(List<Integer> values) {
            addCriterion("completion_tokens in", values, "completionTokens");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensNotIn(List<Integer> values) {
            addCriterion("completion_tokens not in", values, "completionTokens");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensBetween(Integer value1, Integer value2) {
            addCriterion("completion_tokens between", value1, value2, "completionTokens");
            return (Criteria) this;
        }

        public Criteria andCompletionTokensNotBetween(Integer value1, Integer value2) {
            addCriterion("completion_tokens not between", value1, value2, "completionTokens");
            return (Criteria) this;
        }

        public Criteria andTotalTokensIsNull() {
            addCriterion("total_tokens is null");
            return (Criteria) this;
        }

        public Criteria andTotalTokensIsNotNull() {
            addCriterion("total_tokens is not null");
            return (Criteria) this;
        }

        public Criteria andTotalTokensEqualTo(Integer value) {
            addCriterion("total_tokens =", value, "totalTokens");
            return (Criteria) this;
        }

        public Criteria andTotalTokensNotEqualTo(Integer value) {
            addCriterion("total_tokens <>", value, "totalTokens");
            return (Criteria) this;
        }

        public Criteria andTotalTokensGreaterThan(Integer value) {
            addCriterion("total_tokens >", value, "totalTokens");
            return (Criteria) this;
        }

        public Criteria andTotalTokensGreaterThanOrEqualTo(Integer value) {
            addCriterion("total_tokens >=", value, "totalTokens");
            return (Criteria) this;
        }

        public Criteria andTotalTokensLessThan(Integer value) {
            addCriterion("total_tokens <", value, "totalTokens");
            return (Criteria) this;
        }

        public Criteria andTotalTokensLessThanOrEqualTo(Integer value) {
            addCriterion("total_tokens <=", value, "totalTokens");
            return (Criteria) this;
        }

        public Criteria andTotalTokensIn(List<Integer> values) {
            addCriterion("total_tokens in", values, "totalTokens");
            return (Criteria) this;
        }

        public Criteria andTotalTokensNotIn(List<Integer> values) {
            addCriterion("total_tokens not in", values, "totalTokens");
            return (Criteria) this;
        }

        public Criteria andTotalTokensBetween(Integer value1, Integer value2) {
            addCriterion("total_tokens between", value1, value2, "totalTokens");
            return (Criteria) this;
        }

        public Criteria andTotalTokensNotBetween(Integer value1, Integer value2) {
            addCriterion("total_tokens not between", value1, value2, "totalTokens");
            return (Criteria) this;
        }

        public Criteria andToolCallsIsNull() {
            addCriterion("tool_calls is null");
            return (Criteria) this;
        }

        public Criteria andToolCallsIsNotNull() {
            addCriterion("tool_calls is not null");
            return (Criteria) this;
        }

        public Criteria andToolCallsEqualTo(Integer value) {
            addCriterion("tool_calls =", value, "toolCalls");
            return (Criteria) this;
        }

        public Criteria andToolCallsNotEqualTo(Integer value) {
            addCriterion("tool_calls <>", value, "toolCalls");
            return (Criteria) this;
        }

        public Criteria andToolCallsGreaterThan(Integer value) {
            addCriterion("tool_calls >", value, "toolCalls");
            return (Criteria) this;
        }

        public Criteria andToolCallsGreaterThanOrEqualTo(Integer value) {
            addCriterion("tool_calls >=", value, "toolCalls");
            return (Criteria) this;
        }

        public Criteria andToolCallsLessThan(Integer value) {
            addCriterion("tool_calls <", value, "toolCalls");
            return (Criteria) this;
        }

        public Criteria andToolCallsLessThanOrEqualTo(Integer value) {
            addCriterion("tool_calls <=", value, "toolCalls");
            return (Criteria) this;
        }

        public Criteria andToolCallsIn(List<Integer> values) {
            addCriterion("tool_calls in", values, "toolCalls");
            return (Criteria) this;
        }

        public Criteria andToolCallsNotIn(List<Integer> values) {
            addCriterion("tool_calls not in", values, "toolCalls");
            return (Criteria) this;
        }

        public Criteria andToolCallsBetween(Integer value1, Integer value2) {
            addCriterion("tool_calls between", value1, value2, "toolCalls");
            return (Criteria) this;
        }

        public Criteria andToolCallsNotBetween(Integer value1, Integer value2) {
            addCriterion("tool_calls not between", value1, value2, "toolCalls");
            return (Criteria) this;
        }

        public Criteria andLatencyMsIsNull() {
            addCriterion("latency_ms is null");
            return (Criteria) this;
        }

        public Criteria andLatencyMsIsNotNull() {
            addCriterion("latency_ms is not null");
            return (Criteria) this;
        }

        public Criteria andLatencyMsEqualTo(Integer value) {
            addCriterion("latency_ms =", value, "latencyMs");
            return (Criteria) this;
        }

        public Criteria andLatencyMsNotEqualTo(Integer value) {
            addCriterion("latency_ms <>", value, "latencyMs");
            return (Criteria) this;
        }

        public Criteria andLatencyMsGreaterThan(Integer value) {
            addCriterion("latency_ms >", value, "latencyMs");
            return (Criteria) this;
        }

        public Criteria andLatencyMsGreaterThanOrEqualTo(Integer value) {
            addCriterion("latency_ms >=", value, "latencyMs");
            return (Criteria) this;
        }

        public Criteria andLatencyMsLessThan(Integer value) {
            addCriterion("latency_ms <", value, "latencyMs");
            return (Criteria) this;
        }

        public Criteria andLatencyMsLessThanOrEqualTo(Integer value) {
            addCriterion("latency_ms <=", value, "latencyMs");
            return (Criteria) this;
        }

        public Criteria andLatencyMsIn(List<Integer> values) {
            addCriterion("latency_ms in", values, "latencyMs");
            return (Criteria) this;
        }

        public Criteria andLatencyMsNotIn(List<Integer> values) {
            addCriterion("latency_ms not in", values, "latencyMs");
            return (Criteria) this;
        }

        public Criteria andLatencyMsBetween(Integer value1, Integer value2) {
            addCriterion("latency_ms between", value1, value2, "latencyMs");
            return (Criteria) this;
        }

        public Criteria andLatencyMsNotBetween(Integer value1, Integer value2) {
            addCriterion("latency_ms not between", value1, value2, "latencyMs");
            return (Criteria) this;
        }

        public Criteria andCreateTimeIsNull() {
            addCriterion("create_time is null");
            return (Criteria) this;
        }

        public Criteria andCreateTimeIsNotNull() {
            addCriterion("create_time is not null");
            return (Criteria) this;
        }

        public Criteria andCreateTimeEqualTo(Date value) {
            addCriterion("create_time =", value, "createTime");
            return (Criteria) this;
        }

        public Criteria andCreateTimeNotEqualTo(Date value) {
            addCriterion("create_time <>", value, "createTime");
            return (Criteria) this;
        }

        public Criteria andCreateTimeGreaterThan(Date value) {
            addCriterion("create_time >", value, "createTime");
            return (Criteria) this;
        }

        public Criteria andCreateTimeGreaterThanOrEqualTo(Date value) {
            addCriterion("create_time >=", value, "createTime");
            return (Criteria) this;
        }

        public Criteria andCreateTimeLessThan(Date value) {
            addCriterion("create_time <", value, "createTime");
            return (Criteria) this;
        }

        public Criteria andCreateTimeLessThanOrEqualTo(Date value) {
            addCriterion("create_time <=", value, "createTime");
            return (Criteria) this;
        }

        public Criteria andCreateTimeIn(List<Date> values) {
            addCriterion("create_time in", values, "createTime");
            return (Criteria) this;
        }

        public Criteria andCreateTimeNotIn(List<Date> values) {
            addCriterion("create_time not in", values, "createTime");
            return (Criteria) this;
        }

        public Criteria andCreateTimeBetween(Date value1, Date value2) {
            addCriterion("create_time between", value1, value2, "createTime");
            return (Criteria) this;
        }

        public Criteria andCreateTimeNotBetween(Date value1, Date value2) {
            addCriterion("create_time not between", value1, value2, "createTime");
            return (Criteria) this;
        }
    }

    public static class Criteria extends GeneratedCriteria {
        protected Criteria() {
            super();
        }
    }

    public static class Criterion {
        private String condition;

        private Object value;

        private Object secondValue;

        private boolean noValue;

        private boolean singleValue;

        private boolean betweenValue;

        private boolean listValue;

        private String typeHandler;

        public String getCondition() {
            return condition;
        }

        public Object getValue() {
            return value;
        }

        public Object getSecondValue() {
            return secondValue;
        }

        public boolean isNoValue() {
            return noValue;
        }

        public boolean isSingleValue() {
            return singleValue;
        }

        public boolean isBetweenValue() {
            return betweenValue;
        }

        public boolean isListValue() {
            return listValue;
        }

        public String getTypeHandler() {
            return typeHandler;
        }

        protected Criterion(String condition) {
            super();
            this.condition = condition;
            this.typeHandler = null;
            this.noValue = true;
        }

        protected Criterion(String condition, Object value, String typeHandler) {
            super();
            this.condition = condition;
            this.value = value;
            this.typeHandler = typeHandler;
            if (value instanceof List<?>) {
                this.listValue = true;
            } else {
                this.singleValue = true;
            }
        }

        protected Criterion(String condition, Object value) {
            this(condition, value, null);
        }

        protected Criterion(String condition, Object value, Object secondValue, String typeHandler) {
            super();
            this.condition = condition;
            this.value = value;
            this.secondValue = secondValue;
            this.typeHandler = typeHandler;
            this.betweenValue = true;
        }

        protected Criterion(String condition, Object value, Object secondValue) {
            this(condition, value, secondValue, null);
        }
    }
}