import React, { useState } from 'react'
import { Typography, Button, Box, Dialog, DialogTitle, DialogContent, TextField, DialogActions, List, ListItemButton, ListItemText, Alert, CircularProgress, IconButton, ListItem } from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'

export default function ProjectList() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [projectToDelete, setProjectToDelete] = useState<any>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)

  const { data: projects, isLoading, refetch, error: queryError } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      console.log('🔄 Fetching projects from /api/projects/')
      const result = await api.listProjects()
      console.log('✅ Projects API response:', result)
      console.log('   Type:', typeof result, 'IsArray:', Array.isArray(result), 'Length:', result?.length)
      return result
    },
  })

  // Debug: Log whenever projects data changes
  React.useEffect(() => {
    console.log('📊 Projects state updated:', {
      isLoading,
      hasData: !!projects,
      isArray: Array.isArray(projects),
      length: projects?.length,
      data: projects
    })
  }, [projects, isLoading])

  const create = useMutation({
    mutationFn: async (data: { name: string; description: string }) => {
      console.log('Creating project:', data)
      const result = await api.createProject(data)
      console.log('Project created:', result)
      return result
    },
    onSuccess: (res) => {
      console.log('Creation successful, closing modal and refetching')
      setOpen(false)
      setName('')
      setDescription('')
      setError(null)
      // Force immediate refetch
      refetch()
    },
    onError: (err: any) => {
      console.error('Creation failed:', err)
      setError(err.message || 'Failed to create project')
    },
  })

  const deleteProject = useMutation({
    mutationFn: async (projectId: string) => {
      return await api.deleteProject(projectId)
    },
    onSuccess: () => {
      setDeleteDialogOpen(false)
      setProjectToDelete(null)
      setError(null)
      refetch()
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to delete project')
      setDeleteDialogOpen(false)
    },
  })

  const handleCreate = () => {
    setError(null)
    create.mutate({ name, description })
  }

  const handleDeleteClick = (e: React.MouseEvent, project: any) => {
    e.stopPropagation() // Prevent navigation
    setProjectToDelete(project)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = () => {
    if (projectToDelete) {
      deleteProject.mutate(projectToDelete.id)
    }
  }

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>Loading projects...</Typography>
        </Box>
      </Box>
    )
  }

  if (queryError) {
    return (
      <Box sx={{ textAlign:'center', mt:8 }}>
        <Alert severity="error" sx={{ mb:2 }}>
          {(queryError as any).message || 'Failed to load projects.'}
        </Alert>
        <Button variant="outlined" onClick={()=> refetch()}>Retry</Button>
      </Box>
    )
  }

  const projectsArray = Array.isArray(projects) ? projects : []
  const hasProjects = projectsArray.length > 0

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Projects</Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>
          New Project
        </Button>
      </Box>


      {!hasProjects && (
        <Alert severity="info" sx={{ mb: 2 }}>
          No projects yet. Click "New Project" to create your first one.
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <List>
        {projectsArray.map((p: any) => (
          <ListItem
            key={p.id}
            secondaryAction={
              <IconButton
                edge="end"
                aria-label="delete"
                onClick={(e) => handleDeleteClick(e, p)}
                color="error"
              >
                <DeleteIcon />
              </IconButton>
            }
            disablePadding
          >
            <ListItemButton onClick={() => navigate(`/projects/${p.id}`)}>
              <ListItemText
                primary={p.name || 'Untitled'}
                secondary={p.description || 'No description'}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          <TextField
            fullWidth
            label="Project Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            sx={{ mb: 2 }}
            autoFocus
            required
          />
          <TextField
            fullWidth
            label="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)} disabled={create.isPending}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!name.trim() || create.isPending}
            startIcon={create.isPending ? <CircularProgress size={20} /> : null}
          >
            {create.isPending ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Project?</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{projectToDelete?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={deleteProject.isPending}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deleteProject.isPending}
          >
            {deleteProject.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
