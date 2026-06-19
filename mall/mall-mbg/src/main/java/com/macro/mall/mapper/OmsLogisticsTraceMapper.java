package com.macro.mall.mapper;

import com.macro.mall.model.OmsLogisticsTrace;
import com.macro.mall.model.OmsLogisticsTraceExample;
import java.util.List;
import org.apache.ibatis.annotations.Param;

public interface OmsLogisticsTraceMapper {
    long countByExample(OmsLogisticsTraceExample example);

    int deleteByExample(OmsLogisticsTraceExample example);

    int deleteByPrimaryKey(Long id);

    int insert(OmsLogisticsTrace row);

    int insertSelective(OmsLogisticsTrace row);

    List<OmsLogisticsTrace> selectByExample(OmsLogisticsTraceExample example);

    OmsLogisticsTrace selectByPrimaryKey(Long id);

    int updateByExampleSelective(@Param("row") OmsLogisticsTrace row, @Param("example") OmsLogisticsTraceExample example);

    int updateByExample(@Param("row") OmsLogisticsTrace row, @Param("example") OmsLogisticsTraceExample example);

    int updateByPrimaryKeySelective(OmsLogisticsTrace row);

    int updateByPrimaryKey(OmsLogisticsTrace row);
}