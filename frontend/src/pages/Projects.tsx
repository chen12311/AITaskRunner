import { useEffect, useState, useCallback } from 'react'
import { Plus, Edit, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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

import { useProjectStore } from '@/stores'
import type { Project } from '@/types'
import ProjectDialog from '@/components/ProjectDialog'

export function Component() {
  const { t } = useTranslation()
  const { projects, loading, fetchProjects, deleteProject } = useProjectStore()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [projectToDelete, setProjectToDelete] = useState<string | null>(null)

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const handleEdit = useCallback((project: Project) => {
    setEditingProject(project)
    setDialogOpen(true)
  }, [])

  const handleCreate = useCallback(() => {
    setEditingProject(null)
    setDialogOpen(true)
  }, [])

  const handleDelete = useCallback(async () => {
    if (projectToDelete === null) return
    try {
      await deleteProject(projectToDelete)
      toast.success(t('projects.deleteSuccess'))
    } catch {
      toast.error(t('projects.deleteFailed'))
    }
    setDeleteDialogOpen(false)
    setProjectToDelete(null)
  }, [projectToDelete, deleteProject, t])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('projects.title')}</h1>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          {t('projects.createProject')}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('projects.title')}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('projects.table.name')}</TableHead>
                  <TableHead>{t('projects.table.directory')}</TableHead>
                  <TableHead>{t('projects.table.description')}</TableHead>
                  <TableHead className="w-[100px]">{t('projects.table.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projects.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                      {t('projects.noData')}
                    </TableCell>
                  </TableRow>
                ) : (
                  projects.map((project) => (
                    <TableRow key={project.id}>
                      <TableCell className="font-medium">{project.name}</TableCell>
                      <TableCell className="font-mono text-sm text-muted-foreground">
                        {project.directory_path || project.directory}
                      </TableCell>
                      <TableCell className="max-w-[300px] truncate">
                        {project.description || '-'}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="icon" onClick={() => handleEdit(project)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setProjectToDelete(project.id)
                              setDeleteDialogOpen(true)
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('projects.dialog.deleteTitle')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('projects.dialog.deleteDescription')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>
              {t('projects.dialog.confirmDelete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <ProjectDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        project={editingProject}
      />
    </div>
  )
}

Component.displayName = 'Projects'
