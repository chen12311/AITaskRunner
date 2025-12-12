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
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'

import { useProjectStore } from '@/stores'
import type { Project } from '@/types'

// Schema 验证消息由组件级翻译处理
const formSchema = z.object({
  name: z.string().min(1),
  directory_path: z.string().min(1),
  description: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

interface ProjectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  project: Project | null
}

export default function ProjectDialog({ open, onOpenChange, project }: ProjectDialogProps) {
  const { t } = useTranslation()
  const { createProject, updateProject, fetchProjects } = useProjectStore()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      directory_path: '',
      description: '',
    },
  })

  useEffect(() => {
    if (project) {
      form.reset({
        name: project.name,
        directory_path: project.directory_path || project.directory || '',
        description: project.description || '',
      })
    } else {
      form.reset({
        name: '',
        directory_path: '',
        description: '',
      })
    }
  }, [project, form])

  const onSubmit = async (data: FormData) => {
    // 使用翻译消息验证必填字段
    if (!data.name.trim()) {
      form.setError('name', { message: t('projects.dialog.form.nameRequired') })
      return
    }
    if (!data.directory_path.trim()) {
      form.setError('directory_path', { message: t('projects.dialog.form.directoryRequired') })
      return
    }

    try {
      if (project) {
        await updateProject(project.id, data)
        toast.success(t('projects.updateSuccess'))
      } else {
        await createProject(data)
        toast.success(t('projects.createSuccess'))
      }
      await fetchProjects()
      onOpenChange(false)
    } catch {
      toast.error(project ? t('projects.updateFailed') : t('projects.createFailed'))
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {project ? t('projects.dialog.title.edit') : t('projects.dialog.title.create')}
          </DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('projects.dialog.form.name')}</FormLabel>
                  <FormControl>
                    <Input placeholder={t('projects.dialog.form.namePlaceholder')} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="directory_path"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('projects.dialog.form.directory')}</FormLabel>
                  <FormControl>
                    <Input placeholder={t('projects.dialog.form.directoryPlaceholder')} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('projects.dialog.form.description')}</FormLabel>
                  <FormControl>
                    <Textarea placeholder={t('projects.dialog.form.descriptionPlaceholder')} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                {t('common.cancel')}
              </Button>
              <Button type="submit">{project ? t('common.save') : t('common.create')}</Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
