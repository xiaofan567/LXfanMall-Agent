package com.macro.mall.service;

import com.macro.mall.common.api.CommonPage;
import com.macro.mall.dto.*;

import java.util.List;

/**
 * Token用量统计Service
 */
public interface TokenUsageService {

    /**
     * 上报Token用量记录
     */
    void report(String username, String sessionId, String intent, String model,
                Integer promptTokens, Integer completionTokens, Integer totalTokens,
                Integer toolCalls, Integer latencyMs);

    /**
     * 获取汇总统计
     */
    TokenUsageSummaryResult getSummary();

    /**
     * 获取折线图数据
     */
    List<TokenUsageChartResult> getChartData(String startDate, String endDate);

    /**
     * 获取用户排行 Top N
     */
    List<TokenUsageRankingResult> getUserRanking(Integer limit);

    /**
     * 获取意图分布
     */
    List<TokenUsageIntentResult> getIntentDistribution();

    /**
     * 分页查询明细
     */
    CommonPage<TokenUsageDetailResult> getList(String username, String intent,
                                                String startDate, String endDate,
                                                Integer pageNum, Integer pageSize);
}
