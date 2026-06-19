package com.macro.mall.dto;

import io.swagger.annotations.ApiModelProperty;
import lombok.Getter;
import lombok.Setter;

/**
 * Token用量折线图数据项
 */
@Getter
@Setter
public class TokenUsageChartResult {

    @ApiModelProperty("日期 (yyyy-MM-dd)")
    private String date;

    @ApiModelProperty("Token消耗总量")
    private Long totalTokens;

    @ApiModelProperty("请求次数")
    private Long requestCount;
}
