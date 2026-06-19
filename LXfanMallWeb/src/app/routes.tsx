import { createBrowserRouter } from 'react-router'
import { Layout } from './components/Layout'
import { Home } from './pages/Home'
import { Category } from './pages/Category'
import { ProductDetail } from './pages/ProductDetail'
import { Cart } from './pages/Cart'
import { Order } from './pages/Order'
import { Orders } from './pages/Orders'
import { Profile } from './pages/Profile'
import { Payment } from './pages/Payment'
import { AIChat } from './pages/AIChat'
import { ActivityComingSoon } from './pages/ActivityComingSoon'
import { ReturnApply } from './pages/ReturnApply'
import { ReturnRecord } from './pages/ReturnRecord'

export const router = createBrowserRouter([
  {
    path: '/',
    Component: Layout,
    children: [
      { index: true, Component: Home },
      { path: 'category/:id', Component: Category },
      { path: 'product/:id', Component: ProductDetail },
      { path: 'cart', Component: Cart },
      { path: 'order', Component: Order },
      { path: 'orders', Component: Orders },
      { path: 'payment', Component: Payment },
      { path: 'profile', Component: Profile },
      { path: 'return-apply', Component: ReturnApply },
      { path: 'return-record', Component: ReturnRecord },
      { path: 'ai-chat', Component: AIChat },
      { path: 'activity-coming-soon', Component: ActivityComingSoon },
      { path: '*', Component: Home },
    ],
  },
])