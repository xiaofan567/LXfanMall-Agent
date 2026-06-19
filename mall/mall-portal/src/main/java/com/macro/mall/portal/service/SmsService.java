package com.macro.mall.portal.service;

/**
 * 短信服务接口
 * 解耦具体短信服务商实现，可灵活切换阿里云、腾讯云等
 */
public interface SmsService {

    /**
     * 发送短信验证码
     *
     * @param telephone 手机号
     * @param code      验证码（由调用方生成）
     */
    void sendSmsCode(String telephone, String code);

    /**
     * 校验短信验证码（短信认证服务：由服务商校验）
     *
     * @param telephone 手机号
     * @param code      用户输入的验证码
     * @return true=验证通过，false=验证失败
     */
    boolean verifySmsCode(String telephone, String code);

    /*
     * === 旧版接口（自行生成验证码模式，已弃用，保留参考） ===
     *
     * void sendSmsCode(String telephone, String code);
     *   - 由调用方生成验证码，传入后发送
     *   - 验证码存储和校验由调用方通过 Redis 管理
     */
}
