package com.macro.mall.portal.dao;

import com.macro.mall.portal.domain.LogisticsTraceResult;
import org.apache.ibatis.annotations.Param;

import java.util.Date;
import java.util.List;

/**
 * 物流轨迹查询Dao
 * Created by macro on 2026/5/18.
 */
public interface PortalOrderLogisticsDao {

    /**
     * 获取订单物流轨迹列表
     */
    List<LogisticsTraceResult> getLogisticsTrace(@Param("orderId") Long orderId);

    /**
     * 获取订单当前最大轨迹编码
     */
    Integer getMaxStatusCode(@Param("orderId") Long orderId);

    /**
     * 插入物流轨迹记录
     */
    int insertTrace(@Param("orderId") Long orderId,
                    @Param("deliverySn") String deliverySn,
                    @Param("statusCode") Integer statusCode,
                    @Param("location") String location,
                    @Param("statusText") String statusText,
                    @Param("traceTime") Date traceTime);
}
