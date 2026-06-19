package com.macro.mall.mapper;

import com.macro.mall.model.UmsTokenUsage;
import com.macro.mall.model.UmsTokenUsageExample;
import java.util.List;
import org.apache.ibatis.annotations.Param;

public interface UmsTokenUsageMapper {
    long countByExample(UmsTokenUsageExample example);

    int deleteByExample(UmsTokenUsageExample example);

    int deleteByPrimaryKey(Long id);

    int insert(UmsTokenUsage row);

    int insertSelective(UmsTokenUsage row);

    List<UmsTokenUsage> selectByExample(UmsTokenUsageExample example);

    UmsTokenUsage selectByPrimaryKey(Long id);

    int updateByExampleSelective(@Param("row") UmsTokenUsage row, @Param("example") UmsTokenUsageExample example);

    int updateByExample(@Param("row") UmsTokenUsage row, @Param("example") UmsTokenUsageExample example);

    int updateByPrimaryKeySelective(UmsTokenUsage row);

    int updateByPrimaryKey(UmsTokenUsage row);
}