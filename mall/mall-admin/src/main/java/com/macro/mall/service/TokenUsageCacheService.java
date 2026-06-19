package com.macro.mall.service;

import com.macro.mall.dto.*;

import java.util.List;

/**
 * Token用量缓存Service
 */
public interface TokenUsageCacheService {

    /** 获取缓存的汇总统计 */
    TokenUsageSummaryResult getSummary();

    /** 缓存汇总统计 */
    void setSummary(TokenUsageSummaryResult result);

    /** 删除汇总统计缓存 */
    void delSummary();

    /** 获取缓存的折线图数据 */
    List<TokenUsageChartResult> getChartData(String startDate, String endDate);

    /** 缓存折线图数据 */
    void setChartData(String startDate, String endDate, List<TokenUsageChartResult> data);

    /** 获取缓存的用户排行 */
    List<TokenUsageRankingResult> getUserRanking(Integer limit);

    /** 缓存用户排行 */
    void setUserRanking(Integer limit, List<TokenUsageRankingResult> data);

    /** 获取缓存的意图分布 */
    List<TokenUsageIntentResult> getIntentDistribution();

    /** 缓存意图分布 */
    void setIntentDistribution(List<TokenUsageIntentResult> data);

    /** 清除所有Token用量缓存 */
    void delAll();
}
