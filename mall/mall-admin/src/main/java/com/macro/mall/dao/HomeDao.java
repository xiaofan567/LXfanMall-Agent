package com.macro.mall.dao;

import com.macro.mall.dto.HomeChartResult;
import com.macro.mall.dto.HomeMemberOverview;
import com.macro.mall.dto.HomeProductOverview;
import com.macro.mall.dto.HomeSummaryResult;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 首页统计自定义Dao
 */
public interface HomeDao {

    /**
     * 获取首页汇总统计（订单数、销售额、各状态订单数、同比数据）
     */
    HomeSummaryResult getSummary();

    /**
     * 获取折线图数据（按日期分组的订单数和金额）
     */
    List<HomeChartResult> getChartData(@Param("startDate") String startDate,
                                       @Param("endDate") String endDate);

    /**
     * 获取商品总览（已上架、已下架、库存紧张、总数）
     */
    HomeProductOverview getProductOverview();

    /**
     * 获取用户总览（今日/昨日/本月新增、总数）
     */
    HomeMemberOverview getMemberOverview();

    /**
     * 获取待处理退款申请数 (return_apply status=0 表示待处理)
     */
    Long getPendingRefundCount();

    /**
     * 获取待处理退货订单数 (return_apply status=1 表示退货中)
     */
    Long getPendingReturnCount();

    /**
     * 获取即将到期的广告位数 (7天内到期且状态为启用)
     */
    Long getAdExpiringCount();
}
