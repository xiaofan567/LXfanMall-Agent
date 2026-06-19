package com.macro.mall.dao;

import com.macro.mall.dto.*;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * Token用量统计Dao
 */
public interface TokenUsageDao {

    /**
     * 插入一条Token用量记录
     */
    int insert(@Param("username") String username,
               @Param("sessionId") String sessionId,
               @Param("intent") String intent,
               @Param("model") String model,
               @Param("promptTokens") Integer promptTokens,
               @Param("completionTokens") Integer completionTokens,
               @Param("totalTokens") Integer totalTokens,
               @Param("toolCalls") Integer toolCalls,
               @Param("latencyMs") Integer latencyMs);

    /**
     * 获取汇总统计
     */
    TokenUsageSummaryResult getSummary();

    /**
     * 获取折线图数据
     */
    List<TokenUsageChartResult> getChartData(@Param("startDate") String startDate,
                                              @Param("endDate") String endDate);

    /**
     * 获取用户排行
     */
    List<TokenUsageRankingResult> getUserRanking(@Param("limit") Integer limit);

    /**
     * 获取意图分布
     */
    List<TokenUsageIntentResult> getIntentDistribution();

    /**
     * 分页查询明细（分页由 PageHelper 接管）
     */
    List<TokenUsageDetailResult> getList(@Param("username") String username,
                                          @Param("intent") String intent,
                                          @Param("startDate") String startDate,
                                          @Param("endDate") String endDate);

    /**
     * 查询明细总数
     */
    Long getListCount(@Param("username") String username,
                      @Param("intent") String intent,
                      @Param("startDate") String startDate,
                      @Param("endDate") String endDate);
}
