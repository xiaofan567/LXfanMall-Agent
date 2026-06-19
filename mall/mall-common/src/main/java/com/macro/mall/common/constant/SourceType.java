package com.macro.mall.common.constant;

/**
 * 订单来源类型枚举
 */
public enum SourceType {

    /** PC订单 */
    PC(0, "PC订单"),
    /** APP订单 */
    APP(1, "APP订单");

    private final int value;
    private final String description;

    SourceType(int value, String description) {
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
