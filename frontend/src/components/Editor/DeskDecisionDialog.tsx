import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ClipboardCheck } from "lucide-react"
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
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface DeskDecisionDialogProps {
  paperId: string
  paperTitle: string
}

export default function DeskDecisionDialog({ paperId, paperTitle }: DeskDecisionDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [decision, setDecision] = useState<"proceed" | "reject">("proceed")
  const [rationale, setRationale] = useState("")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () =>
      PapersService.makeDeskDecision({
        paperId,
        requestBody: {
          paper_id: paperId,
          decision,
          rationale: rationale || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast(`Paper ${decision === "proceed" ? "sent to review" : "rejected"}`)
      setIsOpen(false)
      setRationale("")
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
          <ClipboardCheck className="mr-2 h-4 w-4" />
          Desk Decision
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Desk Decision</DialogTitle>
          <DialogDescription>
            Make an initial decision for: {paperTitle}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="decision">Decision</Label>
            <Select
              value={decision}
              onValueChange={(value: "proceed" | "reject") => setDecision(value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select decision" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="proceed">Proceed to review</SelectItem>
                <SelectItem value="reject">Desk reject</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="rationale">Rationale (optional)</Label>
            <Input
              id="rationale"
              placeholder="Reason for decision..."
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
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
          >
            Submit Decision
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
