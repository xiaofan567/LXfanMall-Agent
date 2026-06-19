package com.macro.mall.portal.service.impl;

import com.github.pagehelper.PageHelper;
import com.macro.mall.mapper.OmsOrderMapper;
import com.macro.mall.mapper.PmsCommentMapper;
import com.macro.mall.model.*;
import com.macro.mall.portal.domain.PmsCommentParam;
import com.macro.mall.portal.service.PmsCommentService;
import com.macro.mall.portal.service.UmsMemberService;
import org.springframework.beans.factory.annotation.Autowired;
import com.macro.mall.common.constant.EnableStatus;
import org.springframework.stereotype.Service;

import java.util.Date;
import java.util.List;

/**
 * 前台商品评价管理Service实现类
 */
@Service
public class PmsCommentServiceImpl implements PmsCommentService {

    @Autowired
    private PmsCommentMapper commentMapper;

    @Autowired
    private UmsMemberService memberService;

    @Autowired
    private OmsOrderMapper orderMapper;

    @Override
    public List<PmsComment> list(Long productId, Integer pageNum, Integer pageSize) {
        PageHelper.startPage(pageNum, pageSize);
        PmsCommentExample example = new PmsCommentExample();
        example.createCriteria()
                .andProductIdEqualTo(productId)
                .andShowStatusEqualTo(EnableStatus.ENABLED.getValue());
        example.setOrderByClause("create_time desc");
        return commentMapper.selectByExampleWithBLOBs(example);
    }

    @Override
    public long count(Long productId) {
        PmsCommentExample example = new PmsCommentExample();
        example.createCriteria()
                .andProductIdEqualTo(productId)
                .andShowStatusEqualTo(EnableStatus.ENABLED.getValue());
        return commentMapper.countByExample(example);
    }

    @Override
    public void create(PmsCommentParam param) {
        UmsMember member = memberService.getCurrentMember();
        PmsComment comment = new PmsComment();
        comment.setMemberId(member.getId());
        comment.setOrderId(param.getOrderId());
        comment.setOrderItemId(param.getOrderItemId());
        comment.setProductId(param.getProductId());
        comment.setStar(param.getStar());
        comment.setContent(param.getContent());
        comment.setPics(param.getPics());
        comment.setProductAttribute(param.getProductAttribute());
        comment.setMemberNickName(member.getNickname());
        comment.setMemberIcon(member.getIcon());
        comment.setCreateTime(new Date());
        comment.setShowStatus(1); // 默认显示
        comment.setCollectCouont(0);
        comment.setReadCount(0);
        comment.setReplayCount(0);
        commentMapper.insertSelective(comment);

        // 更新订单的评论时间
        OmsOrder order = new OmsOrder();
        order.setId(param.getOrderId());
        order.setCommentTime(new Date());
        OmsOrderExample example = new OmsOrderExample();
        example.createCriteria().andIdEqualTo(param.getOrderId());
        orderMapper.updateByExampleSelective(order, example);
    }

    @Override
    public List<PmsComment> listByMember(Integer pageNum, Integer pageSize) {
        UmsMember member = memberService.getCurrentMember();
        PageHelper.startPage(pageNum, pageSize);
        PmsCommentExample example = new PmsCommentExample();
        example.createCriteria()
                .andMemberIdEqualTo(member.getId());
        example.setOrderByClause("create_time desc");
        return commentMapper.selectByExampleWithBLOBs(example);
    }
}
