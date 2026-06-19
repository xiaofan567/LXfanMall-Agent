package com.macro.mall.common.constant;

/**
 * 删除状态枚举
 * 逻辑删除标志：0=未删除，1=已删除
 */
public enum DeleteStatus {

    /** 未删除 */
    NOT_DELETED(0),
    /** 已删除（逻辑删除） */
    DELETED(1);

    private final int value;

    DeleteStatus(int value) {
        this.value = value;
    }

    public int getValue() {
        return value;
    }
}
