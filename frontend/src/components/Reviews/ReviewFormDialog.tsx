import { useMutation, useQueryClient } from "@tanstack/react-query"
import { FileEdit } from "lucide-react"
import { useState } from "react"

import { ReviewerAssignmentsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface ReviewFormDialogProps {
  assignmentId: string
  paperTitle: string
}

export default function ReviewFormDialog({
  assignmentId,
  paperTitle,
}: ReviewFormDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [content, setContent] = useState("")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () =>
      ReviewerAssignmentsService.submitReview({
        assignmentId,
        requestBody: {
          assignment_id: assignmentId,
          content,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Review submitted successfully")
      setIsOpen(false)
      setContent("")
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["reviewer-assignments"] })
    },
  })

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <FileEdit className="mr-2 h-4 w-4" />
          Submit Review
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Submit Review</DialogTitle>
          <DialogDescription>
            Write your review for: {paperTitle}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="review-content">Review</Label>
            <Textarea
              id="review-content"
              placeholder="Enter your review..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={10}
            />
          </div>
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" disabled={mutation.isPending}>
              Cancel
            </Button>
          </DialogClose>
          <LoadingButton
            onClick={() => mutation.mutate()}
            loading={mutation.isPending}
            disabled={!content.trim()}
          >
            Submit Review
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
