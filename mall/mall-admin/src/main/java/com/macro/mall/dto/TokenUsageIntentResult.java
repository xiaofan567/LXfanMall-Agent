package com.macro.mall.dto;

import io.swagger.annotations.ApiModelProperty;
import lombok.Getter;
import lombok.Setter;

/**
 * Token用量意图分布
 */
@Getter
@Setter
public class TokenUsageIntentResult {

    @ApiModelProperty("意图类型")
    private String intent;

    @ApiModelProperty("Token消耗总量")
    private Long totalTokens;

    @ApiModelProperty("请求次数")
    private Long requestCount;
}
