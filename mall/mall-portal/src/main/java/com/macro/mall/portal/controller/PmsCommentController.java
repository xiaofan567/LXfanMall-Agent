package com.macro.mall.portal.controller;

import com.macro.mall.common.api.CommonPage;
import com.macro.mall.common.api.CommonResult;
import com.macro.mall.model.PmsComment;
import com.macro.mall.portal.domain.PmsCommentParam;
import com.macro.mall.portal.service.PmsCommentService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 前台商品评价管理Controller
 */
@Controller
@Api(tags = "PmsCommentController")
@Tag(name = "PmsCommentController", description = "前台商品评价管理")
@RequestMapping("/comment")
public class PmsCommentController {

    @Autowired
    private PmsCommentService commentService;

    @ApiOperation("分页获取商品评价")
    @RequestMapping(value = "/list", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<CommonPage<PmsComment>> list(@RequestParam Long productId,
                                                     @RequestParam(defaultValue = "1") Integer pageNum,
                                                     @RequestParam(defaultValue = "10") Integer pageSize) {
        List<PmsComment> commentList = commentService.list(productId, pageNum, pageSize);
        return CommonResult.success(CommonPage.restPage(commentList));
    }

    @ApiOperation("获取商品评价数量")
    @RequestMapping(value = "/count", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<Long> count(@RequestParam Long productId) {
        long count = commentService.count(productId);
        return CommonResult.success(count);
    }

    @ApiOperation("创建商品评价")
    @RequestMapping(value = "/create", method = RequestMethod.POST)
    @ResponseBody
    public CommonResult create(@RequestBody PmsCommentParam param) {
        commentService.create(param);
        return CommonResult.success(null, "评价成功");
    }

    @ApiOperation("获取当前会员的评价列表")
    @RequestMapping(value = "/listByMember", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<CommonPage<PmsComment>> listByMember(@RequestParam(defaultValue = "1") Integer pageNum,
                                                              @RequestParam(defaultValue = "10") Integer pageSize) {
        List<PmsComment> commentList = commentService.listByMember(pageNum, pageSize);
        return CommonResult.success(CommonPage.restPage(commentList));
    }
}
