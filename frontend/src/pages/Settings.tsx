import { useEffect, useState } from 'react'
import { Check, Info } from 'lucide-react'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

import { settingsApi } from '@/api'
import type { Settings, CLIOption, TerminalOption, SettingsMap } from '@/types'

// 将后端格式 {key: {value, description}} 转换为前端格式 {key: value}
function transformSettings(rawSettings: SettingsMap): Settings {
  const result: Settings = {}
  for (const [key, item] of Object.entries(rawSettings)) {
    if (item && item.value !== undefined) {
      (result as Record<string, unknown>)[key] = item.value
    }
  }
  return result
}

export function Component() {
  const { t } = useTranslation()
  const [settings, setSettings] = useState<Settings | null>(null)
  const [cliOptions, setCLIOptions] = useState<CLIOption[]>([])
  const [reviewCLIOptions, setReviewCLIOptions] = useState<CLIOption[]>([])
  const [terminalOptions, setTerminalOptions] = useState<TerminalOption[]>([])
  const [loading, setLoading] = useState(true)

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8086'

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    setLoading(true)
    try {
      const [settingsRes, cliRes, reviewCLIRes, terminalRes] = await Promise.all([
        settingsApi.getAllSettings(),
        settingsApi.getAvailableCLIs(),
        settingsApi.getAvailableReviewCLIs(),
        settingsApi.getAvailableTerminals(),
      ])

      // 后端返回格式: {settings: {key: {value, description}}}, 需要转换为 {key: value}
      if (settingsRes.settings) {
        setSettings(transformSettings(settingsRes.settings))
      }
      // 后端返回格式: {cli_tools: [...], current: "..."}
      if (cliRes?.cli_tools && Array.isArray(cliRes.cli_tools)) {
        setCLIOptions(cliRes.cli_tools.map((cli: CLIOption & { available?: boolean }) => ({
          ...cli,
          installed: cli.installed ?? cli.available ?? false,
        })))
      }
      // 后端返回格式: {cli_tools: [...], current: "..."}
      if (reviewCLIRes?.cli_tools && Array.isArray(reviewCLIRes.cli_tools)) {
        setReviewCLIOptions(reviewCLIRes.cli_tools.map((cli: CLIOption & { available?: boolean }) => ({
          ...cli,
          installed: cli.installed ?? cli.available ?? false,
        })))
      }
      // 后端返回格式: {terminals: [...], current: "...", platform: "..."}
      if (terminalRes?.terminals && Array.isArray(terminalRes.terminals)) {
        setTerminalOptions(terminalRes.terminals.map((t: TerminalOption & { available?: boolean }) => ({
          ...t,
          installed: t.installed ?? t.available ?? false,
        })))
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
      toast.error(t('settings.loadFailed'))
    } finally {
      setLoading(false)
    }
  }

  const updateSetting = async (key: string, value: string | number | boolean) => {
    try {
      await settingsApi.updateSetting(key, value)
      setSettings((prev) => (prev ? { ...prev, [key]: value } : prev))
      toast.success(t('settings.updateSuccess'))
    } catch {
      toast.error(t('settings.updateFailed'))
    }
  }

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">{t('settings.title')}</h1>
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-[200px] w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">{t('settings.title')}</h1>

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.api.title')}</CardTitle>
          <CardDescription>{t('settings.api.description')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">{t('settings.api.frontend')}</span>
            <Badge variant="secondary">{apiBaseUrl}</Badge>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">{t('settings.api.backend')}</span>
            <Badge variant="secondary">{apiBaseUrl}</Badge>
          </div>
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>{t('settings.api.hint')}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.review.title')}</CardTitle>
          <CardDescription>{t('settings.review.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2">
            <Switch
              id="review-enabled"
              checked={settings?.review_enabled}
              onCheckedChange={(checked) => updateSetting('review_enabled', checked)}
            />
            <Label htmlFor="review-enabled">{t('settings.review.enable')}</Label>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.cli.title')}</CardTitle>
          <CardDescription>{t('settings.cli.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {cliOptions.map((cli) => (
              <div
                key={cli.id}
                onClick={() => cli.installed && updateSetting('default_cli', cli.id)}
                className={cn(
                  'border rounded-lg px-4 py-3 cursor-pointer transition-all inline-flex items-center gap-3',
                  settings?.default_cli === cli.id && 'border-primary ring-2 ring-primary/20',
                  !cli.installed && 'opacity-50 cursor-not-allowed'
                )}
              >
                <span className="font-medium whitespace-nowrap">{t(`settings.clis.${cli.id}`)}</span>
                <div className="flex items-center gap-2">
                  {cli.recommended && <Badge>{t('settings.cli.recommended')}</Badge>}
                  {!cli.installed && <Badge variant="destructive">{t('settings.cli.notInstalled')}</Badge>}
                  {settings?.default_cli === cli.id && (
                    <Check className="h-4 w-4 text-primary" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {settings?.review_enabled && (
        <Card>
          <CardHeader>
            <CardTitle>{t('settings.reviewCli.title')}</CardTitle>
            <CardDescription>{t('settings.reviewCli.description')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {reviewCLIOptions.map((cli) => (
                <div
                  key={cli.id}
                  onClick={() => cli.installed && updateSetting('review_cli', cli.id)}
                  className={cn(
                    'border rounded-lg px-4 py-3 cursor-pointer transition-all inline-flex items-center gap-3',
                    settings?.review_cli === cli.id && 'border-primary ring-2 ring-primary/20',
                    !cli.installed && 'opacity-50 cursor-not-allowed'
                  )}
                >
                  <span className="font-medium whitespace-nowrap">{t(`settings.clis.${cli.id}`)}</span>
                  <div className="flex items-center gap-2">
                    {!cli.installed && <Badge variant="destructive">{t('settings.cli.notInstalled')}</Badge>}
                    {settings?.review_cli === cli.id && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.concurrent.title')}</CardTitle>
          <CardDescription>{t('settings.concurrent.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Label htmlFor="max-concurrent">{t('settings.concurrent.label')}</Label>
            <Input
              id="max-concurrent"
              type="number"
              min={1}
              max={10}
              value={settings?.max_concurrent || 3}
              onChange={(e) => updateSetting('max_concurrent', parseInt(e.target.value) || 1)}
              className="w-24"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.terminal.title')}</CardTitle>
          <CardDescription>{t('settings.terminal.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {terminalOptions.map((terminal) => (
              <div
                key={terminal.id}
                onClick={() => terminal.installed && updateSetting('terminal_type', terminal.id)}
                className={cn(
                  'border rounded-lg px-4 py-3 cursor-pointer transition-all inline-flex items-center gap-3',
                  settings?.terminal_type === terminal.id && 'border-primary ring-2 ring-primary/20',
                  !terminal.installed && 'opacity-50 cursor-not-allowed'
                )}
              >
                <span className="font-medium whitespace-nowrap">{t(`settings.terminals.${terminal.id}`)}</span>
                <div className="flex items-center gap-2">
                  {terminal.recommended && <Badge>{t('settings.cli.recommended')}</Badge>}
                  {!terminal.installed && <Badge variant="destructive">{t('settings.terminal.notInstalled')}</Badge>}
                  {settings?.terminal_type === terminal.id && (
                    <Check className="h-4 w-4 text-primary" />
                  )}
                </div>
              </div>
            ))}
          </div>
          <Alert className="mt-4">
            <Info className="h-4 w-4" />
            <AlertDescription>
              {t('settings.terminal.hint')}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  )
}

Component.displayName = 'Settings'
