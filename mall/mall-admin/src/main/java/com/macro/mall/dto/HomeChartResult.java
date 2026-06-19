package com.macro.mall.dto;

import io.swagger.annotations.ApiModelProperty;
import lombok.Getter;
import lombok.Setter;

import java.math.BigDecimal;

/**
 * 首页折线图数据项
 */
@Getter
@Setter
public class HomeChartResult {

    @ApiModelProperty("日期 (yyyy-MM-dd)")
    private String date;

    @ApiModelProperty("订单数量")
    private Long orderCount;

    @ApiModelProperty("订单金额")
    private BigDecimal orderAmount;
}
