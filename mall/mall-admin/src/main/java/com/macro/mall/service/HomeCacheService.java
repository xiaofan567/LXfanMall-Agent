package com.macro.mall.service;

import com.macro.mall.dto.HomeChartResult;
import com.macro.mall.dto.HomeMemberOverview;
import com.macro.mall.dto.HomeProductOverview;
import com.macro.mall.dto.HomeSummaryResult;

import java.util.List;

/**
 * 首页统计缓存Service
 */
public interface HomeCacheService {

    /**
     * 获取缓存的汇总统计
     */
    HomeSummaryResult getSummary();

    /**
     * 缓存汇总统计
     */
    void setSummary(HomeSummaryResult result);

    /**
     * 删除汇总统计缓存
     */
    void delSummary();

    /**
     * 获取缓存的折线图数据
     */
    List<HomeChartResult> getChartData(String startDate, String endDate);

    /**
     * 缓存折线图数据
     */
    void setChartData(String startDate, String endDate, List<HomeChartResult> data);

    /**
     * 删除折线图缓存
     */
    void delChartData();

    /**
     * 获取缓存的商品总览
     */
    HomeProductOverview getProductOverview();

    /**
     * 缓存商品总览
     */
    void setProductOverview(HomeProductOverview data);

    /**
     * 删除商品总览缓存
     */
    void delProductOverview();

    /**
     * 获取缓存的用户总览
     */
    HomeMemberOverview getMemberOverview();

    /**
     * 缓存用户总览
     */
    void setMemberOverview(HomeMemberOverview data);

    /**
     * 删除用户总览缓存
     */
    void delMemberOverview();

    /**
     * 清除所有首页缓存
     */
    void delAll();
}
