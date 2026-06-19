package com.macro.mall.service.impl;

import com.github.pagehelper.PageHelper;
import com.macro.mall.common.api.CommonPage;
import com.macro.mall.dao.TokenUsageDao;
import com.macro.mall.dto.*;
import com.macro.mall.service.TokenUsageCacheService;
import com.macro.mall.service.TokenUsageService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Token用量统计Service实现类
 */
@Service
public class TokenUsageServiceImpl implements TokenUsageService {

    private static final Logger logger = LoggerFactory.getLogger(TokenUsageServiceImpl.class);

    @Autowired
    private TokenUsageDao tokenUsageDao;

    @Autowired
    private TokenUsageCacheService tokenUsageCacheService;

    @Override
    public void report(String username, String sessionId, String intent, String model,
                       Integer promptTokens, Integer completionTokens, Integer totalTokens,
                       Integer toolCalls, Integer latencyMs) {
        tokenUsageDao.insert(username, sessionId, intent, model, promptTokens, completionTokens, totalTokens, toolCalls, latencyMs);
        // 上报后清除汇总缓存，下次查询时重新计算
        tokenUsageCacheService.delAll();
        logger.info("Token usage recorded | user=%s tokens=%d intent=%s", username, totalTokens, intent);
    }

    @Override
    public TokenUsageSummaryResult getSummary() {
        // 1. 先查缓存
        TokenUsageSummaryResult cached = tokenUsageCacheService.getSummary();
        if (cached != null) {
            logger.debug("Token用量汇总命中缓存");
            return cached;
        }

        // 2. 缓存未命中，查数据库
        logger.debug("Token用量汇总未命中缓存，查询数据库");
        TokenUsageSummaryResult result = tokenUsageDao.getSummary();
        if (result == null) {
            result = new TokenUsageSummaryResult();
        }

        // 计算今日平均每次请求Token数
        if (result.getTodayRequestCount() != null && result.getTodayRequestCount() > 0) {
            result.setTodayAvgTokens(result.getTodayTotalTokens() / result.getTodayRequestCount());
        } else {
            result.setTodayAvgTokens(0L);
        }

        // 3. 写入缓存
        tokenUsageCacheService.setSummary(result);
        return result;
    }

    @Override
    public List<TokenUsageChartResult> getChartData(String startDate, String endDate) {
        // 1. 先查缓存
        List<TokenUsageChartResult> cached = tokenUsageCacheService.getChartData(startDate, endDate);
        if (cached != null) {
            logger.debug("Token用量折线图命中缓存: {} ~ {}", startDate, endDate);
            return cached;
        }

        // 2. 缓存未命中，查数据库
        logger.debug("Token用量折线图未命中缓存，查询数据库: {} ~ {}", startDate, endDate);
        List<TokenUsageChartResult> data = tokenUsageDao.getChartData(startDate, endDate);

        // 3. 写入缓存
        tokenUsageCacheService.setChartData(startDate, endDate, data);
        return data;
    }

    @Override
    public List<TokenUsageRankingResult> getUserRanking(Integer limit) {
        // 1. 先查缓存
        List<TokenUsageRankingResult> cached = tokenUsageCacheService.getUserRanking(limit);
        if (cached != null) {
            logger.debug("Token用量用户排行命中缓存");
            return cached;
        }

        // 2. 缓存未命中，查数据库
        logger.debug("Token用量用户排行未命中缓存，查询数据库");
        List<TokenUsageRankingResult> data = tokenUsageDao.getUserRanking(limit);

        // 3. 写入缓存
        tokenUsageCacheService.setUserRanking(limit, data);
        return data;
    }

    @Override
    public List<TokenUsageIntentResult> getIntentDistribution() {
        // 1. 先查缓存
        List<TokenUsageIntentResult> cached = tokenUsageCacheService.getIntentDistribution();
        if (cached != null) {
            logger.debug("Token用量意图分布命中缓存");
            return cached;
        }

        // 2. 缓存未命中，查数据库
        logger.debug("Token用量意图分布未命中缓存，查询数据库");
        List<TokenUsageIntentResult> data = tokenUsageDao.getIntentDistribution();

        // 3. 写入缓存
        tokenUsageCacheService.setIntentDistribution(data);
        return data;
    }

    @Override
    public CommonPage<TokenUsageDetailResult> getList(String username, String intent,
                                                       String startDate, String endDate,
                                                       Integer pageNum, Integer pageSize) {
        PageHelper.startPage(pageNum, pageSize);
        List<TokenUsageDetailResult> list = tokenUsageDao.getList(username, intent, startDate, endDate);
        return CommonPage.restPage(list);
    }
}
