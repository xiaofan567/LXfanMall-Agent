package com.macro.mall.common.constant;

/**
 * 订单类型枚举
 */
public enum OrderType {

    /** 正常订单 */
    NORMAL(0, "正常订单"),
    /** 秒杀订单 */
    FLASH_SALE(1, "秒杀订单");

    private final int value;
    private final String description;

    OrderType(int value, String description) {
        this.value = value;
        this.description = description;
    }

    public int getValue() {
        return value;
    }

    public String getDescription() {
        return description;
    }
}
