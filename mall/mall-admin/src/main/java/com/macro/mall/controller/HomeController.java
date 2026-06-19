package com.macro.mall.controller;

import com.macro.mall.common.api.CommonResult;
import com.macro.mall.dto.HomeChartResult;
import com.macro.mall.dto.HomeMemberOverview;
import com.macro.mall.dto.HomeProductOverview;
import com.macro.mall.dto.HomeSummaryResult;
import com.macro.mall.service.HomeService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 首页统计Controller
 */
@Controller
@Api(tags = "HomeController")
@Tag(name = "HomeController", description = "首页统计")
@RequestMapping("/home")
public class HomeController {

    @Autowired
    private HomeService homeService;

    @ApiOperation("获取首页汇总统计")
    @RequestMapping(value = "/summary", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<HomeSummaryResult> summary() {
        return CommonResult.success(homeService.getSummary());
    }

    @ApiOperation("获取订单统计折线图数据")
    @RequestMapping(value = "/chart", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<List<HomeChartResult>> chart(@RequestParam("startDate") String startDate,
                                                     @RequestParam("endDate") String endDate) {
        return CommonResult.success(homeService.getChartData(startDate, endDate));
    }

    @ApiOperation("获取商品总览")
    @RequestMapping(value = "/productOverview", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<HomeProductOverview> productOverview() {
        return CommonResult.success(homeService.getProductOverview());
    }

    @ApiOperation("获取用户总览")
    @RequestMapping(value = "/memberOverview", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<HomeMemberOverview> memberOverview() {
        return CommonResult.success(homeService.getMemberOverview());
    }
}
