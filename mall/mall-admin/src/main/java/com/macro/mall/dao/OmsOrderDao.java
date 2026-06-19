package com.macro.mall.dao;

import com.macro.mall.dto.LogisticsTraceResult;
import com.macro.mall.dto.OmsOrderDeliveryParam;
import com.macro.mall.dto.OmsOrderDetail;
import com.macro.mall.dto.OmsOrderQueryParam;
import com.macro.mall.model.OmsOrder;
import org.apache.ibatis.annotations.Param;

import java.util.Date;
import java.util.List;

/**
 * 订单查询自定义Dao
 * Created by macro on 2018/10/12.
 */
public interface OmsOrderDao {
    /**
     * 条件查询订单
     */
    List<OmsOrder> getList(@Param("queryParam") OmsOrderQueryParam queryParam);

    /**
     * 批量发货
     */
    int delivery(@Param("list") List<OmsOrderDeliveryParam> deliveryParamList);

    /**
     * 获取订单详情
     */
    OmsOrderDetail getDetail(@Param("id") Long id);

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
