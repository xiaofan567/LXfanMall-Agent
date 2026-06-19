package com.macro.mall.portal.domain;

import io.swagger.annotations.ApiModelProperty;
import lombok.Getter;
import lombok.Setter;

import java.util.Date;

/**
 * 物流轨迹结果
 * Created by macro on 2026/5/18.
 */
@Getter
@Setter
public class LogisticsTraceResult {
    @ApiModelProperty("轨迹时间")
    private Date traceTime;
    @ApiModelProperty("轨迹地点")
    private String location;
    @ApiModelProperty("轨迹状态描述")
    private String statusText;
    @ApiModelProperty("轨迹状态编码")
    private Integer statusCode;
}
