package com.macro.mall.common.constant;

/**
 * 订单状态枚举
 *
 * 状态流转：0(待付款) → 1(待发货) → 2(已发货) → 7(已送达) → 3(已完成)
 *          0(待付款) → 4(已关闭/取消)
 */
public enum OrderStatus {

    /** 待付款 */
    PENDING_PAYMENT(0, "待付款"),
    /** 待发货（已付款） */
    PENDING_DELIVERY(1, "待发货"),
    /** 已发货 */
    SHIPPED(2, "已发货"),
    /** 已完成 */
    COMPLETED(3, "已完成"),
    /** 已关闭（超时取消/用户取消/管理员关闭） */
    CLOSED(4, "已关闭"),
    /** 无效订单 */
    INVALID(5, "无效订单"),
    /** 已送达（用户端，物流签收后） */
    DELIVERED(7, "已送达");

    private final int value;
    private final String description;

    OrderStatus(int value, String description) {
        this.value = value;
        this.description = description;
    }

    public int getValue() {
        return value;
    }

    public String getDescription() {
        return description;
    }

    /**
     * 根据值获取枚举
     */
    public static OrderStatus fromValue(int value) {
        for (OrderStatus status : values()) {
            if (status.value == value) {
                return status;
            }
        }
        throw new IllegalArgumentException("未知的订单状态值: " + value);
    }
}
