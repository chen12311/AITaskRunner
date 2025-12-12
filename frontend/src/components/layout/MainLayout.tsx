import { Outlet } from 'react-router-dom'
import { Toaster } from '@/components/ui/sonner'
import Sidebar from './Sidebar'
import Header from './Header'

export default function MainLayout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col lg:ml-64 min-w-0">
        <Header />
        <main className="flex-1 bg-muted/30 overflow-auto">
          <Outlet />
        </main>
      </div>
      <Toaster />
    </div>
  )
}
