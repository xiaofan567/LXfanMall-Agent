package com.macro.mall.common.constant;

/**
 * 优惠券使用状态枚举
 */
public enum CouponUseStatus {

    /** 未使用 */
    UNUSED(0, "未使用"),
    /** 已使用 */
    USED(1, "已使用");

    private final int value;
    private final String description;

    CouponUseStatus(int value, String description) {
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
