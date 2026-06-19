import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface MemberInfo {
  id: number
  memberLevelId: number
  username: string
  nickname: string
  phone: string
  icon: string
  gender: number
  birthday: string
  city: string
  job: string
  personalizedSignature: string
  integration: number
  growth: number
  luckeyCount: number
  historyIntegration: number
}

interface UserState {
  member: MemberInfo | null
  token: string | null
  isAuthenticated: boolean
  setMember: (member: MemberInfo) => void
  login: (member: MemberInfo, token: string) => void
  logout: () => void
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      member: null,
      token: null,
      isAuthenticated: false,

      setMember: (member) => {
        set({ member, isAuthenticated: true })
      },

      login: (member, token) => {
        set({ member, token, isAuthenticated: true })
        localStorage.setItem('token', token)
      },

      logout: () => {
        set({ member: null, token: null, isAuthenticated: false })
        localStorage.removeItem('token')
        localStorage.removeItem('user-storage')
      },
    }),
    {
      name: 'user-storage',
      partialize: (state) => ({
        member: state.member,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)
