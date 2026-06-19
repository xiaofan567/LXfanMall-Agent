package com.macro.mall.dto;

import io.swagger.annotations.ApiModelProperty;
import lombok.Getter;
import lombok.Setter;

/**
 * Token用量上报参数
 */
@Getter
@Setter
public class TokenUsageReportParam {

    @ApiModelProperty("用户名")
    private String username;

    @ApiModelProperty("会话ID")
    private String sessionId;

    @ApiModelProperty("意图分类")
    private String intent;

    @ApiModelProperty("模型名称")
    private String model;

    @ApiModelProperty("输入Token数")
    private Integer promptTokens;

    @ApiModelProperty("输出Token数")
    private Integer completionTokens;

    @ApiModelProperty("总Token数")
    private Integer totalTokens;

    @ApiModelProperty("工具调用次数")
    private Integer toolCalls;

    @ApiModelProperty("请求耗时(毫秒)")
    private Integer latencyMs;
}
