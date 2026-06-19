package com.macro.mall.portal.service;

import com.macro.mall.portal.domain.LogisticsDetailResult;

/**
 * 物流查询Service
 * Created by macro on 2026/5/18.
 */
public interface OmsPortalOrderLogisticsService {

    /**
     * 获取订单物流详情
     */
    LogisticsDetailResult getLogisticsDetail(Long orderId);
}
