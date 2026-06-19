package com.macro.mall.controller;

import com.macro.mall.common.api.CommonPage;
import com.macro.mall.common.api.CommonResult;
import com.macro.mall.dto.*;
import com.macro.mall.service.TokenUsageService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Token用量统计Controller
 */
@Controller
@Api(tags = "TokenUsageController")
@Tag(name = "TokenUsageController", description = "Token用量统计")
@RequestMapping("/home/tokenUsage")
public class TokenUsageController {

    @Autowired
    private TokenUsageService tokenUsageService;

    @ApiOperation("上报Token用量记录")
    @RequestMapping(value = "/report", method = RequestMethod.POST)
    @ResponseBody
    public CommonResult<String> report(@RequestBody TokenUsageReportParam param) {
        tokenUsageService.report(
                param.getUsername(),
                param.getSessionId(),
                param.getIntent(),
                param.getModel(),
                param.getPromptTokens(),
                param.getCompletionTokens(),
                param.getTotalTokens(),
                param.getToolCalls(),
                param.getLatencyMs()
        );
        return CommonResult.success("ok");
    }

    @ApiOperation("获取Token用量汇总统计")
    @RequestMapping(value = "/summary", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<TokenUsageSummaryResult> summary() {
        return CommonResult.success(tokenUsageService.getSummary());
    }

    @ApiOperation("获取Token用量折线图数据")
    @RequestMapping(value = "/chart", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<List<TokenUsageChartResult>> chart(@RequestParam("startDate") String startDate,
                                                           @RequestParam("endDate") String endDate) {
        return CommonResult.success(tokenUsageService.getChartData(startDate, endDate));
    }

    @ApiOperation("获取用户Token用量排行")
    @RequestMapping(value = "/ranking", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<List<TokenUsageRankingResult>> ranking(@RequestParam(value = "limit", defaultValue = "10") Integer limit) {
        return CommonResult.success(tokenUsageService.getUserRanking(limit));
    }

    @ApiOperation("获取意图分布")
    @RequestMapping(value = "/intentDistribution", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<List<TokenUsageIntentResult>> intentDistribution() {
        return CommonResult.success(tokenUsageService.getIntentDistribution());
    }

    @ApiOperation("分页查询Token用量明细")
    @RequestMapping(value = "/list", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<CommonPage<TokenUsageDetailResult>> list(
            @RequestParam(value = "username", required = false) String username,
            @RequestParam(value = "intent", required = false) String intent,
            @RequestParam(value = "startDate", required = false) String startDate,
            @RequestParam(value = "endDate", required = false) String endDate,
            @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
            @RequestParam(value = "pageSize", defaultValue = "10") Integer pageSize) {
        return CommonResult.success(tokenUsageService.getList(username, intent, startDate, endDate, pageNum, pageSize));
    }
}
