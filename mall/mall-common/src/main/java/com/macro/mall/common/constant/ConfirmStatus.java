package com.macro.mall.common.constant;

/**
 * 确认收货状态枚举
 */
public enum ConfirmStatus {

    /** 未确认 */
    UNCONFIRMED(0, "未确认"),
    /** 已确认 */
    CONFIRMED(1, "已确认");

    private final int value;
    private final String description;

    ConfirmStatus(int value, String description) {
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
