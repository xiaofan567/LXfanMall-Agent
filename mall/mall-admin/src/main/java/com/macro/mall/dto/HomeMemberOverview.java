package com.macro.mall.dto;

import io.swagger.annotations.ApiModelProperty;
import lombok.Getter;
import lombok.Setter;

/**
 * 首页用户总览
 */
@Getter
@Setter
public class HomeMemberOverview {

    @ApiModelProperty("今日新增会员数")
    private Long todayNewCount;

    @ApiModelProperty("昨日新增会员数")
    private Long yesterdayNewCount;

    @ApiModelProperty("本月新增会员数")
    private Long monthNewCount;

    @ApiModelProperty("会员总数")
    private Long totalCount;
}
