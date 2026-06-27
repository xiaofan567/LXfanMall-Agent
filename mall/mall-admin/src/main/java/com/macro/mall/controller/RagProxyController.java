package com.macro.mall.controller;

import com.macro.mall.common.api.CommonResult;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Controller;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

/**
 * RAG 知识库管理代理 Controller — 转发请求到 agent-service。
 */
@Controller
@Api(tags = "RagProxyController")
@Tag(name = "RagProxyController", description = "RAG 知识库管理")
@RequestMapping("/rag")
public class RagProxyController {

    private static final Logger LOGGER = LoggerFactory.getLogger(RagProxyController.class);

    @Autowired
    private RestTemplate restTemplate;

    @Value("${agent.service.url:http://localhost:8000}")
    private String agentServiceUrl;

    @ApiOperation("上传文档并处理入库")
    @RequestMapping(value = "/upload", method = RequestMethod.POST)
    @ResponseBody
    public CommonResult<Object> upload(
            @RequestPart("file") MultipartFile file,
            @RequestParam(value = "strategy", defaultValue = "recursive") String strategy,
            @RequestParam(value = "chunk_size", defaultValue = "500") int chunkSize,
            @RequestParam(value = "chunk_overlap", defaultValue = "50") int chunkOverlap
    ) {
        try {
            String url = agentServiceUrl + "/api/v1/rag/upload";

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", file.getResource());
            body.add("strategy", strategy);
            body.add("chunk_size", String.valueOf(chunkSize));
            body.add("chunk_overlap", String.valueOf(chunkOverlap));

            HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    url, HttpMethod.POST, requestEntity,
                    new org.springframework.core.ParameterizedTypeReference<Map<String, Object>>() {}
            );

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> result = response.getBody();
                if (Integer.valueOf(200).equals(result.get("code"))) {
                    return CommonResult.success(result.get("data"));
                }
                return CommonResult.failed((String) result.get("message"));
            }
            return CommonResult.failed("代理请求失败");
        } catch (Exception e) {
            LOGGER.error("RAG 文档上传代理失败", e);
            return CommonResult.failed("文档上传失败: " + e.getMessage());
        }
    }

    @ApiOperation("获取文档列表")
    @RequestMapping(value = "/documents", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<Object> listDocuments(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        try {
            String url = agentServiceUrl + "/api/v1/rag/documents?page=" + page + "&size=" + size;
            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    url, HttpMethod.GET, null,
                    new org.springframework.core.ParameterizedTypeReference<Map<String, Object>>() {}
            );
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> result = response.getBody();
                if (Integer.valueOf(200).equals(result.get("code"))) {
                    return CommonResult.success(result.get("data"));
                }
            }
            return CommonResult.failed("获取文档列表失败");
        } catch (Exception e) {
            LOGGER.error("获取 RAG 文档列表代理失败", e);
            return CommonResult.failed("获取文档列表失败: " + e.getMessage());
        }
    }

    @ApiOperation("删除文档")
    @RequestMapping(value = "/documents/{fileName}", method = RequestMethod.DELETE)
    @ResponseBody
    public CommonResult<Object> deleteDocument(@PathVariable String fileName) {
        try {
            String url = agentServiceUrl + "/api/v1/rag/documents/" + fileName;
            restTemplate.delete(url);
            return CommonResult.success(null);
        } catch (Exception e) {
            LOGGER.error("RAG 文档删除代理失败", e);
            return CommonResult.failed("删除文档失败: " + e.getMessage());
        }
    }

    @ApiOperation("获取文本分割策略")
    @RequestMapping(value = "/strategies", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<Object> getStrategies() {
        try {
            String url = agentServiceUrl + "/api/v1/rag/strategies";
            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    url, HttpMethod.GET, null,
                    new org.springframework.core.ParameterizedTypeReference<Map<String, Object>>() {}
            );
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> result = response.getBody();
                if (Integer.valueOf(200).equals(result.get("code"))) {
                    return CommonResult.success(result.get("data"));
                }
            }
            return CommonResult.failed("获取策略列表失败");
        } catch (Exception e) {
            LOGGER.error("获取 RAG 策略列表代理失败", e);
            return CommonResult.failed("获取策略列表失败: " + e.getMessage());
        }
    }

    @ApiOperation("获取知识库统计")
    @RequestMapping(value = "/stats", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<Object> getStats() {
        try {
            String url = agentServiceUrl + "/api/v1/rag/stats";
            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    url, HttpMethod.GET, null,
                    new org.springframework.core.ParameterizedTypeReference<Map<String, Object>>() {}
            );
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> result = response.getBody();
                if (Integer.valueOf(200).equals(result.get("code"))) {
                    return CommonResult.success(result.get("data"));
                }
            }
            return CommonResult.failed("获取统计信息失败");
        } catch (Exception e) {
            LOGGER.error("获取 RAG 统计信息代理失败", e);
            return CommonResult.failed("获取统计信息失败: " + e.getMessage());
        }
    }

    @ApiOperation("获取文档切片详情")
    @RequestMapping(value = "/documents/{fileName}/chunks", method = RequestMethod.GET)
    @ResponseBody
    public CommonResult<Object> getDocumentChunks(@PathVariable String fileName) {
        try {
            String url = agentServiceUrl + "/api/v1/rag/documents/" + fileName + "/chunks";
            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    url, HttpMethod.GET, null,
                    new org.springframework.core.ParameterizedTypeReference<Map<String, Object>>() {}
            );
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> result = response.getBody();
                if (Integer.valueOf(200).equals(result.get("code"))) {
                    return CommonResult.success(result.get("data"));
                }
            }
            return CommonResult.failed("获取文档切片失败");
        } catch (Exception e) {
            LOGGER.error("获取 RAG 文档切片代理失败", e);
            return CommonResult.failed("获取文档切片失败: " + e.getMessage());
        }
    }
}
