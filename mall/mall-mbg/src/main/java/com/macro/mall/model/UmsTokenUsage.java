package com.macro.mall.model;

import io.swagger.annotations.ApiModelProperty;
import java.io.Serializable;
import java.util.Date;

public class UmsTokenUsage implements Serializable {
    private Long id;

    @ApiModelProperty(value = "用户名")
    private String username;

    @ApiModelProperty(value = "会话ID")
    private String sessionId;

    @ApiModelProperty(value = "意图分类(product_recommend/order_query/chitchat等)")
    private String intent;

    @ApiModelProperty(value = "模型名称(deepseek-v4-flash等)")
    private String model;

    @ApiModelProperty(value = "输入token数")
    private Integer promptTokens;

    @ApiModelProperty(value = "输出token数")
    private Integer completionTokens;

    @ApiModelProperty(value = "总token数")
    private Integer totalTokens;

    @ApiModelProperty(value = "工具调用次数")
    private Integer toolCalls;

    @ApiModelProperty(value = "请求耗时(毫秒)")
    private Integer latencyMs;

    @ApiModelProperty(value = "创建时间")
    private Date createTime;

    private static final long serialVersionUID = 1L;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public String getIntent() {
        return intent;
    }

    public void setIntent(String intent) {
        this.intent = intent;
    }

    public String getModel() {
        return model;
    }

    public void setModel(String model) {
        this.model = model;
    }

    public Integer getPromptTokens() {
        return promptTokens;
    }

    public void setPromptTokens(Integer promptTokens) {
        this.promptTokens = promptTokens;
    }

    public Integer getCompletionTokens() {
        return completionTokens;
    }

    public void setCompletionTokens(Integer completionTokens) {
        this.completionTokens = completionTokens;
    }

    public Integer getTotalTokens() {
        return totalTokens;
    }

    public void setTotalTokens(Integer totalTokens) {
        this.totalTokens = totalTokens;
    }

    public Integer getToolCalls() {
        return toolCalls;
    }

    public void setToolCalls(Integer toolCalls) {
        this.toolCalls = toolCalls;
    }

    public Integer getLatencyMs() {
        return latencyMs;
    }

    public void setLatencyMs(Integer latencyMs) {
        this.latencyMs = latencyMs;
    }

    public Date getCreateTime() {
        return createTime;
    }

    public void setCreateTime(Date createTime) {
        this.createTime = createTime;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append(getClass().getSimpleName());
        sb.append(" [");
        sb.append("Hash = ").append(hashCode());
        sb.append(", id=").append(id);
        sb.append(", username=").append(username);
        sb.append(", sessionId=").append(sessionId);
        sb.append(", intent=").append(intent);
        sb.append(", model=").append(model);
        sb.append(", promptTokens=").append(promptTokens);
        sb.append(", completionTokens=").append(completionTokens);
        sb.append(", totalTokens=").append(totalTokens);
        sb.append(", toolCalls=").append(toolCalls);
        sb.append(", latencyMs=").append(latencyMs);
        sb.append(", createTime=").append(createTime);
        sb.append(", serialVersionUID=").append(serialVersionUID);
        sb.append("]");
        return sb.toString();
    }
}