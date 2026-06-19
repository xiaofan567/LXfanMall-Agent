package com.macro.mall.dto;

import io.swagger.annotations.ApiModelProperty;
import lombok.Getter;
import lombok.Setter;

/**
 * 首页商品总览
 */
@Getter
@Setter
public class HomeProductOverview {

    @ApiModelProperty("已下架商品数")
    private Long delistedCount;

    @ApiModelProperty("已上架商品数")
    private Long listedCount;

    @ApiModelProperty("库存紧张商品数 (stock < 10)")
    private Long lowStockCount;

    @ApiModelProperty("全部商品数")
    private Long totalCount;
}
