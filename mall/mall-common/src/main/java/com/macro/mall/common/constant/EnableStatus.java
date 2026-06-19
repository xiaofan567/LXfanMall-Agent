package com.macro.mall.common.constant;

/**
 * 通用启用/禁用状态枚举
 * 适用于：管理员状态、会员状态、优惠券会话状态等
 */
public enum EnableStatus {

    /** 禁用 */
    DISABLED(0, "禁用"),
    /** 启用 */
    ENABLED(1, "启用");

    private final int value;
    private final String description;

    EnableStatus(int value, String description) {
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
