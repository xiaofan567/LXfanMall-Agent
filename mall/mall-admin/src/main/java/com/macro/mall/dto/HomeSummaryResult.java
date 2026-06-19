package com.macro.mall.dto;

import io.swagger.annotations.ApiModelProperty;
import lombok.Getter;
import lombok.Setter;

import java.math.BigDecimal;

/**
 * 首页汇总统计结果
 */
@Getter
@Setter
public class HomeSummaryResult {

    // ── 今日统计卡片 ──
    @ApiModelProperty("今日订单总数")
    private Long todayOrderCount;

    @ApiModelProperty("今日销售总额")
    private BigDecimal todaySales;

    @ApiModelProperty("昨日销售总额")
    private BigDecimal yesterdaySales;

    // ── 待处理事务 ──
    @ApiModelProperty("待付款订单数")
    private Long pendingPaymentCount;

    @ApiModelProperty("已完成订单数")
    private Long completedOrderCount;

    @ApiModelProperty("待确认收货订单数")
    private Long deliveredOrderCount;

    @ApiModelProperty("待发货订单数")
    private Long pendingShipmentCount;

    @ApiModelProperty("已发货订单数")
    private Long shippedOrderCount;

    @ApiModelProperty("待处理退款申请数")
    private Long pendingRefundCount;

    @ApiModelProperty("待处理退货订单数")
    private Long pendingReturnCount;

    @ApiModelProperty("广告位即将到期数")
    private Long adExpiringCount;

    // ── 订单统计侧栏 ──
    @ApiModelProperty("本月订单总数")
    private Long monthlyOrderCount;

    @ApiModelProperty("本周订单总数")
    private Long weeklyOrderCount;

    @ApiModelProperty("本月销售总额")
    private BigDecimal monthlySales;

    @ApiModelProperty("本周销售总额")
    private BigDecimal weeklySales;

    @ApiModelProperty("本月订单同比百分比 (如 +10.5)")
    private String monthlyOrderGrowth;

    @ApiModelProperty("本周订单同比百分比")
    private String weeklyOrderGrowth;

    @ApiModelProperty("本月销售同比百分比")
    private String monthlySalesGrowth;

    @ApiModelProperty("本周销售同比百分比")
    private String weeklySalesGrowth;

    // ── 上期数据（仅用于内部计算同比，不返回前端） ──
    @ApiModelProperty(hidden = true)
    private Long lastMonthOrderCount;

    @ApiModelProperty(hidden = true)
    private Long lastWeekOrderCount;

    @ApiModelProperty(hidden = true)
    private BigDecimal lastMonthSales;

    @ApiModelProperty(hidden = true)
    private BigDecimal lastWeekSales;
}
