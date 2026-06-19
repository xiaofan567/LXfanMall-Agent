package com.macro.mall.service;

import com.macro.mall.dto.HomeChartResult;
import com.macro.mall.dto.HomeMemberOverview;
import com.macro.mall.dto.HomeProductOverview;
import com.macro.mall.dto.HomeSummaryResult;

import java.util.List;

/**
 * 首页统计Service
 */
public interface HomeService {

    /**
     * 获取首页汇总统计（含同比计算）
     */
    HomeSummaryResult getSummary();

    /**
     * 获取折线图数据
     */
    List<HomeChartResult> getChartData(String startDate, String endDate);

    /**
     * 获取商品总览
     */
    HomeProductOverview getProductOverview();

    /**
     * 获取用户总览
     */
    HomeMemberOverview getMemberOverview();
}
