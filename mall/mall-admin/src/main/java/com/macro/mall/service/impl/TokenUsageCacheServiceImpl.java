package com.macro.mall.service.impl;

import com.macro.mall.common.service.RedisService;
import com.macro.mall.dto.*;
import com.macro.mall.service.TokenUsageCacheService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Token用量缓存Service实现类
 */
@Service
public class TokenUsageCacheServiceImpl implements TokenUsageCacheService {

    @Autowired
    private RedisService redisService;

    @Value("${redis.database}")
    private String REDIS_DATABASE;

    @Value("${redis.key.tokenUsage}")
    private String REDIS_KEY_TOKEN_USAGE;

    @Value("${redis.expire.tokenUsage}")
    private Long REDIS_EXPIRE;

    // ── 汇总统计 ──

    @Override
    public TokenUsageSummaryResult getSummary() {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_TOKEN_USAGE + ":summary";
        return (TokenUsageSummaryResult) redisService.get(key);
    }

    @Override
    public void setSummary(TokenUsageSummaryResult result) {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_TOKEN_USAGE + ":summary";
        redisService.set(key, result, REDIS_EXPIRE);
    }

    @Override
    public void delSummary() {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_TOKEN_USAGE + ":summary";
        redisService.del(key);
    }

    // ── 折线图 ──

    @SuppressWarnings("unchecked")
    @Override
    public List<TokenUsageChartResult> getChartData(String startDate, String endDate) {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_TOKEN_USAGE + ":chart:" + startDate + ":" + endDate;
        return (List<TokenUsageChartResult>) redisService.get(key);
    }

    @Override
    public void setChartData(String startDate, String endDate, List<TokenUsageChartResult> data) {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_TOKEN_USAGE + ":chart:" + startDate + ":" + endDate;
        redisService.set(key, data, REDIS_EXPIRE);
    }

    // ── 用户排行 ──

    @SuppressWarnings("unchecked")
    @Override
    public List<TokenUsageRankingResult> getUserRanking(Integer limit) {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_TOKEN_USAGE + ":ranking:" + limit;
        return (List<TokenUsageRankingResult>) redisService.get(key);
    }

    @Override
    public void setUserRanking(Integer limit, List<TokenUsageRankingResult> data) {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_TOKEN_USAGE + ":ranking:" + limit;
        redisService.set(key, data, REDIS_EXPIRE);
    }

    // ── 意图分布 ──

    @SuppressWarnings("unchecked")
    @Override
    public List<TokenUsageIntentResult> getIntentDistribution() {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_TOKEN_USAGE + ":intent";
        return (List<TokenUsageIntentResult>) redisService.get(key);
    }

    @Override
    public void setIntentDistribution(List<TokenUsageIntentResult> data) {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_TOKEN_USAGE + ":intent";
        redisService.set(key, data, REDIS_EXPIRE);
    }

    // ── 批量清除 ──

    @Override
    public void delAll() {
        delSummary();
        // 其他 key 含参数，依赖 TTL 自动过期
    }
}
