package com.macro.mall.portal.service;

import com.macro.mall.model.OmsOrderReturnApply;
import com.macro.mall.portal.domain.OmsOrderReturnApplyParam;

import java.util.List;

/**
 * 前台订单退货管理Service
 * Created by macro on 2018/10/17.
 */
public interface OmsPortalOrderReturnApplyService {
    /**
     * 提交申请
     */
    int create(OmsOrderReturnApplyParam returnApply);

    /**
     * 获取会员的退货申请列表
     */
    List<OmsOrderReturnApply> list(String memberUsername);

    /**
     * 获取退货申请详情
     */
    OmsOrderReturnApply getItem(Long id);
}
