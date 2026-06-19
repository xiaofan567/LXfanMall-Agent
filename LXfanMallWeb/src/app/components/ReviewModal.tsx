import { Star, X, Loader2, ImagePlus } from "lucide-react"
import { useState } from "react"
import { commentApi } from "@/utils/api"
import { toast } from "sonner"

interface ReviewItem {
  orderItemId: number
  productId: number
  productName: string
  productPic: string
  productPrice: string
  productQuantity: number
  productAttribute?: string
}

interface ReviewModalProps {
  orderId: number
  items: ReviewItem[]
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

export function ReviewModal({ orderId, items, open, onClose, onSuccess }: ReviewModalProps) {
  const [reviews, setReviews] = useState<Record<number, { star: number; content: string; pics: string }>>({})
  const [submitting, setSubmitting] = useState(false)
  const [currentItemIndex, setCurrentItemIndex] = useState(0)

  const currentItem = items[currentItemIndex]
  const currentReview = reviews[currentItem?.orderItemId] || { star: 5, content: "", pics: "" }

  if (!open) return null

  const updateCurrentReview = (updates: Partial<{ star: number; content: string; pics: string }>) => {
    setReviews((prev) => ({
      ...prev,
      [currentItem.orderItemId]: {
        ...(prev[currentItem.orderItemId] || { star: 5, content: "", pics: "" }),
        ...updates,
      },
    }))
  }

  const handleSubmitAll = async () => {
    // 检查是否所有商品都已评价
    for (const item of items) {
      const r = reviews[item.orderItemId]
      if (!r || !r.content?.trim()) {
        toast.error(`请为「${item.productName}」填写评价内容`)
        return
      }
    }

    setSubmitting(true)
    try {
      for (const item of items) {
        const r = reviews[item.orderItemId] || { star: 5, content: "", pics: "" }
        await commentApi.create({
          orderId,
          orderItemId: item.orderItemId,
          productId: item.productId,
          star: r.star,
          content: r.content,
          pics: r.pics || undefined,
          productAttribute: item.productAttribute || undefined,
        })
      }
      toast.success("评价成功！")
      onSuccess()
      onClose()
      setReviews({})
      setCurrentItemIndex(0)
    } catch {
      toast.error("评价提交失败，请重试")
    } finally {
      setSubmitting(false)
    }
  }

  const isAllReviewed = items.every((item) => {
    const r = reviews[item.orderItemId]
    return r && r.content?.trim().length > 0
  })

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-900">发表评价</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg transition-colors">
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        {items.length > 1 && (
          <div className="flex gap-2 px-6 pt-4">
            {items.map((item, idx) => {
              const reviewed = reviews[item.orderItemId]?.content?.trim().length > 0
              return (
                <button
                  key={item.orderItemId}
                  onClick={() => setCurrentItemIndex(idx)}
                  className={`w-12 h-12 rounded-lg border-2 overflow-hidden flex-shrink-0 ${
                    idx === currentItemIndex ? "border-[#e02020]" : reviewed ? "border-green-400" : "border-gray-200"
                  }`}
                >
                  <img src={item.productPic || ""} alt="" className="w-full h-full object-cover" />
                </button>
              )
            })}
          </div>
        )}

        {/* Current item review */}
        {currentItem && (
          <div className="px-6 py-4">
            {/* Product info */}
            <div className="flex items-center gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
              <img src={currentItem.productPic || ""} alt={currentItem.productName}
                className="w-16 h-16 rounded-lg object-cover bg-gray-100" />
              <div>
                <p className="text-sm font-medium text-gray-800 line-clamp-1">{currentItem.productName}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {currentItem.productAttribute && <span>{currentItem.productAttribute} </span>}
                  x{currentItem.productQuantity}
                </p>
                <p className="text-sm text-[#e02020] font-medium mt-0.5">¥{parseFloat(currentItem.productPrice || "0").toFixed(2)}</p>
              </div>
            </div>

            {/* Star rating */}
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">商品评分</p>
              <div className="flex gap-1">
                {Array.from({ length: 5 }, (_, i) => (
                  <button key={i} onClick={() => updateCurrentReview({ star: i + 1 })}
                    className="p-0.5 transition-transform hover:scale-110">
                    <Star
                      size={28}
                      className={i < currentReview.star ? "fill-yellow-400 text-yellow-400" : "text-gray-200"}
                    />
                  </button>
                ))}
              </div>
            </div>

            {/* Content */}
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">评价内容</p>
              <textarea
                value={currentReview.content}
                onChange={(e) => updateCurrentReview({ content: e.target.value })}
                placeholder="说说你的使用心得，帮助其他小伙伴参考～"
                className="w-full border border-gray-200 rounded-lg p-3 text-sm h-28 resize-none focus:outline-none focus:border-[#e02020] transition-colors"
                maxLength={500}
              />
              <p className="text-xs text-gray-400 text-right mt-1">{currentReview.content.length}/500</p>
            </div>

            {/* Pics */}
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">上传图片（可选）</p>
              <div className="flex gap-2">
                <label className="w-20 h-20 border border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:border-gray-400 transition-colors">
                  <ImagePlus size={24} className="text-gray-400" />
                  <span className="text-xs text-gray-400 mt-1">上传</span>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={async (e) => {
                      const file = e.target.files?.[0]
                      if (!file) return
                      // 转换为 base64 作为临时方案（实际生产应使用 oss/文件服务器上传）
                      const reader = new FileReader()
                      reader.onload = (ev) => {
                        const dataUrl = ev.target?.result as string
                        updateCurrentReview({ pics: dataUrl })
                      }
                      reader.readAsDataURL(file)
                    }}
                  />
                </label>
                {currentReview.pics && (
                  <div className="relative w-20 h-20">
                    <img src={currentReview.pics} alt="" className="w-full h-full rounded-lg object-cover border" />
                    <button
                      onClick={() => updateCurrentReview({ pics: "" })}
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-gray-700 text-white rounded-full flex items-center justify-center text-xs"
                    >
                      <X size={12} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100 bg-gray-50 rounded-b-xl">
          <span className="text-xs text-gray-400">
            评价 {Object.keys(reviews).filter((k) => reviews[Number(k)]?.content?.trim()).length}/{items.length}
          </span>
          <div className="flex gap-2">
            {items.length > 1 && currentItemIndex < items.length - 1 && (
              <button
                onClick={() => setCurrentItemIndex((i) => Math.min(i + 1, items.length - 1))}
                disabled={!currentReview.content?.trim()}
                className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                下一个商品
              </button>
            )}
            <button
              onClick={handleSubmitAll}
              disabled={submitting || !isAllReviewed}
              className="px-6 py-2 text-sm bg-[#e02020] text-white rounded-lg hover:bg-[#c01010] transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {submitting && <Loader2 size={14} className="animate-spin" />}
              提交评价
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
