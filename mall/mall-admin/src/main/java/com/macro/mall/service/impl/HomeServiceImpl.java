package com.macro.mall.service.impl;

import com.macro.mall.dao.HomeDao;
import com.macro.mall.dto.HomeChartResult;
import com.macro.mall.dto.HomeMemberOverview;
import com.macro.mall.dto.HomeProductOverview;
import com.macro.mall.dto.HomeSummaryResult;
import com.macro.mall.service.HomeCacheService;
import com.macro.mall.service.HomeService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

/**
 * 首页统计Service实现类
 *
 * 缓存策略：Cache-Aside（旁路缓存）
 * - 读：先查缓存 → 命中直接返回 → 未命中查 DB → 写缓存 → 返回
 * - 缓存 key 由 HomeCacheService 管理，TTL 5 分钟
 * - Redis 故障时 HomeCacheService 静默降级，自动走 DB
 */
@Service
public class HomeServiceImpl implements HomeService {

    private static final Logger logger = LoggerFactory.getLogger(HomeServiceImpl.class);

    @Autowired
    private HomeDao homeDao;

    @Autowired
    private HomeCacheService homeCacheService;

    @Override
    public HomeSummaryResult getSummary() {
        // 1. 先查缓存
        HomeSummaryResult cached = homeCacheService.getSummary();
        if (cached != null) {
            logger.debug("首页汇总统计命中缓存");
            return cached;
        }

        // 2. 缓存未命中，查数据库
        logger.debug("首页汇总统计未命中缓存，查询数据库");
        HomeSummaryResult result = homeDao.getSummary();
        if (result == null) {
            return new HomeSummaryResult();
        }

        // 补充退款/退货/广告到期数量
        result.setPendingRefundCount(homeDao.getPendingRefundCount());
        result.setPendingReturnCount(homeDao.getPendingReturnCount());
        result.setAdExpiringCount(homeDao.getAdExpiringCount());

        // 计算同比百分比
        result.setMonthlyOrderGrowth(calcGrowth(result.getMonthlyOrderCount(), result.getLastMonthOrderCount()));
        result.setWeeklyOrderGrowth(calcGrowth(result.getWeeklyOrderCount(), result.getLastWeekOrderCount()));
        result.setMonthlySalesGrowth(calcGrowth(result.getMonthlySales(), result.getLastMonthSales()));
        result.setWeeklySalesGrowth(calcGrowth(result.getWeeklySales(), result.getLastWeekSales()));

        // 3. 写入缓存
        homeCacheService.setSummary(result);
        return result;
    }

    @Override
    public List<HomeChartResult> getChartData(String startDate, String endDate) {
        // 1. 先查缓存
        List<HomeChartResult> cached = homeCacheService.getChartData(startDate, endDate);
        if (cached != null) {
            logger.debug("折线图数据命中缓存: {} ~ {}", startDate, endDate);
            return cached;
        }

        // 2. 缓存未命中，查数据库
        logger.debug("折线图数据未命中缓存，查询数据库: {} ~ {}", startDate, endDate);
        List<HomeChartResult> data = homeDao.getChartData(startDate, endDate);

        // 3. 写入缓存
        homeCacheService.setChartData(startDate, endDate, data);
        return data;
    }

    @Override
    public HomeProductOverview getProductOverview() {
        // 1. 先查缓存
        HomeProductOverview cached = homeCacheService.getProductOverview();
        if (cached != null) {
            logger.debug("商品总览命中缓存");
            return cached;
        }

        // 2. 缓存未命中，查数据库
        logger.debug("商品总览未命中缓存，查询数据库");
        HomeProductOverview data = homeDao.getProductOverview();

        // 3. 写入缓存
        homeCacheService.setProductOverview(data);
        return data;
    }

    @Override
    public HomeMemberOverview getMemberOverview() {
        // 1. 先查缓存
        HomeMemberOverview cached = homeCacheService.getMemberOverview();
        if (cached != null) {
            logger.debug("用户总览命中缓存");
            return cached;
        }

        // 2. 缓存未命中，查数据库
        logger.debug("用户总览未命中缓存，查询数据库");
        HomeMemberOverview data = homeDao.getMemberOverview();

        // 3. 写入缓存
        homeCacheService.setMemberOverview(data);
        return data;
    }

    /**
     * 计算同比百分比：(current - previous) / previous * 100
     * 返回格式如 "+10.5%" 或 "-5.2%"，previous 为 0 时返回 "0%"
     */
    private String calcGrowth(long current, long previous) {
        if (previous == 0) {
            return current > 0 ? "+100%" : "0%";
        }
        double pct = (double) (current - previous) / previous * 100;
        String sign = pct >= 0 ? "+" : "";
        return sign + String.format("%.1f", pct) + "%";
    }

    private String calcGrowth(BigDecimal current, BigDecimal previous) {
        if (current == null) current = BigDecimal.ZERO;
        if (previous == null) previous = BigDecimal.ZERO;
        if (previous.compareTo(BigDecimal.ZERO) == 0) {
            return current.compareTo(BigDecimal.ZERO) > 0 ? "+100%" : "0%";
        }
        BigDecimal pct = current.subtract(previous)
                .divide(previous, 4, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100));
        String sign = pct.compareTo(BigDecimal.ZERO) >= 0 ? "+" : "";
        return sign + String.format("%.1f", pct.doubleValue()) + "%";
    }
}
