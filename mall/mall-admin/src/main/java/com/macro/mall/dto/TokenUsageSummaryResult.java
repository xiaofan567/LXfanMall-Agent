package com.macro.mall.dto;

import io.swagger.annotations.ApiModelProperty;
import lombok.Getter;
import lombok.Setter;

import java.math.BigDecimal;

/**
 * Token用量汇总统计结果
 */
@Getter
@Setter
public class TokenUsageSummaryResult {

    @ApiModelProperty("今日Token总消耗")
    private Long todayTotalTokens;

    @ApiModelProperty("今日请求次数")
    private Long todayRequestCount;

    @ApiModelProperty("今日平均每次请求Token数")
    private Long todayAvgTokens;

    @ApiModelProperty("本周Token总消耗")
    private Long weeklyTotalTokens;

    @ApiModelProperty("本周请求次数")
    private Long weeklyRequestCount;

    @ApiModelProperty("本月Token总消耗")
    private Long monthlyTotalTokens;

    @ApiModelProperty("本月请求次数")
    private Long monthlyRequestCount;

    @ApiModelProperty("本月活跃用户数")
    private Long monthlyActiveUsers;

    @ApiModelProperty("总Token消耗")
    private Long totalTokens;

    @ApiModelProperty("总请求次数")
    private Long totalRequestCount;

    @ApiModelProperty("总用户数")
    private Long totalUsers;
}
