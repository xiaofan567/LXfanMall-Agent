package com.macro.mall.service.impl;

import com.macro.mall.common.service.RedisService;
import com.macro.mall.dto.HomeChartResult;
import com.macro.mall.dto.HomeMemberOverview;
import com.macro.mall.dto.HomeProductOverview;
import com.macro.mall.dto.HomeSummaryResult;
import com.macro.mall.service.HomeCacheService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 首页统计缓存Service实现类
 *
 * 类名匹配 *CacheService 切点，自动被 RedisCacheAspect 拦截，
 * Redis 故障时静默降级，不影响正常业务。
 */
@Service
public class HomeCacheServiceImpl implements HomeCacheService {

    @Autowired
    private RedisService redisService;

    @Value("${redis.database}")
    private String REDIS_DATABASE;

    @Value("${redis.key.home}")
    private String REDIS_KEY_HOME;

    @Value("${redis.expire.home}")
    private Long REDIS_EXPIRE;

    // ── 汇总统计 ──

    @Override
    public HomeSummaryResult getSummary() {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_HOME + ":summary";
        return (HomeSummaryResult) redisService.get(key);
    }

    @Override
    public void setSummary(HomeSummaryResult result) {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_HOME + ":summary";
        redisService.set(key, result, REDIS_EXPIRE);
    }

    @Override
    public void delSummary() {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_HOME + ":summary";
        redisService.del(key);
    }

    // ── 折线图 ──

    @SuppressWarnings("unchecked")
    @Override
    public List<HomeChartResult> getChartData(String startDate, String endDate) {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_HOME + ":chart:" + startDate + ":" + endDate;
        return (List<HomeChartResult>) redisService.get(key);
    }

    @Override
    public void setChartData(String startDate, String endDate, List<HomeChartResult> data) {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_HOME + ":chart:" + startDate + ":" + endDate;
        redisService.set(key, data, REDIS_EXPIRE);
    }

    @Override
    public void delChartData() {
        // 折线图 key 包含日期参数，无法穷举删除
        // 依赖 TTL 自动过期，或在 delAll() 中按已知 key 删除
    }

    // ── 商品总览 ──

    @Override
    public HomeProductOverview getProductOverview() {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_HOME + ":productOverview";
        return (HomeProductOverview) redisService.get(key);
    }

    @Override
    public void setProductOverview(HomeProductOverview data) {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_HOME + ":productOverview";
        redisService.set(key, data, REDIS_EXPIRE);
    }

    @Override
    public void delProductOverview() {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_HOME + ":productOverview";
        redisService.del(key);
    }

    // ── 用户总览 ──

    @Override
    public HomeMemberOverview getMemberOverview() {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_HOME + ":memberOverview";
        return (HomeMemberOverview) redisService.get(key);
    }

    @Override
    public void setMemberOverview(HomeMemberOverview data) {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_HOME + ":memberOverview";
        redisService.set(key, data, REDIS_EXPIRE);
    }

    @Override
    public void delMemberOverview() {
        String key = REDIS_DATABASE + ":" + REDIS_KEY_HOME + ":memberOverview";
        redisService.del(key);
    }

    // ── 批量清除 ──

    @Override
    public void delAll() {
        delSummary();
        delProductOverview();
        delMemberOverview();
        // 折线图缓存按 TTL 自动过期
    }
}
