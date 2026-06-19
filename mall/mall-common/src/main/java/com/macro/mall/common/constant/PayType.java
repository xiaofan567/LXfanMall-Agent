package com.macro.mall.common.constant;

/**
 * 支付方式枚举
 */
public enum PayType {

    /** 未支付 */
    UNPAID(0, "未支付"),
    /** 支付宝 */
    ALIPAY(1, "支付宝"),
    /** 微信 */
    WECHAT(2, "微信");

    private final int value;
    private final String description;

    PayType(int value, String description) {
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
