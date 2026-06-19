package com.macro.mall.portal.service.impl;

import cn.hutool.core.collection.CollUtil;
import com.macro.mall.mapper.OmsCompanyAddressMapper;
import com.macro.mall.mapper.OmsOrderMapper;
import com.macro.mall.model.OmsCompanyAddress;
import com.macro.mall.model.OmsCompanyAddressExample;
import com.macro.mall.model.OmsOrder;
import com.macro.mall.model.OmsOrderExample;
import com.macro.mall.portal.dao.PortalOrderLogisticsDao;
import com.macro.mall.portal.domain.LogisticsDetailResult;
import com.macro.mall.portal.domain.LogisticsTraceResult;
import com.macro.mall.portal.service.OmsPortalOrderLogisticsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 物流查询Service实现类
 * Created by macro on 2026/5/18.
 */
@Service
public class OmsPortalOrderLogisticsServiceImpl implements OmsPortalOrderLogisticsService {

    @Autowired
    private OmsOrderMapper orderMapper;
    @Autowired
    private OmsCompanyAddressMapper companyAddressMapper;
    @Autowired
    private PortalOrderLogisticsDao logisticsDao;

    @Override
    public LogisticsDetailResult getLogisticsDetail(Long orderId) {
        // 查询订单
        OmsOrder order = orderMapper.selectByPrimaryKey(orderId);
        if (order == null) {
            return null;
        }

        LogisticsDetailResult result = new LogisticsDetailResult();
        result.setDeliveryCompany(order.getDeliveryCompany());
        result.setDeliverySn(order.getDeliverySn());
        result.setDeliveryTime(order.getDeliveryTime());
        result.setReceiverName(order.getReceiverName());
        result.setReceiverPhone(order.getReceiverPhone());

        // 拼接收货地址
        StringBuilder address = new StringBuilder();
        if (order.getReceiverProvince() != null) {
            address.append(order.getReceiverProvince());
        }
        if (order.getReceiverCity() != null) {
            address.append(" ").append(order.getReceiverCity());
        }
        if (order.getReceiverRegion() != null) {
            address.append(" ").append(order.getReceiverRegion());
        }
        if (order.getReceiverDetailAddress() != null) {
            address.append(" ").append(order.getReceiverDetailAddress());
        }
        result.setReceiverAddress(address.toString());

        // 查询物流轨迹
        List<LogisticsTraceResult> traceList = logisticsDao.getLogisticsTrace(orderId);
        result.setTraceList(traceList);

        return result;
    }

    /**
     * 获取默认发货地址的城市
     */
    public String getDepartureCity() {
        OmsCompanyAddressExample example = new OmsCompanyAddressExample();
        example.createCriteria().andSendStatusEqualTo(1);
        List<OmsCompanyAddress> addresses = companyAddressMapper.selectByExample(example);
        if (CollUtil.isNotEmpty(addresses)) {
            OmsCompanyAddress address = addresses.get(0);
            StringBuilder sb = new StringBuilder();
            if (address.getProvince() != null) {
                sb.append(address.getProvince());
            }
            if (address.getCity() != null) {
                sb.append(address.getCity());
            }
            return sb.toString();
        }
        return "广东省深圳市";
    }
}
