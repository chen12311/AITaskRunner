import { useEffect, useState, useMemo, useCallback } from 'react'
import { RefreshCw, Activity, Server, Zap, AlertCircle, Pause, Square, ExternalLink } from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import { enUS, zhCN } from 'date-fns/locale'
import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Skeleton } from '@/components/ui/skeleton'

import { useSessionStore } from '@/stores'
import type { SessionStatusFilter } from '@/types/task'
import { useWebSocket } from '@/hooks'

interface StatCardProps {
  label: string
  value: number | string
  icon: React.ReactNode
  className?: string
}

const StatCard = ({ label, value, icon, className = '' }: StatCardProps) => (
  <Card className={className}>
    <CardContent className="flex items-center justify-between p-6">
      <div>
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-3xl font-bold mt-1">{value}</p>
      </div>
      <div className="text-muted-foreground">{icon}</div>
    </CardContent>
  </Card>
)

export function Component() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const {
    sessions,
    stats,
    loading,
    fetchAllSessions,
    stopSession,
    pauseSession,
    stopAllSessions,
    statusFilter,
    setStatusFilter,
  } = useSessionStore()

  const [search, setSearch] = useState('')
  const [stopDialogOpen, setStopDialogOpen] = useState(false)
  const [stopAllDialogOpen, setStopAllDialogOpen] = useState(false)
  const [sessionToStop, setSessionToStop] = useState<string | null>(null)
  const currentLocale = i18n.language.startsWith('zh') ? zhCN : enUS

  const statusConfig = useMemo(() => ({
    running: { label: t('sessions.status.running'), variant: 'default' as const },
    paused: { label: t('sessions.status.paused'), variant: 'secondary' as const },
    stopped: { label: t('sessions.status.stopped'), variant: 'outline' as const },
  }), [t])

  // 优化7.1-7.3: 使用 WebSocket 替代轮询
  useWebSocket({ enabled: true })

  // 初始加载会话数据
  useEffect(() => {
    fetchAllSessions()
    // 优化7.2: 移除轮询，改用 WebSocket 推送
  }, [fetchAllSessions])

  // 过滤会话
  const filteredSessions = useMemo(() => {
    return sessions.filter((session) => {
      const matchesStatus = statusFilter === 'all' || session.status === statusFilter
      const matchesSearch = search === '' || session.task_id.toLowerCase().includes(search.toLowerCase())
      return matchesStatus && matchesSearch
    })
  }, [sessions, statusFilter, search])

  // 手动刷新
  const handleRefresh = useCallback(() => {
    fetchAllSessions()
    toast.success(t('sessions.toast.refreshed'))
  }, [fetchAllSessions, t])

  // 停止单个会话
  const handleStopSession = useCallback(async () => {
    if (!sessionToStop) return

    try {
      await stopSession(sessionToStop)
      setStopDialogOpen(false)
      setSessionToStop(null)
    } catch (error) {
      console.error('Failed to stop session:', error)
    }
  }, [sessionToStop, stopSession])

  // 暂停会话
  const handlePauseSession = useCallback(async (taskId: string) => {
    try {
      await pauseSession(taskId)
    } catch (error) {
      console.error('Failed to pause session:', error)
    }
  }, [pauseSession])

  // 停止所有会话
  const handleStopAllSessions = useCallback(async () => {
    try {
      await stopAllSessions()
      setStopAllDialogOpen(false)
    } catch (error) {
      console.error('Failed to stop all sessions:', error)
    }
  }, [stopAllSessions])

  // 跳转到日志查看详情
  const handleViewDetails = useCallback((taskId: string) => {
    navigate(`/logs?taskId=${taskId}`)
  }, [navigate])

  // 计算运行时长
  const getRunningDuration = useCallback((startedAt: string) => {
    try {
      return formatDistanceToNow(new Date(startedAt), { locale: currentLocale, addSuffix: false })
    } catch {
      return '-'
    }
  }, [currentLocale])

  // 格式化时间戳
  const formatTime = useCallback((time: string) => {
    try {
      return format(new Date(time), 'yyyy-MM-dd HH:mm:ss', { locale: currentLocale })
    } catch {
      return '-'
    }
  }, [currentLocale])

  // 根据可用性确定槽位颜色
  const getSlotColor = () => {
    if (stats.availableSlots === 0) return 'text-red-600'
    if (stats.availableSlots <= 1) return 'text-yellow-600'
    return 'text-green-600'
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t('sessions.title')}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t('sessions.description')}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            {t('sessions.refresh')}
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setStopAllDialogOpen(true)}
            disabled={sessions.length === 0}
          >
            <Square className="h-4 w-4 mr-2" />
            {t('sessions.stopAll')}
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label={t('sessions.stats.active')}
          value={stats.active}
          icon={<Activity className="h-8 w-8 text-green-600" />}
          className="border-l-4 border-l-green-600"
        />
        <StatCard
          label={t('sessions.stats.total')}
          value={stats.total}
          icon={<Server className="h-8 w-8" />}
        />
        <StatCard
          label={t('sessions.stats.maxConcurrent')}
          value={stats.maxConcurrent}
          icon={<Zap className="h-8 w-8 text-blue-600" />}
        />
        <StatCard
          label={t('sessions.stats.availableSlots')}
          value={stats.availableSlots}
          icon={<AlertCircle className={`h-8 w-8 ${getSlotColor()}`} />}
          className={`border-l-4 ${
            stats.availableSlots === 0
              ? 'border-l-red-600'
              : stats.availableSlots <= 1
              ? 'border-l-yellow-600'
              : 'border-l-green-600'
          }`}
        />
      </div>

      {/* 筛选和搜索 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t('sessions.listTitle')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Select
              value={statusFilter}
              onValueChange={(value) => setStatusFilter(value as SessionStatusFilter)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={t('sessions.filters.statusPlaceholder')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('sessions.status.all')}</SelectItem>
                <SelectItem value="running">{t('sessions.status.running')}</SelectItem>
                <SelectItem value="paused">{t('sessions.status.paused')}</SelectItem>
                <SelectItem value="stopped">{t('sessions.status.stopped')}</SelectItem>
              </SelectContent>
            </Select>
            <Input
              placeholder={t('sessions.filters.searchPlaceholder')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
            />
          </div>

          {/* 会话表格 */}
          {loading && sessions.length === 0 ? (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : filteredSessions.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Server className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>{search || statusFilter !== 'all' ? t('sessions.empty.noMatch') : t('sessions.empty.noData')}</p>
            </div>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('sessions.table.taskId')}</TableHead>
                    <TableHead>{t('sessions.table.status')}</TableHead>
                    <TableHead>{t('sessions.table.pid')}</TableHead>
                    <TableHead>{t('sessions.table.startedAt')}</TableHead>
                    <TableHead>{t('sessions.table.duration')}</TableHead>
                    <TableHead className="text-right">{t('sessions.table.actions')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSessions.map((session) => (
                    <TableRow key={session.task_id}>
                      <TableCell className="font-mono text-xs">
                        {session.task_id.substring(0, 8)}...
                      </TableCell>
                      <TableCell>
                        <Badge variant={statusConfig[session.status]?.variant || 'outline'}>
                          {statusConfig[session.status]?.label || session.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {session.pid || '-'}
                      </TableCell>
                      <TableCell className="text-sm">
                        {formatTime(session.started_at)}
                      </TableCell>
                      <TableCell className="text-sm">
                        {getRunningDuration(session.started_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex gap-1 justify-end">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewDetails(session.task_id)}
                            title={t('sessions.actions.viewDetails')}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                          {session.status === 'running' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handlePauseSession(session.task_id)}
                              title={t('sessions.actions.pause')}
                            >
                              <Pause className="h-4 w-4" />
                            </Button>
                          )}
                          {(session.status === 'running' || session.status === 'paused') && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSessionToStop(session.task_id)
                                setStopDialogOpen(true)
                              }}
                              title={t('sessions.actions.stop')}
                            >
                              <Square className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 停止单个会话确认 */}
      <AlertDialog open={stopDialogOpen} onOpenChange={setStopDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('sessions.dialogs.stopOne.title')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('sessions.dialogs.stopOne.description', { taskId: sessionToStop?.substring(0, 8) || '' })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('sessions.dialogs.stopOne.cancel')}</AlertDialogCancel>
            <AlertDialogAction onClick={handleStopSession}>{t('sessions.dialogs.stopOne.confirm')}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 停止所有会话确认 */}
      <AlertDialog open={stopAllDialogOpen} onOpenChange={setStopAllDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('sessions.dialogs.stopAll.title')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('sessions.dialogs.stopAll.description', { count: sessions.length })}
              <strong className="block mt-2 text-destructive">{t('sessions.dialogs.stopAll.warning')}</strong>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('sessions.dialogs.stopAll.cancel')}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleStopAllSessions}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {t('sessions.dialogs.stopAll.confirm')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
