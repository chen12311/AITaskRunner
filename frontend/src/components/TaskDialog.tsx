import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'

import { useTaskStore } from '@/stores'
import type { Task, Project } from '@/types'

const formSchema = z.object({
  project_id: z.string().min(1),
  markdown_document_relative_path: z.string().min(1),
  cli_type: z.string().optional(),
  enable_review: z.enum(['inherit', 'enabled', 'disabled']),
})

type FormData = z.infer<typeof formSchema>

interface TaskDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  task: Task | null
  projects: Project[]
}

export default function TaskDialog({ open, onOpenChange, task, projects }: TaskDialogProps) {
  const { t } = useTranslation()
  const { createTask, updateTask, fetchTasks } = useTaskStore()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      project_id: '',
      markdown_document_relative_path: '',
      cli_type: '',
      enable_review: 'inherit',
    },
  })

  // 根据 project_directory 找到对应的 project_id
  const findProjectId = (projectDir: string | undefined): string => {
    if (!projectDir) return ''
    const project = projects.find(p => p.directory === projectDir)
    return project?.id?.toString() || ''
  }

  // 从完整路径提取相对路径
  const extractRelativePath = (fullPath: string | undefined, projectDir: string | undefined): string => {
    if (!fullPath || !projectDir) return ''
    return fullPath.replace(projectDir, '').replace(/^\//, '')
  }

  useEffect(() => {
    if (task) {
      const reviewValue = task.enable_review === true ? 'enabled' : task.enable_review === false ? 'disabled' : 'inherit'
      form.reset({
        project_id: findProjectId(task.project_directory),
        markdown_document_relative_path: extractRelativePath(task.markdown_document_path, task.project_directory),
        cli_type: task.cli_type || '',
        enable_review: reviewValue,
      })
    } else {
      form.reset({
        project_id: '',
        markdown_document_relative_path: '',
        cli_type: '',
        enable_review: 'inherit',
      })
    }
  }, [task, form, projects])

  const onSubmit = async (data: FormData) => {
    // Validate required fields with translated messages
    if (!data.project_id.trim()) {
      form.setError('project_id', { message: t('tasks.form.projectRequired') })
      return
    }
    if (!data.markdown_document_relative_path.trim()) {
      form.setError('markdown_document_relative_path', { message: t('tasks.form.docPathRequired') })
      return
    }

    const cliType = data.cli_type ? (data.cli_type as Task['cli_type']) : undefined
    const enableReview = data.enable_review === 'enabled' ? true : data.enable_review === 'disabled' ? false : null

    try {
      if (task) {
        await updateTask(task.id, {
          project_id: data.project_id,
          markdown_document_relative_path: data.markdown_document_relative_path,
          cli_type: cliType,
          enable_review: enableReview,
        })
        toast.success(t('tasks.form.updateSuccess'))
      } else {
        await createTask({
          project_id: data.project_id,
          markdown_document_relative_path: data.markdown_document_relative_path,
          cli_type: cliType,
          enable_review: enableReview,
        })
        toast.success(t('tasks.form.createSuccess'))
      }
      await fetchTasks()
      onOpenChange(false)
    } catch {
      toast.error(task ? t('tasks.form.updateFailed') : t('tasks.form.createFailed'))
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {task ? t('tasks.form.title.edit') : t('tasks.form.title.create')}
          </DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="project_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('tasks.form.project')}</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder={t('tasks.form.projectPlaceholder')} />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {projects.map((project) => (
                        <SelectItem key={project.id} value={project.id.toString()}>
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="markdown_document_relative_path"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('tasks.form.docPath')}</FormLabel>
                  <FormControl>
                    <Input placeholder={t('tasks.form.docPathPlaceholder')} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="cli_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('tasks.form.cliType')}</FormLabel>
                  <Select
                    onValueChange={(value) => field.onChange(value === '__default__' ? '' : value)}
                    value={field.value || '__default__'}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder={t('tasks.form.cliTypePlaceholder')} />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="__default__">{t('tasks.form.cliTypeDefault')}</SelectItem>
                      <SelectItem value="claude_code">Claude Code</SelectItem>
                      <SelectItem value="codex">Codex</SelectItem>
                      <SelectItem value="aider">Aider</SelectItem>
                      <SelectItem value="cursor">Cursor</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="enable_review"
              render={({ field }) => (
                <FormItem className="space-y-3">
                  <FormLabel>{t('tasks.form.enableReview')}</FormLabel>
                  <FormControl>
                    <RadioGroup
                      onValueChange={field.onChange}
                      value={field.value}
                      className="flex gap-4"
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="inherit" id="inherit" />
                        <Label htmlFor="inherit">{t('tasks.form.reviewInherit')}</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="enabled" id="enabled" />
                        <Label htmlFor="enabled">{t('tasks.form.reviewEnabled')}</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="disabled" id="disabled" />
                        <Label htmlFor="disabled">{t('tasks.form.reviewDisabled')}</Label>
                      </div>
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                {t('common.cancel')}
              </Button>
              <Button type="submit">{task ? t('common.save') : t('common.create')}</Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
