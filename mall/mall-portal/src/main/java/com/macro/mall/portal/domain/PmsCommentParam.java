package com.macro.mall.portal.domain;

import io.swagger.annotations.ApiModelProperty;

/**
 * 商品评价创建参数
 */
public class PmsCommentParam {

    @ApiModelProperty("订单ID")
    private Long orderId;

    @ApiModelProperty("订单项ID")
    private Long orderItemId;

    @ApiModelProperty("商品ID")
    private Long productId;

    @ApiModelProperty(value = "评价星数：0->5")
    private Integer star;

    @ApiModelProperty("评价内容")
    private String content;

    @ApiModelProperty("上传图片地址，以逗号隔开")
    private String pics;

    @ApiModelProperty("购买时的商品属性")
    private String productAttribute;

    public Long getOrderId() {
        return orderId;
    }

    public void setOrderId(Long orderId) {
        this.orderId = orderId;
    }

    public Long getOrderItemId() {
        return orderItemId;
    }

    public void setOrderItemId(Long orderItemId) {
        this.orderItemId = orderItemId;
    }

    public Long getProductId() {
        return productId;
    }

    public void setProductId(Long productId) {
        this.productId = productId;
    }

    public Integer getStar() {
        return star;
    }

    public void setStar(Integer star) {
        this.star = star;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public String getPics() {
        return pics;
    }

    public void setPics(String pics) {
        this.pics = pics;
    }

    public String getProductAttribute() {
        return productAttribute;
    }

    public void setProductAttribute(String productAttribute) {
        this.productAttribute = productAttribute;
    }
}
