package com.macro.mall.portal.component;

import cn.hutool.core.collection.CollUtil;
import com.macro.mall.mapper.OmsOrderMapper;
import com.macro.mall.model.OmsOrder;
import com.macro.mall.model.OmsOrderExample;
import com.macro.mall.portal.dao.PortalOrderLogisticsDao;
import com.macro.mall.portal.service.impl.OmsPortalOrderLogisticsServiceImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import com.macro.mall.common.constant.DeleteStatus;
import com.macro.mall.common.constant.OrderStatus;
import org.springframework.stereotype.Component;

import java.util.Date;
import java.util.List;

/**
 * 物流模拟定时任务
 * 每60秒执行一次，将已发货订单的物流状态推进到下一阶段
 * Created by macro on 2026/5/18.
 */
@Component
public class LogisticsSimulateTask {

    private static final Logger LOGGER = LoggerFactory.getLogger(LogisticsSimulateTask.class);

    @Autowired
    private OmsOrderMapper orderMapper;
    @Autowired
    private PortalOrderLogisticsDao logisticsDao;
    @Autowired
    private OmsPortalOrderLogisticsServiceImpl logisticsService;

    /**
     * 每60秒执行一次
     */
    @Scheduled(fixedDelay = 60000)
    public void simulateLogistics() {
        LOGGER.info("物流模拟定时任务开始执行");

        // 查询所有已发货(status=2)的订单
        OmsOrderExample example = new OmsOrderExample();
        example.createCriteria()
                .andDeleteStatusEqualTo(DeleteStatus.NOT_DELETED.getValue())
                .andStatusEqualTo(OrderStatus.SHIPPED.getValue());
        List<OmsOrder> orderList = orderMapper.selectByExample(example);

        if (CollUtil.isEmpty(orderList)) {
            return;
        }

        for (OmsOrder order : orderList) {
            try {
                processOrder(order);
            } catch (Exception e) {
                LOGGER.error("处理订单 {} 物流模拟时出错: {}", order.getId(), e.getMessage());
            }
        }

        LOGGER.info("物流模拟定时任务执行完毕，处理订单数：{}", orderList.size());
    }

    private void processOrder(OmsOrder order) {
        Long orderId = order.getId();

        // 查询该订单当前最大 status_code
        Integer maxCode = logisticsDao.getMaxStatusCode(orderId);

        if (maxCode == null) {
            // 首次初始化：插入第一条物流记录（status_code=0）
            String departureCity = logisticsService.getDepartureCity();
            logisticsDao.insertTrace(orderId, order.getDeliverySn(), 0,
                    departureCity + "仓库", "您的包裹正在出库", new Date());
            LOGGER.info("订单 {} 物流轨迹初始化完成，发货城市：{}", orderId, departureCity);
        } else if (maxCode < 10) {
            // 推进到下一阶段
            int nextCode = maxCode + 1;
            insertNextTrace(order, nextCode, order.getDeliverySn());
            LOGGER.info("订单 {} 物流轨迹推进到状态 {}", orderId, nextCode);

            // 当物流轨迹到达签收状态(10)时，自动将订单状态更新为已送达(7)
            if (nextCode == 10) {
                order.setStatus(OrderStatus.DELIVERED.getValue());
                orderMapper.updateByPrimaryKey(order);
                LOGGER.info("订单 {} 物流已签收，订单状态更新为已送达(7)", orderId);
            }
        } else if (maxCode == 10 && order.getStatus() == OrderStatus.SHIPPED.getValue()) {
            // 物流已签收但订单状态仍为已发货(2)，补更新为已送达(7)
            order.setStatus(OrderStatus.DELIVERED.getValue());
            orderMapper.updateByPrimaryKey(order);
            LOGGER.info("订单 {} 物流已签收，补更新订单状态为已送达(7)", orderId);
        }
        // maxCode == 10 且状态已是 7 或 3 时，不再处理
    }

    private void insertNextTrace(OmsOrder order, int code, String deliverySn) {
        Long orderId = order.getId();
        String departureCity = logisticsService.getDepartureCity();
        String receiverCity = order.getReceiverCity() != null ? order.getReceiverCity() : "目的城市";
        String receiverRegion = order.getReceiverRegion() != null ? order.getReceiverRegion() : "目的区域";
        String location;
        String statusText;
        Date now = new Date();

        switch (code) {
            case 1:
                location = departureCity + "仓库";
                statusText = "包裹已出库，等待快递员揽收";
                break;
            case 2:
                location = departureCity;
                statusText = "快递员已揽收";
                break;
            case 3:
                location = departureCity + "营业网点";
                statusText = "快件已到达【" + departureCity + "】营业网点";
                break;
            case 4:
                location = departureCity;
                statusText = "快件已从【" + departureCity + "】网点发出，下一站：分拨中心";
                break;
            case 5:
                location = departureCity + "分拨中心";
                statusText = "快件已到达【" + departureCity + "】分拨中心";
                break;
            case 6:
                location = departureCity;
                statusText = "快件已从【" + departureCity + "】分拨中心发出，前往【" + receiverCity + "】";
                break;
            case 7:
                location = receiverCity + "分拨中心";
                statusText = "快件已到达【" + receiverCity + "】分拨中心";
                break;
            case 8:
                location = receiverCity;
                statusText = "快件已从【" + receiverCity + "】分拨中心发出，下一站：【" + receiverRegion + "】网点";
                break;
            case 9:
                location = receiverCity;
                statusText = "快递员正在派送中，预计今日送达";
                break;
            case 10:
                location = receiverCity;
                statusText = "订单已签收，期待再次为您服务！";
                break;
            default:
                location = "";
                statusText = "";
        }

        logisticsDao.insertTrace(orderId, deliverySn, code, location, statusText, now);
    }
}
