package com.macro.mall.dto;

import io.swagger.annotations.ApiModelProperty;
import lombok.Getter;
import lombok.Setter;

/**
 * Token用量用户排行
 */
@Getter
@Setter
public class TokenUsageRankingResult {

    @ApiModelProperty("用户名")
    private String username;

    @ApiModelProperty("Token总消耗")
    private Long totalTokens;

    @ApiModelProperty("请求次数")
    private Long requestCount;
}
