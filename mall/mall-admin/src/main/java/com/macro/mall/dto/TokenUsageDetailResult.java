package com.macro.mall.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.macro.mall.model.UmsTokenUsage;
import lombok.Getter;
import lombok.Setter;

import java.util.Date;

/**
 * Token用量明细记录（继承实体类，扩展格式化注解）
 */
@Getter
@Setter
public class TokenUsageDetailResult extends UmsTokenUsage {

    @Override
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "Asia/Shanghai")
    public Date getCreateTime() {
        return super.getCreateTime();
    }
}
