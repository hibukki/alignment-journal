import { useMutation, useQueryClient } from "@tanstack/react-query"
import { UserPlus } from "lucide-react"
import { useState } from "react"

import { PapersService } from "@/client"
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface InviteReviewerDialogProps {
  paperId: string
  versionId: string
  paperTitle: string
}

export default function InviteReviewerDialog({
  paperId,
  versionId,
  paperTitle,
}: InviteReviewerDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [reviewerPersonId, setReviewerPersonId] = useState("")
  const [identityConfidential, setIdentityConfidential] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () =>
      PapersService.inviteReviewer({
        paperId,
        versionId,
        requestBody: {
          paper_version_id: versionId,
          reviewer_person_id: reviewerPersonId,
          identity_confidential: identityConfidential,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Reviewer invited successfully")
      setIsOpen(false)
      setReviewerPersonId("")
      setIdentityConfidential(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["papers"] })
    },
  })

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <UserPlus className="mr-2 h-4 w-4" />
          Invite Reviewer
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Invite Reviewer</DialogTitle>
          <DialogDescription>
            Invite a reviewer for: {paperTitle}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="reviewerId">Reviewer Person ID</Label>
            <Input
              id="reviewerId"
              placeholder="Enter reviewer's person ID..."
              value={reviewerPersonId}
              onChange={(e) => setReviewerPersonId(e.target.value)}
            />
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="confidential"
              checked={identityConfidential}
              onCheckedChange={(checked) =>
                setIdentityConfidential(checked === true)
              }
            />
            <Label htmlFor="confidential">Keep reviewer identity confidential</Label>
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
            disabled={!reviewerPersonId}
          >
            Send Invitation
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
