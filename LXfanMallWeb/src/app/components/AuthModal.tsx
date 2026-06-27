import { useState, useEffect, useRef, useCallback } from "react"
import * as Dialog from "@radix-ui/react-dialog"
import { X, Lock, User as UserIcon, Phone, ShieldCheck, ArrowRight, Loader2, Eye, EyeOff } from "lucide-react"
import { authApi } from "@/utils/api"
import { useUserStore } from "@/store/userStore"
import { useAuthModalStore } from "@/store/authModalStore"
import { toast } from "sonner"

type AuthMode = "login" | "register"

export function AuthModal() {
  const isOpen = useAuthModalStore((s) => s.isOpen)
  const storeMode = useAuthModalStore((s) => s.mode)
  const closeAuth = useAuthModalStore((s) => s.closeAuth)

  const [mode, setMode] = useState<AuthMode>(storeMode)
  const [loading, setLoading] = useState(false)
  const login = useUserStore((s) => s.login)
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const handleOpenChange = useCallback((open: boolean) => {
    if (!open) closeAuth()
  }, [closeAuth])

  useEffect(() => {
    if (isOpen) setMode(storeMode)
    return () => { if (countdownRef.current) clearInterval(countdownRef.current) }
  }, [isOpen, storeMode])

  // Login form
  const [loginUsername, setLoginUsername] = useState("")
  const [loginPassword, setLoginPassword] = useState("")

  // Register form
  const [regUsername, setRegUsername] = useState("")
  const [regPhone, setRegPhone] = useState("")
  const [regCode, setRegCode] = useState("")
  const [regPassword, setRegPassword] = useState("")
  const [countdown, setCountdown] = useState(0)
  const [agreedTerms, setAgreedTerms] = useState(false)
  const [showRegPassword, setShowRegPassword] = useState(false)

  const startCountdown = () => {
    setCountdown(60)
    countdownRef.current = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) { clearInterval(countdownRef.current!); return 0 }
        return c - 1
      })
    }, 1000)
  }

  const handleGetCode = async (phone: string) => {
    if (!phone || countdown > 0) return
    try {
      await authApi.getAuthCode(phone)
      toast.success("验证码已发送")
      startCountdown()
    } catch {
      toast.error("发送验证码失败")
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const data: any = await authApi.login({
        username: loginUsername,
        password: loginPassword,
      })
      const token = data.token || data.tokenHead + data.token
      // 先保存 token 到 localStorage，以便后续请求自动携带
      localStorage.setItem('token', token)
      // 获取用户信息
      const member: any = await authApi.getMemberInfo()
      setLoading(false)
      closeAuth()
      // 更新用户状态
      login(member, token)
      toast.success("登录成功")
    } catch {
      setLoading(false)
      toast.error("登录失败，请检查账号密码")
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!regUsername.trim()) { toast.error("请输入用户名"); return }
    if (!regPhone.trim()) { toast.error("请输入手机号"); return }
    if (!regCode.trim()) { toast.error("请输入验证码"); return }
    if (!regPassword.trim()) { toast.error("请设置密码"); return }
    if (regPassword.length < 6) { toast.error("密码至少6位"); return }
    if (!agreedTerms) { toast.error("请同意用户协议"); return }
    setLoading(true)
    try {
      await authApi.register({
        username: regUsername.trim(),
        password: regPassword,
        telephone: regPhone.trim(),
        authCode: regCode.trim(),
      })
      toast.success("注册成功，请登录")
      setMode("login")
    } catch (err: any) {
      toast.error(err?.message || "注册失败")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog.Root open={isOpen} onOpenChange={handleOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[850px] max-h-[90vh] shadow-2xl focus:outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] rounded-2xl overflow-hidden flex bg-white">

          {/* Left Side - Banner */}
          <div className="flex w-5/12 bg-[#e02020] relative flex-col justify-between p-8 text-white overflow-hidden">
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg">
                  <span className="text-[#e02020] font-black text-lg select-none">LX</span>
                </div>
                <div>
                  <div className="text-white font-black text-xl tracking-wide select-none">LXfanMall</div>
                </div>
              </div>
              <h2 className="text-3xl font-bold mb-3">
                {mode === "login" ? "欢迎回来" : "加入我们"}
              </h2>
              <p className="text-white/80 text-sm leading-relaxed">
                {mode === "login"
                  ? "登录您的账号，体验智能购物的无限乐趣。"
                  : "注册成为 LXfanMall 会员，享专属折扣、新品首发等特权。"}
              </p>
            </div>
            <div className="relative z-10 text-sm text-white/60">
              © {new Date().getFullYear()} LXfanMall. All rights reserved.
            </div>
            <div className="absolute top-[-20%] left-[-20%] w-64 h-64 bg-white/10 rounded-full blur-3xl mix-blend-overlay" />
            <div className="absolute bottom-[-10%] right-[-20%] w-80 h-80 bg-black/10 rounded-full blur-3xl mix-blend-overlay" />
          </div>

          {/* Right Side - Form */}
          <div className="w-7/12 p-8 relative bg-white overflow-y-auto">
            <Dialog.Title className="sr-only">{mode === "login" ? "登录账号" : "注册账号"}</Dialog.Title>
            <Dialog.Description className="sr-only">{mode === "login" ? "登录您的 LXfanMall 账号" : "注册成为 LXfanMall 新会员"}</Dialog.Description>
            <Dialog.Close className="absolute right-6 top-6 text-gray-400 hover:text-gray-700 transition-colors bg-gray-100 hover:bg-gray-200 p-2 rounded-full outline-none">
              <X size={18} />
            </Dialog.Close>

            <div key={mode} className="min-h-full flex flex-col justify-center max-w-sm mx-auto py-4" style={{ animation: "fadeInLeft 0.25s ease" }}>
              {mode === "login" ? (
                <>
                  <div className="mb-8">
                    <h3 className="text-2xl font-bold text-gray-900">账号登录</h3>
                  </div>

                  <form className="space-y-5" onSubmit={handleLogin}>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-gray-700">用户名</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"><UserIcon size={16} className="text-gray-400" /></div>
                        <input type="text" value={loginUsername} onChange={(e) => setLoginUsername(e.target.value)} className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020] transition-all" placeholder="请输入用户名" />
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between items-center">
                        <label className="text-xs font-medium text-gray-700">密码</label>
                      </div>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"><Lock size={16} className="text-gray-400" /></div>
                        <input type="password" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020] transition-all" placeholder="请输入密码" />
                      </div>
                    </div>
                    <div className="pt-2">
                      <button type="submit" disabled={loading} className="w-full py-3 bg-[#e02020] hover:bg-[#c01010] text-white rounded-lg text-sm font-bold shadow-lg shadow-red-500/30 transition-all flex justify-center items-center gap-2 group disabled:opacity-70">
                        <Loader2 size={18} className={`animate-spin ${loading ? '' : 'hidden'}`} />
                        <ArrowRight size={16} className={`group-hover:translate-x-1 transition-transform ${loading ? 'hidden' : ''}`} />
                        {loading ? "登录中..." : "登 录"}
                      </button>
                    </div>
                  </form>

                  <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                    <div className="font-medium mb-1">🎮 演示模式</div>
                    <div>账号：<code className="bg-amber-100 px-1.5 py-0.5 rounded text-amber-900 font-mono">xiaofan</code></div>
                    <div>密码：<code className="bg-amber-100 px-1.5 py-0.5 rounded text-amber-900 font-mono">xiaofan</code></div>
                  </div>

                  <div className="mt-4 text-center text-sm text-gray-400">
                    演示模式下不支持注册新账号
                  </div>
                </>
              ) : (
                <>
                  <div className="mb-6">
                    <h3 className="text-2xl font-bold text-gray-900">新用户注册</h3>
                    <p className="text-sm text-gray-500 mt-2">注册即享新人百元大礼包</p>
                  </div>

                  <form className="space-y-4" onSubmit={handleRegister}>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-gray-700">用户名</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"><UserIcon size={16} className="text-gray-400" /></div>
                        <input type="text" value={regUsername} onChange={(e) => setRegUsername(e.target.value)} className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020] transition-all" placeholder="请输入用户名" />
                      </div>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-gray-700">手机号</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"><Phone size={16} className="text-gray-400" /></div>
                        <input type="text" value={regPhone} onChange={(e) => setRegPhone(e.target.value)} className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020] transition-all" placeholder="请输入手机号" />
                      </div>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-gray-700">验证码</label>
                      <div className="relative flex gap-3">
                        <div className="relative flex-1">
                          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"><ShieldCheck size={16} className="text-gray-400" /></div>
                          <input type="text" value={regCode} onChange={(e) => setRegCode(e.target.value)} className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020] transition-all" placeholder="请输入验证码" />
                        </div>
                        <button type="button" disabled={countdown > 0} onClick={() => handleGetCode(regPhone)} className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors whitespace-nowrap">
                          {countdown > 0 ? `${countdown}s` : "获取验证码"}
                        </button>
                      </div>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-gray-700">设置密码</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"><Lock size={16} className="text-gray-400" /></div>
                        <input type={showRegPassword ? "text" : "password"} value={regPassword} onChange={(e) => setRegPassword(e.target.value)} className="w-full pl-10 pr-10 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e02020]/20 focus:border-[#e02020] transition-all" placeholder="请设置6-20位密码" />
                        <button type="button" onClick={() => setShowRegPassword(!showRegPassword)} className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors">
                          {showRegPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>
                    <div className="flex items-start gap-2 mt-2">
                      <input type="checkbox" id="terms" checked={agreedTerms} onChange={(e) => setAgreedTerms(e.target.checked)} className="mt-1 accent-[#e02020]" />
                      <label htmlFor="terms" className="text-xs text-gray-500 leading-tight">我已阅读并同意 <span className="text-[#e02020] hover:underline cursor-pointer">《用户服务协议》</span> 和 <span className="text-[#e02020] hover:underline cursor-pointer">《隐私政策》</span></label>
                    </div>
                    <div className="pt-2">
                      <button type="submit" disabled={loading} className="w-full py-3 bg-[#e02020] hover:bg-[#c01010] text-white rounded-lg text-sm font-bold shadow-lg shadow-red-500/30 transition-all flex justify-center items-center gap-2 group disabled:opacity-70">
                        <Loader2 size={18} className={`animate-spin ${loading ? '' : 'hidden'}`} />
                        {loading ? "注册中..." : "立即注册"}
                      </button>
                    </div>
                  </form>

                  <div className="mt-4 text-center text-sm text-gray-500">
                    已有账号？{" "}
                    <button onClick={() => setMode("login")} className="text-[#e02020] font-medium hover:underline">直接登录</button>
                  </div>
                </>
              )}
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
