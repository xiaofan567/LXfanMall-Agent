import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router";
import {
  X,
  Send,
  Minus,
  Bot,
  Package,
  MessageSquare,
  ChevronRight,
  MapPin,
  Truck,
  CheckCircle2,
  Circle,
  Trash2,
} from "lucide-react";
import { agentApi } from "@/utils/api";

// ── 结构化数据接口（对齐后端 ChatResponse） ──

interface ProductCard {
  id: number;
  name: string;
  price: number;
  original_price?: number;
  image?: string;
  rating?: number;
  reason?: string;
}

interface OrderCard {
  order_id: number;
  order_sn: string;
  product_name: string;
  product_image?: string;
  total_amount: number;
  status: number;
  status_text: string;
  create_time?: string;
}

interface AddressCard {
  id: number;
  name: string;
  phone: string;
  address: string;
  is_default?: boolean;
}

interface TraceItem {
  traceTime: string;
  location: string;
  statusText: string;
  statusCode: number;
}

interface LogisticsCard {
  deliveryCompany: string;
  deliverySn: string;
  receiverName: string;
  receiverPhone: string;
  receiverAddress: string;
  traceList: TraceItem[];
}

interface UnreviewedItem {
  order_id: number;
  order_sn: string;
  item_id: number;
  product_id: number;
  product_name: string;
  product_pic?: string;
  product_price: number;
  product_attr?: string;
}

// ── 消息接口 ──

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  products?: ProductCard[];
  orders?: OrderCard[];
  addresses?: AddressCard[];
  logistics?: LogisticsCard[];
  unreviewed?: UnreviewedItem[];
}

// ── 工具结果解析 ──

interface ToolResult {
  tool: string;
  data: unknown;
}

function parseToolResults(toolResults: ToolResult[]): {
  products: ProductCard[];
  orders: OrderCard[];
  addresses: AddressCard[];
  logistics: LogisticsCard[];
  unreviewed: UnreviewedItem[];
} {
  const products: ProductCard[] = [];
  const orders: OrderCard[] = [];
  const addresses: AddressCard[] = [];
  const logistics: LogisticsCard[] = [];
  const unreviewed: UnreviewedItem[] = [];

  for (const item of toolResults) {
    const { tool, data } = item;

    if (
      (tool === "search_products" || tool === "get_recommendations") &&
      Array.isArray(data)
    ) {
      for (const p of data) {
        products.push({
          id: p.id ?? 0,
          name: p.name ?? "",
          price: p.price ?? 0,
          original_price: p.originalPrice,
          image: p.pic,
          sale: p.sale,
        } as unknown as ProductCard);
      }
    } else if (tool === "get_product_info" && data && typeof data === "object") {
      const product = (data as Record<string, unknown>).product ?? data;
      const p = product as Record<string, unknown>;
      products.push({
        id: p.id ?? 0,
        name: p.name ?? "",
        price: p.price ?? 0,
        original_price: p.originalPrice,
        image: p.pic,
      } as ProductCard);
    } else if (tool === "get_user_orders" && Array.isArray(data)) {
      const statusMap: Record<number, string> = {
        0: "待付款",
        1: "待发货",
        2: "已发货",
        3: "已完成",
        4: "已关闭",
        5: "无效",
      };
      for (const o of data) {
        const items = o.orderItemList ?? [];
        // 跳过无效订单（无商品项或无订单号）
        if (!items.length || !o.orderSn) continue;
        orders.push({
          order_id: o.id ?? 0,
          order_sn: o.orderSn ?? "",
          product_name: items[0]?.productName ?? "未知商品",
          product_image: items[0]?.productPic,
          total_amount: o.totalAmount ?? 0,
          status: o.status ?? -1,
          status_text: statusMap[o.status ?? -1] ?? "未知",
          create_time: o.createTime,
        });
      }
    } else if (tool === "get_order_detail" && data && typeof data === "object") {
      const o = data as Record<string, unknown>;
      const items = (o.orderItemList as unknown[]) ?? [];
      if (!items.length) {
        // 跳过无商品项的无效订单详情
      } else {
        const statusMap: Record<number, string> = {
          0: "待付款",
          1: "待发货",
          2: "已发货",
          3: "已完成",
          4: "已关闭",
          5: "无效",
        };
        orders.push({
          order_id: (o.id as number) ?? 0,
          order_sn: (o.orderSn as string) ?? "",
          product_name: ((items[0] as Record<string, unknown>)?.productName as string) ?? "未知商品",
          product_image: (items[0] as Record<string, unknown>)?.productPic as string | undefined,
          total_amount: (o.totalAmount as number) ?? 0,
          status: (o.status as number) ?? -1,
          status_text: statusMap[(o.status as number) ?? -1] ?? "未知",
          create_time: o.createTime as string | undefined,
        });
      }
    } else if (tool === "get_addresses" && Array.isArray(data)) {
      for (const a of data) {
        const province = a.province ?? "";
        const city = a.city ?? "";
        const region = a.region ?? "";
        const detail = a.detailAddress ?? "";
        addresses.push({
          id: a.id ?? 0,
          name: a.name ?? "",
          phone: a.phoneNumber ?? "",
          address: `${province}${city}${region}${detail}`,
          is_default: a.defaultStatus === 1,
        });
      }
    } else if (tool === "get_logistics" && data && typeof data === "object") {
      const d = data as Record<string, unknown>;
      const traceList = (d.traceList as TraceItem[]) ?? [];
      logistics.push({
        deliveryCompany: (d.deliveryCompany as string) ?? "未知快递",
        deliverySn: (d.deliverySn as string) ?? "",
        receiverName: (d.receiverName as string) ?? "",
        receiverPhone: (d.receiverPhone as string) ?? "",
        receiverAddress: (d.receiverAddress as string) ?? "",
        traceList: traceList,
      });
    } else if (tool === "check_unreviewed_products" && Array.isArray(data)) {
      for (const order of data) {
        const items = order.items ?? [];
        for (const item of items) {
          unreviewed.push({
            order_id: order.order_id ?? 0,
            order_sn: order.order_sn ?? "",
            item_id: item.item_id ?? 0,
            product_id: item.product_id ?? 0,
            product_name: item.product_name ?? "",
            product_pic: item.product_pic,
            product_price: item.product_price ?? 0,
            product_attr: item.product_attr,
          });
        }
      }
    }
  }

  return { products, orders, addresses, logistics, unreviewed };
}

// ── 快捷问题 ──

const QUICK_QUESTIONS = [
  "推荐热门商品",
  "查询我的订单",
  "物流到哪了？",
  "有什么优惠活动",
  "申请售后",
];

// ── 状态标签颜色 ──

function getStatusColor(status: number): string {
  switch (status) {
    case 0:
      return "bg-orange-50 text-orange-600"; // 待付款
    case 1:
      return "bg-yellow-50 text-yellow-600"; // 待发货
    case 2:
      return "bg-blue-50 text-blue-600"; // 已发货
    case 3:
      return "bg-green-50 text-green-600"; // 已完成
    case 4:
      return "bg-gray-50 text-gray-500"; // 已关闭
    default:
      return "bg-gray-50 text-gray-500";
  }
}

// ── 组件 ──

export function AIFloatingBall() {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isPulsing, setIsPulsing] = useState(true);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "👋 您好！我是 LXfanMall AI 智能助手 **小L**！\n\n我能帮您推荐商品、查询订单、追踪物流，快来试试吧！",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const sessionIdRef = useRef<string>(
    localStorage.getItem("ai_session_id") || crypto.randomUUID(),
  );

  // 持久化 session_id 到 localStorage，刷新页面后恢复对话历史
  useEffect(() => {
    localStorage.setItem("ai_session_id", sessionIdRef.current);
  }, []);

  // 组件挂载时：登录用户优先用 latest session，匿名用 localStorage 的 uuid
  useEffect(() => {
    const initSession = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          const latestId = await agentApi.getLatestSession();
          if (latestId) {
            sessionIdRef.current = latestId;
            localStorage.setItem("ai_session_id", latestId);
          }
        } catch {
          // 接口失败时 fallback 到 localStorage 的 uuid
        }
      }
      // 加载历史对话
      const loadHistory = async () => {
        try {
          const history = await agentApi.getHistory(sessionIdRef.current);
          if (history.length === 0) return;

          const restored: Message[] = [
            {
              id: "welcome",
              role: "assistant",
              content:
                "👋 您好！我是 LXfanMall AI 智能助手 **小L**！\n\n我能帮您推荐商品、查询订单、追踪物流，快来试试吧！",
              timestamp: new Date(),
            },
            ...history.map((msg, i) => {
              const base = {
                id: `restored-${i}`,
                role: msg.role === "user" ? ("user" as const) : ("assistant" as const),
                content: msg.content,
                timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
              };
              // 解析 tool_results 恢复卡片组件
              if (msg.role === "assistant" && msg.tool_results && msg.tool_results.length > 0) {
                const { products, orders, addresses, logistics, unreviewed } = parseToolResults(msg.tool_results);
                return {
                  ...base,
                  products: products.length ? products : undefined,
                  orders: orders.length ? orders : undefined,
                  addresses: addresses.length ? addresses : undefined,
                  logistics: logistics.length ? logistics : undefined,
                  unreviewed: unreviewed.length ? unreviewed : undefined,
                };
              }
              return base;
            }),
          ];
          setMessages(restored);
        } catch {
          // 拉取失败不影响正常使用
        }
      };
      await loadHistory();
    };
    initSession();
  }, []);

  useEffect(() => {
    if (isOpen && !isMinimized) {
      messagesEndRef.current?.scrollIntoView();
    }
  }, [messages, isOpen, isMinimized]);

  useEffect(() => {
    const timer = setTimeout(() => setIsPulsing(false), 5000);
    return () => clearTimeout(timer);
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      const userMsg: Message = {
        id: Date.now().toString(),
        role: "user",
        content: text.trim(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInput("");

      // 占位 AI 消息（loading 态）
      const aiMsgId = (Date.now() + 1).toString();
      const placeholder: Message = {
        id: aiMsgId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, placeholder]);

      try {
        const stream = await agentApi.chatStream(text.trim(), sessionIdRef.current);
        const reader = stream.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let accumulated = "";
        let doneReply = "";
        let toolResults: ToolResult[] = [];
        let rafId = 0;

        const flushUI = () => {
          rafId = 0;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId ? { ...m, content: accumulated } : m
            )
          );
          requestAnimationFrame(() => {
            messagesEndRef.current?.scrollIntoView();
          });
        };
        const scheduleFlush = () => {
          if (!rafId) {
            rafId = requestAnimationFrame(flushUI);
          }
        };

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const data = JSON.parse(line.slice(6));
              if (data.token) {
                accumulated += data.token;
                scheduleFlush();
              }
              if (data.done) {
                if (data.reply) doneReply = data.reply;
                if (data.tool_results) toolResults = data.tool_results;
              }
            } catch {
              /* 忽略解析错误 */
            }
          }
        }

        // 处理 buffer 中残留的最后一条消息
        if (buffer.startsWith("data: ")) {
          try {
            const data = JSON.parse(buffer.slice(6));
            if (data.token) {
              accumulated += data.token;
            }
            if (data.done) {
              if (data.reply) doneReply = data.reply;
              if (data.tool_results) toolResults = data.tool_results;
            }
          } catch {
            /* 忽略解析错误 */
          }
        }

        if (rafId) cancelAnimationFrame(rafId);

        // 优先用累积 token，没有则用 done.reply
        // 注释掉非流式回退，避免 Agent 被执行两次
        if (!accumulated && doneReply) {
          accumulated = doneReply;
        } else if (!accumulated && !doneReply) {
          accumulated = "抱歉，暂时无法处理您的请求。";
        }

        // 解析工具结果为结构化数据
        const { products, orders, addresses, logistics, unreviewed } = parseToolResults(toolResults);

        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsgId
              ? {
                  ...m,
                  content: accumulated,
                  products: products.length ? products : undefined,
                  orders: orders.length ? orders : undefined,
                  addresses: addresses.length ? addresses : undefined,
                  logistics: logistics.length ? logistics : undefined,
                  unreviewed: unreviewed.length ? unreviewed : undefined,
                }
              : m
          )
        );
        requestAnimationFrame(() => {
          messagesEndRef.current?.scrollIntoView();
        });
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsgId
              ? { ...m, content: "网络开小差了，请稍后再试～" }
              : m
          )
        );
      }
    },
    []
  );

  const handleQuickQuestion = useCallback(
    (question: string) => {
      if (!isOpen) {
        setIsOpen(true);
        setIsMinimized(false);
      }
      setTimeout(() => sendMessage(question), 100);
    },
    [isOpen, sendMessage],
  );

  const handleClearChat = useCallback(async () => {
    // 清空后端 session
    await agentApi.clearHistory(sessionIdRef.current);
    // 生成新 session_id，断开与旧 session 的关联
    const newId = crypto.randomUUID();
    sessionIdRef.current = newId;
    localStorage.setItem("ai_session_id", newId);
    // 重置为欢迎消息
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content:
          "👋 您好！我是 LXfanMall AI 智能助手 **小L**！\n\n我能帮您推荐商品、查询订单、追踪物流，快来试试吧！",
        timestamp: new Date(),
      },
    ]);
  }, []);

  const formatContent = (content: string) => {
    return content.split("\n").map((line, i) => {
      const boldProcessed = line.split(/\*\*(.*?)\*\*/g).map((part, j) =>
        j % 2 === 1 ? (
          <strong key={j} className="font-semibold">
            {part}
          </strong>
        ) : (
          part
        )
      );
      return (
        <span key={i}>
          {boldProcessed}
          {i < content.split("\n").length - 1 && <br />}
        </span>
      );
    });
  };

  return (
    <div className="fixed right-6 bottom-8 z-50 flex flex-col items-end gap-3">
      {/* Chat panel */}
      {isOpen && (
        <div
          className={`bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden transition-all duration-300 ease-in-out ${
            isMinimized ? "h-14 w-80" : "h-[560px] w-[380px]"
          }`}
          style={{
            animation: "slideUpFade 0.25s ease",
          }}
        >
          {/* Chat header */}
          <div className="bg-gradient-to-r from-[#e02020] to-[#ff4444] px-4 py-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
              <div>
                <div className="text-white font-semibold text-sm">小L AI 智能客服</div>
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-white/80 text-xs">在线服务中</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleClearChat}
                title="清除对话记录"
                className="w-6 h-6 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center text-white transition-colors"
              >
                <Trash2 size={12} />
              </button>
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="w-6 h-6 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center text-white transition-colors"
              >
                <Minus size={12} />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="w-6 h-6 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center text-white transition-colors"
              >
                <X size={12} />
              </button>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* Quick questions */}
              <div className="px-3 py-2 bg-gray-50 border-b border-gray-100 flex gap-1.5 overflow-x-auto shrink-0 no-scrollbar">
                {QUICK_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleQuickQuestion(q)}
                    className="whitespace-nowrap text-xs bg-white border border-gray-200 text-gray-600 hover:border-[#e02020] hover:text-[#e02020] px-2.5 py-1 rounded-full transition-colors shrink-0"
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50/50">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] flex flex-col gap-2 ${
                        msg.role === "user" ? "items-end" : "items-start"
                      }`}
                    >
                      {/* Avatar for assistant */}
                      {msg.role === "assistant" && (
                        <div className="flex items-center gap-1.5 mb-0.5">
                          <div className="w-6 h-6 bg-[#e02020] rounded-full flex items-center justify-center">
                            <Bot size={12} className="text-white" />
                          </div>
                          <span className="text-xs text-gray-400">小L</span>
                        </div>
                      )}

                      {/* Message bubble */}
                      <div
                        className={`px-3 py-2.5 rounded-2xl text-sm leading-relaxed ${
                          msg.role === "user"
                            ? "bg-[#e02020] text-white rounded-tr-sm"
                            : "bg-white text-gray-700 shadow-sm border border-gray-100 rounded-tl-sm"
                        }`}
                      >
                        {msg.role === "assistant" && msg.content === "" ? (
                          <div className="flex gap-1 py-0.5">
                            {[0, 1, 2].map((i) => (
                              <div
                                key={i}
                                className="w-1.5 h-1.5 bg-gray-400 rounded-full"
                                style={{
                                  animation: `bounce 1s infinite ${i * 0.15}s`,
                                }}
                              />
                            ))}
                          </div>
                        ) : (
                          formatContent(msg.content)
                        )}
                      </div>

                      {/* ── 商品卡片 ── */}
                      {msg.products && msg.products.length > 0 && (
                        <div className="w-full space-y-2">
                          {msg.products.map((product) => (
                            <div
                              key={product.id}
                              onClick={() => {
                                navigate(`/product/${product.id}`);
                                setIsOpen(false);
                              }}
                              className="bg-white border border-gray-100 rounded-xl p-2.5 flex gap-2.5 shadow-sm hover:shadow-md hover:border-red-200 transition-all cursor-pointer group"
                            >
                              {product.image ? (
                                <img
                                  src={product.image}
                                  alt={product.name}
                                  className="w-14 h-14 object-cover rounded-lg shrink-0 group-hover:scale-105 transition-transform"
                                />
                              ) : (
                                <div className="w-14 h-14 bg-gray-100 rounded-lg shrink-0 flex items-center justify-center">
                                  <Package size={20} className="text-gray-300" />
                                </div>
                              )}
                              <div className="flex-1 min-w-0">
                                <div className="text-xs text-gray-700 line-clamp-2 mb-1">
                                  {product.name}
                                </div>
                                {product.reason && (
                                  <div className="text-[10px] text-orange-500 mb-1">
                                    {product.reason}
                                  </div>
                                )}
                                <div className="flex items-center justify-between">
                                  <div className="flex items-baseline gap-1">
                                    <span className="text-[#e02020] font-bold text-sm">
                                      ¥{product.price.toLocaleString()}
                                    </span>
                                    {product.original_price &&
                                      product.original_price > product.price && (
                                        <span className="text-gray-400 text-xs line-through">
                                          ¥{product.original_price.toLocaleString()}
                                        </span>
                                      )}
                                  </div>
                                  <span className="flex items-center gap-0.5 text-[#e02020] text-[10px] font-medium">
                                    查看
                                    <ChevronRight size={10} />
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* ── 订单卡片 ── */}
                      {msg.orders && msg.orders.length > 0 && (
                        <div className="w-full space-y-2">
                          {msg.orders.map((order) => (
                            <div
                              key={order.order_id}
                              onClick={() => {
                                navigate("/orders");
                                setIsOpen(false);
                              }}
                              className="bg-white border border-gray-100 rounded-xl p-3 shadow-sm w-full hover:shadow-md hover:border-red-200 transition-all cursor-pointer"
                            >
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-1.5">
                                  <Package size={13} className="text-[#e02020]" />
                                  <span className="text-xs font-semibold text-gray-700">
                                    订单 #{order.order_sn}
                                  </span>
                                </div>
                                <span
                                  className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(order.status)}`}
                                >
                                  {order.status_text}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 mb-2">
                                {order.product_image && (
                                  <img
                                    src={order.product_image}
                                    alt={order.product_name}
                                    className="w-10 h-10 object-cover rounded-lg"
                                  />
                                )}
                                <div className="flex-1 min-w-0">
                                  <div className="text-xs text-gray-600 truncate">
                                    {order.product_name}
                                  </div>
                                  <div className="text-[#e02020] font-bold text-sm">
                                    ¥{order.total_amount.toLocaleString()}
                                  </div>
                                </div>
                              </div>
                              {order.create_time && (
                                <div className="text-[10px] text-gray-400">
                                  下单时间：{order.create_time}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* ── 地址卡片 ── */}
                      {msg.addresses && msg.addresses.length > 0 && (
                        <div className="w-full space-y-2">
                          {msg.addresses.map((addr) => (
                            <div
                              key={addr.id}
                              className="bg-white border border-gray-100 rounded-xl p-3 shadow-sm w-full"
                            >
                              <div className="flex items-center gap-1.5 mb-1">
                                <MapPin size={12} className="text-[#e02020]" />
                                <span className="text-xs font-semibold text-gray-700">
                                  {addr.name}
                                </span>
                                <span className="text-xs text-gray-400">{addr.phone}</span>
                                {addr.is_default && (
                                  <span className="text-[10px] bg-red-50 text-[#e02020] px-1.5 py-0.5 rounded-full">
                                    默认
                                  </span>
                                )}
                              </div>
                              <div className="text-xs text-gray-500">{addr.address}</div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* ── 物流卡片 ── */}
                      {msg.logistics && msg.logistics.length > 0 && (
                        <div className="w-full space-y-2">
                          {msg.logistics.map((log, idx) => (
                            <div
                              key={idx}
                              className="bg-white border border-gray-100 rounded-xl shadow-sm w-full overflow-hidden"
                            >
                              {/* 物流头部信息 */}
                              <div className="bg-gray-50 px-3 py-2.5 border-b border-gray-100">
                                <div className="flex items-center gap-2 mb-1.5">
                                  <Truck size={14} className="text-[#e02020]" />
                                  <span className="text-xs font-semibold text-gray-700">
                                    {log.deliveryCompany}
                                  </span>
                                  <span className="text-[10px] text-gray-400">
                                    {log.deliverySn}
                                  </span>
                                </div>
                                {log.receiverName && (
                                  <div className="flex items-start gap-1.5 text-[10px] text-gray-500">
                                    <MapPin size={10} className="mt-0.5 shrink-0" />
                                    <span>
                                      收件人：{log.receiverName} {log.receiverPhone}
                                      <br />
                                      {log.receiverAddress}
                                    </span>
                                  </div>
                                )}
                              </div>

                              {/* 物流轨迹 */}
                              <div className="px-3 py-3">
                                {log.traceList.length > 0 ? (
                                  <div className="relative pl-6">
                                    {/* 竖线 */}
                                    <div className="absolute left-[7px] top-1.5 bottom-1.5 w-0.5 bg-gray-200" />

                                    {log.traceList.map((trace, index) => {
                                      const isLast = index === log.traceList.length - 1;
                                      const isSigned = trace.statusCode === 10;

                                      return (
                                        <div
                                          key={index}
                                          className={`relative pb-3 last:pb-0 ${
                                            !isLast ? "opacity-60" : ""
                                          }`}
                                        >
                                          {/* 时间轴圆点 */}
                                          <div className="absolute -left-6 top-0.5">
                                            {isLast && isSigned ? (
                                              <CheckCircle2
                                                size={16}
                                                className="text-green-500 fill-green-500"
                                              />
                                            ) : isLast ? (
                                              <div
                                                className="w-[10px] h-[10px] bg-[#e02020] border-2 border-white rounded-full"
                                                style={{
                                                  boxShadow: "0 0 0 2px #e02020",
                                                }}
                                              />
                                            ) : (
                                              <Circle
                                                size={10}
                                                className="text-gray-300 fill-white"
                                              />
                                            )}
                                          </div>

                                          {/* 内容 */}
                                          <div>
                                            <p
                                              className={`text-[11px] leading-tight ${
                                                isLast
                                                  ? isSigned
                                                    ? "text-green-600 font-medium"
                                                    : "text-[#e02020] font-medium"
                                                  : "text-gray-500"
                                              }`}
                                            >
                                              {trace.statusText}
                                            </p>
                                            <div className="flex items-center gap-1.5 mt-0.5">
                                              {trace.location && (
                                                <span className="text-[9px] text-gray-400">
                                                  {trace.location}
                                                </span>
                                              )}
                                              {trace.traceTime && (
                                                <span className="text-[9px] text-gray-400">
                                                  {trace.traceTime
                                                    ?.replace("T", " ")
                                                    .substring(0, 16)}
                                                </span>
                                              )}
                                            </div>
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                ) : (
                                  <div className="text-center py-4 text-gray-400">
                                    <Package
                                      size={24}
                                      className="mx-auto mb-1 text-gray-300"
                                    />
                                    <p className="text-xs">暂无物流信息</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* ── 未评价商品卡片 ── */}
                      {msg.unreviewed && msg.unreviewed.length > 0 && (
                        <div className="w-full space-y-2">
                          {msg.unreviewed.map((item) => (
                            <div
                              key={`${item.order_id}-${item.item_id}`}
                              onClick={() => {
                                navigate("/orders");
                                setIsOpen(false);
                              }}
                              className="bg-white border border-gray-100 rounded-xl p-3 shadow-sm w-full hover:shadow-md hover:border-red-200 transition-all cursor-pointer"
                            >
                              <div className="flex items-center gap-2">
                                {item.product_pic && (
                                  <img
                                    src={item.product_pic}
                                    alt={item.product_name}
                                    className="w-14 h-14 object-cover rounded-lg shrink-0"
                                  />
                                )}
                                <div className="flex-1 min-w-0">
                                  <div className="text-xs font-semibold text-gray-700 truncate">
                                    {item.product_name}
                                  </div>
                                  {item.product_attr && (
                                    <div className="text-[10px] text-gray-400 mt-0.5 truncate">
                                      {item.product_attr}
                                    </div>
                                  )}
                                  <div className="flex items-center justify-between mt-1">
                                    <span className="text-[#e02020] font-bold text-sm">
                                      ¥{item.product_price.toLocaleString()}
                                    </span>
                                    <span className="text-[10px] bg-orange-50 text-orange-500 px-2 py-0.5 rounded-full">
                                      待评价
                                    </span>
                                  </div>
                                  <div className="text-[10px] text-gray-400 mt-0.5">
                                    订单号：{item.order_sn}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      <span className="text-[10px] text-gray-300">
                        {msg.timestamp.toLocaleTimeString("zh-CN", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </div>
                ))}

                <div ref={messagesEndRef} />
              </div>

              {/* Input area */}
              <div className="border-t border-gray-100 p-3 bg-white shrink-0">
                <div className="flex items-center gap-2 bg-gray-50 rounded-full px-4 py-2.5 border border-gray-200 focus-within:border-[#e02020] transition-colors">
                  <MessageSquare size={14} className="text-gray-400 shrink-0" />
                  <input
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
                    placeholder="输入您的问题..."
                    className="flex-1 bg-transparent text-sm outline-none text-gray-700 placeholder-gray-400"
                  />
                  <button
                    onClick={() => sendMessage(input)}
                    disabled={!input.trim()}
                    className={`w-7 h-7 rounded-full flex items-center justify-center transition-all ${
                      input.trim()
                        ? "bg-[#e02020] text-white hover:bg-[#c01010] hover:scale-110"
                        : "bg-gray-200 text-gray-400 cursor-not-allowed"
                    }`}
                  >
                    <Send size={12} />
                  </button>
                </div>
                <div className="text-center mt-2">
                  <span className="text-[10px] text-gray-400">AI 智能客服 · 仅供参考</span>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Floating ball */}
      <div className="relative">
        {/* Notification badge */}
        {!isOpen && (
          <div className="absolute -top-1 -right-1 z-10">
            <span className="flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-4 w-4 bg-yellow-400 items-center justify-center">
                <span className="text-[9px] text-red-800 font-black">1</span>
              </span>
            </span>
          </div>
        )}

        <button
          onClick={() => {
            setIsOpen(!isOpen);
            setIsMinimized(false);
          }}
          className={`relative w-14 h-14 rounded-full shadow-2xl flex items-center justify-center transition-all duration-300 ${
            isOpen
              ? "bg-gray-600 hover:bg-gray-700 rotate-0"
              : "bg-gradient-to-br from-[#e02020] to-[#ff4444] hover:from-[#c01010] hover:to-[#e03030] hover:scale-110"
          } ${isPulsing && !isOpen ? "animate-pulse" : ""}`}
          title="AI 智能客服"
        >
          {isOpen ? (
            <X size={20} className="text-white" />
          ) : (
            <div className="flex flex-col items-center">
              <Bot size={20} className="text-white" />
              <span className="text-white text-[8px] mt-0.5 font-medium">AI客服</span>
            </div>
          )}

          {/* Ripple effect */}
          {!isOpen && (
            <>
              <span className="absolute inset-0 rounded-full bg-[#e02020] animate-ping opacity-25" />
              <span className="absolute inset-0 rounded-full bg-[#e02020] animate-ping opacity-15 animation-delay-300" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
