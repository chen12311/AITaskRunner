import { createBrowserRouter, Navigate } from 'react-router-dom'
import MainLayout from '@/components/layout/MainLayout'

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/tasks" replace />,
      },
      {
        path: 'tasks',
        lazy: () => import('@/pages/Tasks'),
      },
      {
        path: 'sessions',
        lazy: () => import('@/pages/Sessions'),
      },
      {
        path: 'logs',
        lazy: () => import('@/pages/Logs'),
      },
      {
        path: 'templates',
        lazy: () => import('@/pages/Templates'),
      },
      {
        path: 'projects',
        lazy: () => import('@/pages/Projects'),
      },
      {
        path: 'settings',
        lazy: () => import('@/pages/Settings'),
      },
    ],
  },
])

export default router
