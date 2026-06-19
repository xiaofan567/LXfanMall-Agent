import axios from 'axios'

// 创建 axios 实例 - mall-portal 后端 API (端口8085)
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
  paramsSerializer: {
    indexes: null, // 序列化数组为 ids=1&ids=2 而非 ids[]=1&ids[]=2（Spring @RequestParam 需要）
  },
})

// mall-search 搜索服务 (端口8081)
const searchApi = axios.create({
  baseURL: import.meta.env.VITE_SEARCH_API_BASE_URL || '/search-api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加 JWT token
const authInterceptor = (config: any) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}

api.interceptors.request.use(authInterceptor, (error) => Promise.reject(error))
searchApi.interceptors.request.use(authInterceptor, (error) => Promise.reject(error))

// 响应拦截器 - 统一处理 CommonResult 和错误
const responseInterceptor = (response: any) => {
  // mall 后端返回 CommonResult<T> 格式: { code, message, data }
  const res = response.data
  if (res.code === 200 || res.code === 0) {
    return res.data !== undefined ? res.data : res
  }
  // 业务错误
  console.error('API Error:', res.message || '未知错误')
  return Promise.reject(new Error(res.message || '请求失败'))
}

const errorInterceptor = (error: any) => {
  const { response } = error
  if (response) {
    switch (response.status) {
      case 401:
        localStorage.removeItem('token')
        localStorage.removeItem('user-storage')
        // 不在登录页才跳转
        if (window.location.pathname !== '/') {
          window.location.href = '/'
        }
        break
      case 403:
        console.error('权限不足')
        break
      case 404:
        console.error('资源不存在')
        break
      case 500:
        console.error('服务器错误')
        break
    }
  } else if (error.request) {
    console.error('网络连接失败，请检查后端服务是否启动')
  }
  return Promise.reject(error)
}

api.interceptors.response.use(responseInterceptor, errorInterceptor)
searchApi.interceptors.response.use(responseInterceptor, errorInterceptor)

// ==================== 用户认证 API (/sso) ====================
export const authApi = {
  /** 会员登录（后端用 @RequestParam） */
  login: (data: { username: string; password: string }) =>
    api.post('/sso/login', null, { params: data }),
  /** 会员注册（后端用 @RequestParam，必须传 params 而非 body） */
  register: (data: { username: string; password: string; telephone: string; authCode: string }) =>
    api.post('/sso/register', null, { params: data }),
  /** 获取短信验证码 */
  getAuthCode: (telephone: string) =>
    api.get('/sso/getAuthCode', { params: { telephone } }),
  /** 获取当前会员信息（需登录） */
  getMemberInfo: () =>
    api.get('/sso/info'),
  /** 修改密码（后端用 @RequestParam） */
  updatePassword: (data: { telephone: string; password: string; authCode: string }) =>
    api.post('/sso/updatePassword', null, { params: data }),
  /** 刷新 token */
  refreshToken: () =>
    api.get('/sso/refreshToken'),
}

// ==================== 首页 API (/home) ====================
export const homeApi = {
  /** 获取首页聚合内容（banner、品牌、新品、热品、专题） */
  getContent: () =>
    api.get('/home/content'),
  /** 推荐商品列表 */
  getRecommendProducts: (pageNum = 1, pageSize = 4) =>
    api.get('/home/recommendProductList', { params: { pageNum, pageSize } }),
  /** 热门商品 */
  getHotProducts: (pageNum = 1, pageSize = 6) =>
    api.get('/home/hotProductList', { params: { pageNum, pageSize } }),
  /** 新品上市 */
  getNewProducts: (pageNum = 1, pageSize = 6) =>
    api.get('/home/newProductList', { params: { pageNum, pageSize } }),
  /** 商品分类树 */
  getProductCateList: (parentId: number) =>
    api.get(`/home/productCateList/${parentId}`),
  /** 专题列表 */
  getSubjectList: (cateId?: number, pageNum = 1, pageSize = 4) =>
    api.get('/home/subjectList', { params: { cateId, pageNum, pageSize } }),
}

// ==================== 商品 API (/product) ====================
export const productApi = {
  /** 综合搜索/筛选/排序 */
  search: (params: {
    keyword?: string
    brandId?: number
    productCategoryId?: number
    pageNum?: number
    pageSize?: number
    sort?: number // 0=综合,1=新品,2=销量,3=价格升,4=价格降
  }) =>
    api.get('/product/search', { params }),
  /** 商品详情（前台） */
  getDetail: (id: number) =>
    api.get(`/product/detail/${id}`),
  /** 全部分类（树形结构） */
  getCategoryTree: () =>
    api.get('/product/categoryTreeList'),
}

// ==================== 品牌 API (/brand) ====================
export const brandApi = {
  /** 推荐品牌 */
  getRecommendList: (pageNum = 1, pageSize = 6) =>
    api.get('/brand/recommendList', { params: { pageNum, pageSize } }),
  /** 品牌详情 */
  getDetail: (brandId: number) =>
    api.get(`/brand/detail/${brandId}`),
  /** 品牌下的商品 */
  getProductList: (brandId: number, pageNum = 1, pageSize = 6) =>
    api.get('/brand/productList', { params: { brandId, pageNum, pageSize } }),
}

// ==================== 购物车 API (/cart) ====================
export const cartApi = {
  /** 添加商品到购物车 */
  add: (data: {
    productId: number
    productSkuId?: number
    quantity: number
  }) =>
    api.post('/cart/add', data),
  /** 获取购物车列表 */
  getList: () =>
    api.get('/cart/list'),
  /** 获取带促销信息的购物车 */
  getListPromotion: (cartIds?: number[]) =>
    api.get('/cart/list/promotion', { params: { cartIds: cartIds?.join(',') } }),
  /** 修改数量 */
  updateQuantity: (id: number, quantity: number) =>
    api.get('/cart/update/quantity', { params: { id, quantity } }),
  /** 获取商品 SKU 信息用于重选规格 */
  getCartProduct: (productId: number) =>
    api.get(`/cart/getProduct/${productId}`),
  /** 更新购物车商品规格 */
  updateAttr: (data: any) =>
    api.post('/cart/update/attr', data),
  /** 删除购物车商品（后端用 @RequestParam("ids") List<Long>） */
  remove: (ids: number[]) =>
    api.post('/cart/delete', null, { params: { ids } }),
  /** 清空购物车 */
  clear: () =>
    api.post('/cart/clear'),
}

// ==================== 订单 API (/order) ====================
export const orderApi = {
  /** 生成确认单（从购物车） */
  generateConfirmOrder: (cartIds: number[]) =>
    api.post('/order/generateConfirmOrder', cartIds),
  /** 提交订单 */
  generateOrder: (data: {
    cartIds: number[]
    memberReceiveAddressId: number
    couponId?: number
    useIntegration?: number
    payType?: number
  }) =>
    api.post('/order/generateOrder', data),
  /** 支付成功回调 */
  paySuccess: (orderId: number, payType: number) =>
    api.post('/order/paySuccess', null, { params: { orderId, payType } }),
  /** 订单列表 */
  getList: (params: {
    status?: number // -1=全部,0=待付款,1=待发货,2=已发货,3=已完成,4=已关闭
    pageNum?: number
    pageSize?: number
  }) =>
    api.get('/order/list', { params }),
  /** 订单详情 */
  getDetail: (orderId: number) =>
    api.get(`/order/detail/${orderId}`),
  /** 用户取消订单 */
  cancelOrder: (orderId: number) =>
    api.post('/order/cancelUserOrder', null, { params: { orderId } }),
  /** 确认收货 */
  confirmReceive: (orderId: number) =>
    api.post('/order/confirmReceiveOrder', null, { params: { orderId } }),
  /** 删除订单 */
  deleteOrder: (orderId: number) =>
    api.post('/order/deleteOrder', null, { params: { orderId } }),
  /** 获取订单物流详情 */
  getLogistics: (orderId: number) =>
    api.get(`/order/logistics/${orderId}`),
}

// ==================== 会员地址 API (/member/address) ====================
export const addressApi = {
  /** 地址列表 */
  getList: () =>
    api.get('/member/address/list'),
  /** 获取单个地址 */
  getDetail: (id: number) =>
    api.get(`/member/address/${id}`),
  /** 添加地址 */
  add: (data: any) =>
    api.post('/member/address/add', data),
  /** 更新地址 */
  update: (id: number, data: any) =>
    api.post(`/member/address/update/${id}`, data),
  /** 删除地址 */
  remove: (id: number) =>
    api.post(`/member/address/delete/${id}`),
}

// ==================== 会员优惠券 API (/member/coupon) ====================
export const couponApi = {
  /** 领取优惠券 */
  claim: (couponId: number) =>
    api.post(`/member/coupon/add/${couponId}`),
  /** 可用优惠券列表 */
  getAvailableList: () =>
    api.get('/member/coupon/list', { params: { useStatus: 0 } }),
  /** 优惠券领取历史 */
  getHistory: (useStatus?: number) =>
    api.get('/member/coupon/listHistory', { params: { useStatus } }),
  /** 购物车相关优惠券 */
  getCartCoupons: (type: number) => // 0=不可用,1=可用
    api.get(`/member/coupon/list/cart/${type}`),
  /** 商品可用优惠券 */
  getProductCoupons: (productId: number) =>
    api.get(`/member/coupon/listByProduct/${productId}`),
}

// ==================== 会员收藏 API (/member/productCollection) ====================
export const collectionApi = {
  /** 收藏商品 */
  add: (productId: number) =>
    api.post('/member/productCollection/add', { productId }),
  /** 取消收藏 */
  remove: (productId: number) =>
    api.post('/member/productCollection/delete', null, { params: { productId } }),
  /** 收藏列表 */
  getList: (pageNum = 1, pageSize = 5) =>
    api.get('/member/productCollection/list', { params: { pageNum, pageSize } }),
  /** 清空收藏 */
  clear: () =>
    api.post('/member/productCollection/clear'),
}

// ==================== 浏览历史 API (/member/readHistory) ====================
export const historyApi = {
  /** 创建浏览记录 */
  create: (data: { productId: number; productName: string; productPic: string; productPrice: string }) =>
    api.post('/member/readHistory/create', data),
  /** 浏览历史列表 */
  getList: (pageNum = 1, pageSize = 5) =>
    api.get('/member/readHistory/list', { params: { pageNum, pageSize } }),
  /** 删除浏览记录 */
  remove: (ids: string[]) =>
    api.post('/member/readHistory/delete', ids),
  /** 清空浏览记录 */
  clear: () =>
    api.post('/member/readHistory/clear'),
}

// ==================== 品牌关注 API (/member/attention) ====================
export const attentionApi = {
  /** 关注品牌 */
  add: (brandId: number) =>
    api.post('/member/attention/add', { brandId }),
  /** 取消关注 */
  remove: (brandId: number) =>
    api.post('/member/attention/delete', null, { params: { brandId } }),
  /** 关注列表 */
  getList: (pageNum = 1, pageSize = 5) =>
    api.get('/member/attention/list', { params: { pageNum, pageSize } }),
}

// ==================== 搜索 API (mall-search, /esProduct) ====================
export const searchApi_es = {
  /** 简单搜索 */
  searchSimple: (keyword: string, pageNum = 0, pageSize = 5) =>
    searchApi.get('/esProduct/search/simple', { params: { keyword, pageNum, pageSize } }),
  /** 综合搜索（支持筛选、排序） */
  search: (params: {
    keyword?: string
    brandId?: number
    productCategoryId?: number
    pageNum?: number
    pageSize?: number
    sort?: number // 0=相关度,1=新品,2=销量,3=价格升,4=价格降
  }) =>
    searchApi.get('/esProduct/search', { params }),
  /** 根据商品ID推荐相关商品 */
  recommend: (id: number, pageNum = 0, pageSize = 5) =>
    searchApi.get(`/esProduct/recommend/${id}`, { params: { pageNum, pageSize } }),
  /** 获取搜索关联的品牌、分类、属性 */
  getRelatedInfo: (keyword: string) =>
    searchApi.get('/esProduct/search/relate', { params: { keyword } }),
}

// ==================== 商品评价 API (/comment) ====================
export const commentApi = {
  /** 分页获取商品评价 */
  getList: (productId: number, pageNum = 1, pageSize = 10) =>
    api.get('/comment/list', { params: { productId, pageNum, pageSize } }),
  /** 获取商品评价数量 */
  getCount: (productId: number) =>
    api.get('/comment/count', { params: { productId } }),
  /** 创建商品评价 */
  create: (data: {
    orderId: number
    orderItemId: number
    productId: number
    star: number
    content: string
    pics?: string
    productAttribute?: string
  }) =>
    api.post('/comment/create', data),
  /** 获取当前会员的评价列表 */
  listByMember: (pageNum = 1, pageSize = 10) =>
    api.get('/comment/listByMember', { params: { pageNum, pageSize } }),
}

// ==================== 退货 API (/returnApply) ====================
export const returnApi = {
  /** 提交退货申请 */
  create: (data: any) =>
    api.post('/returnApply/create', data),
  /** 获取会员退货申请列表 */
  getList: (memberUsername: string) =>
    api.get('/returnApply/list', { params: { memberUsername } }),
  /** 获取退货申请详情 */
  getDetail: (id: number) =>
    api.get(`/returnApply/${id}`),
}

// ==================== 支付宝 API (/alipay) ====================
export const alipayApi = {
  /** PC网站支付 */
  pay: (outTradeNo: string, subject: string, totalAmount: string, body?: string) =>
    api.get('/alipay/pay', { params: { outTradeNo, subject, totalAmount, body } }),
  /** 查询支付结果 */
  query: (outTradeNo?: string, tradeNo?: string) =>
    api.get('/alipay/query', { params: { outTradeNo, tradeNo } }),
}

// ==================== AI Agent API (agent-service, :8000) ====================

// 独立 Axios 实例 — 不走 CommonResult 拦截器，Agent 直接返回 { reply, intent }
const agentAxios = axios.create({
  baseURL: import.meta.env.VITE_AGENT_API_BASE_URL || '/agent-api',
  timeout: 30000, // LLM 调用耗时较长
  headers: {
    'Content-Type': 'application/json',
  },
})

// 复用 JWT token 拦截器
agentAxios.interceptors.request.use(authInterceptor, (error) => Promise.reject(error))

// Agent 错误拦截器（简化版，不做 401 跳转）
agentAxios.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      console.error('Agent API Error:', error.response.status, error.response.data)
    } else {
      console.error('Agent 服务连接失败，请检查 agent-service 是否启动')
    }
    return Promise.reject(error)
  },
)

export const agentApi = {
  // /** 向 AI Agent 发送消息（非流式） — 已禁用，只用流式 */
  // chat: (message: string, sessionId: string): Promise<{ reply: string; intent?: string }> =>
  //   agentAxios.post('/api/v1/chat', { message, session_id: sessionId }),

  /** 向 AI Agent 发送消息（SSE 流式），返回 ReadableStream reader */
  chatStream: async (message: string, sessionId: string) => {
    const baseURL = import.meta.env.VITE_AGENT_API_BASE_URL || '/agent-api'
    const token = localStorage.getItem('token')
    const res = await fetch(`${baseURL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, session_id: sessionId }),
    })
    if (!res.ok) {
      throw new Error(`Agent stream error: ${res.status}`)
    }
    return res.body!
  },

  /** 获取当前用户最近活跃的 session_id（登录用户） */
  getLatestSession: async (): Promise<string | null> => {
    const baseURL = import.meta.env.VITE_AGENT_API_BASE_URL || '/agent-api'
    const token = localStorage.getItem('token')
    const res = await fetch(`${baseURL}/api/v1/chat/latest-session`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })
    if (!res.ok) return null
    const json = await res.json()
    return json.data?.session_id || null
  },

  /** 获取会话历史（刷新后恢复对话） */
  getHistory: async (sessionId: string): Promise<{ role: string; content: string; timestamp?: string; tool_results?: { tool: string; data: unknown }[] }[]> => {
    const baseURL = import.meta.env.VITE_AGENT_API_BASE_URL || '/agent-api'
    const token = localStorage.getItem('token')
    const res = await fetch(
      `${baseURL}/api/v1/chat/history?session_id=${encodeURIComponent(sessionId)}`,
      {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      },
    )
    if (!res.ok) return []
    const json = await res.json()
    return json.data || []
  },

  /** 清空会话历史 */
  clearHistory: async (sessionId: string): Promise<void> => {
    const baseURL = import.meta.env.VITE_AGENT_API_BASE_URL || '/agent-api'
    const token = localStorage.getItem('token')
    await fetch(
      `${baseURL}/api/v1/chat/history?session_id=${encodeURIComponent(sessionId)}`,
      {
        method: 'DELETE',
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      },
    )
  },
}

export default api
