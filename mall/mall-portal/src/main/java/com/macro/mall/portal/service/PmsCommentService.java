package com.macro.mall.portal.service;

import com.macro.mall.model.PmsComment;
import com.macro.mall.portal.domain.PmsCommentParam;

import java.util.List;

/**
 * 前台商品评价管理Service
 */
public interface PmsCommentService {
    /**
     * 根据商品ID分页获取评价列表
     */
    List<PmsComment> list(Long productId, Integer pageNum, Integer pageSize);

    /**
     * 获取商品评价数量
     */
    long count(Long productId);

    /**
     * 创建商品评价
     */
    void create(PmsCommentParam param);

    /**
     * 获取当前会员的评价列表
     */
    List<PmsComment> listByMember(Integer pageNum, Integer pageSize);
}
