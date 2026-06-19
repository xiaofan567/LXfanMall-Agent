package com.macro.mall.portal.service.impl;

import com.aliyun.auth.credentials.Credential;
import com.aliyun.auth.credentials.provider.StaticCredentialProvider;
import com.aliyun.sdk.service.dypnsapi20170525.AsyncClient;
import com.aliyun.sdk.service.dypnsapi20170525.models.CheckSmsVerifyCodeRequest;
import com.aliyun.sdk.service.dypnsapi20170525.models.CheckSmsVerifyCodeResponse;
import com.aliyun.sdk.service.dypnsapi20170525.models.SendSmsVerifyCodeRequest;
import com.aliyun.sdk.service.dypnsapi20170525.models.SendSmsVerifyCodeResponse;
import darabonba.core.client.ClientOverrideConfiguration;
import com.macro.mall.common.exception.Asserts;
import com.macro.mall.portal.service.SmsService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;

/**
 * 阿里云短信认证服务实现（号码认证服务）
 *
 * 使用 dypnsapi SDK，由阿里云管理验证码的生成、存储和校验。
 * 通过 aliyun.sms.enabled 开关控制：
 * - false（dev 模式）：仅打印日志，不调用真实 API
 * - true（prod 模式）：调用阿里云短信认证 API
 */
@Service
public class AliyunSmsServiceImpl implements SmsService {

    private static final Logger LOGGER = LoggerFactory.getLogger(AliyunSmsServiceImpl.class);

    @Value("${aliyun.sms.enabled}")
    private boolean enabled;

    @Value("${aliyun.sms.access-key-id}")
    private String accessKeyId;

    @Value("${aliyun.sms.access-key-secret}")
    private String accessKeySecret;

    @Value("${aliyun.sms.sign-name}")
    private String signName;

    @Value("${aliyun.sms.template-code}")
    private String templateCode;

    private AsyncClient client;

    @PostConstruct
    public void init() {
        if (!enabled) {
            LOGGER.info("短信认证服务处于 dev 模式，不初始化阿里云客户端");
            return;
        }
        try {
            LOGGER.info("短信认证配置 | enabled={} | AK={}*** | signName={} | templateCode={}",
                    enabled,
                    accessKeyId != null && accessKeyId.length() > 4 ? accessKeyId.substring(0, 4) : "null",
                    signName, templateCode);

            Credential credential = Credential.builder()
                    .accessKeyId(accessKeyId)
                    .accessKeySecret(accessKeySecret)
                    .build();

            StaticCredentialProvider credentialProvider = StaticCredentialProvider.create(credential);

            ClientOverrideConfiguration overrideConfig = ClientOverrideConfiguration.create()
                    .setEndpointOverride("dypnsapi.aliyuncs.com");

            this.client = AsyncClient.builder()
                    .credentialsProvider(credentialProvider)
                    .overrideConfiguration(overrideConfig)
                    .build();

            LOGGER.info("阿里云短信认证服务客户端初始化成功");
        } catch (Exception e) {
            LOGGER.error("阿里云短信认证服务客户端初始化失败", e);
        }
    }

    @PreDestroy
    public void destroy() {
        if (client != null) {
            try {
                client.close();
            } catch (Exception e) {
                LOGGER.warn("关闭短信认证客户端异常", e);
            }
        }
    }

    /**
     * 发送短信验证码（短信认证服务）
     * 阿里云自动生成验证码并发送，无需调用方传入 code
     */
    @Override
    public void sendSmsCode(String telephone, String code) {
        if (!enabled) {
            LOGGER.info("【dev】短信认证服务：模拟发送验证码 -> 手机号 {}，验证码 {}", telephone, code);
            return;
        }

        if (client == null) {
            LOGGER.error("短信认证客户端未初始化，无法发送短信");
            Asserts.fail("短信服务暂时不可用，请稍后重试");
        }

        try {
            SendSmsVerifyCodeRequest request = SendSmsVerifyCodeRequest.builder()
                    .phoneNumber(telephone)
                    .signName(signName)
                    .templateCode(templateCode)
                    .templateParam("{\"code\":\"" + code + "\",\"min\":\"5\"}")
                    .codeType(1L)           // 1=数字验证码
                    .validTime(5L)          // 验证码有效期5分钟
                    .interval(60L)          // 发送间隔60秒
                    .build();

            SendSmsVerifyCodeResponse response = client.sendSmsVerifyCode(request).join();

            if (!"OK".equalsIgnoreCase(response.getBody().getCode())) {
                LOGGER.error("短信发送失败 | phone={} | code={} | message={}",
                        telephone, response.getBody().getCode(), response.getBody().getMessage());
                Asserts.fail("短信发送失败，请稍后重试");
            }

            LOGGER.info("短信认证服务：验证码发送成功 | phone={}", telephone);
        } catch (Exception e) {
            LOGGER.error("短信发送异常 | phone={}", telephone, e);
            Asserts.fail("短信发送失败，请稍后重试");
        }
    }

    /**
     * 校验短信验证码（短信认证服务）
     * 由阿里云端校验验证码是否正确
     */
    @Override
    public boolean verifySmsCode(String telephone, String code) {
        if (!enabled) {
            LOGGER.info("【dev】短信认证服务：模拟校验验证码 -> 手机号 {}，验证码 {}", telephone, code);
            return true; // dev 模式直接通过
        }

        if (client == null) {
            LOGGER.error("短信认证客户端未初始化，无法校验验证码");
            return false;
        }

        try {
            CheckSmsVerifyCodeRequest request = CheckSmsVerifyCodeRequest.builder()
                    .phoneNumber(telephone)
                    .verifyCode(code)
                    .countryCode("cn")
                    .build();

            CheckSmsVerifyCodeResponse response = client.checkSmsVerifyCode(request).join();

            if ("OK".equalsIgnoreCase(response.getBody().getCode())) {
                LOGGER.info("短信认证服务：验证码校验通过 | phone={}", telephone);
                return true;
            }

            LOGGER.warn("短信认证服务：验证码校验失败 | phone={} | code={} | message={}",
                    telephone, response.getBody().getCode(), response.getBody().getMessage());
            return false;
        } catch (Exception e) {
            LOGGER.error("验证码校验异常 | phone={}", telephone, e);
            return false;
        }
    }

    /*
     * ==================== 旧版实现（自行生成验证码模式，已弃用） ====================
     * 以下代码使用 dysmsapi SDK，需要自行生成验证码并通过 Redis 管理。
     * 保留仅供参考，当前已切换为短信认证服务（dypnsapi SDK）。
     *
     * @Override
     * public void sendSmsCode(String telephone, String code) {
     *     if (!enabled) {
     *         LOGGER.info("【dev】验证码 [{}] -> 手机号 {}", code, telephone);
     *         return;
     *     }
     *     try {
     *         SendSmsRequest request = new SendSmsRequest()
     *                 .setPhoneNumbers(telephone)
     *                 .setSignName(signName)
     *                 .setTemplateCode(templateCode)
     *                 .setTemplateParam("{\"code\":\"" + code + "\"}");
     *         SendSmsResponse response = client.sendSms(request);
     *         if (!"OK".equalsIgnoreCase(response.getBody().getCode())) {
     *             Asserts.fail("短信发送失败，请稍后重试");
     *         }
     *     } catch (Exception e) {
     *         Asserts.fail("短信发送失败，请稍后重试");
     *     }
     * }
     */
}
