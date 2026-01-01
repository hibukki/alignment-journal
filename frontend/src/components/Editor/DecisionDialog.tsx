import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Gavel } from "lucide-react"
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

interface DecisionDialogProps {
  paperId: string
  versionId: string
  paperTitle: string
}

export default function DecisionDialog({
  paperId,
  versionId,
  paperTitle,
}: DecisionDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [decision, setDecision] = useState<"accept" | "reject" | "revise">("accept")
  const [rationale, setRationale] = useState("")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () =>
      PapersService.makeDecision({
        paperId,
        versionId,
        requestBody: {
          paper_version_id: versionId,
          decision,
          rationale: rationale || null,
        },
      }),
    onSuccess: () => {
      const messages = {
        accept: "Paper accepted",
        reject: "Paper rejected",
        revise: "Revision requested",
      }
      showSuccessToast(messages[decision])
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
          <Gavel className="mr-2 h-4 w-4" />
          Final Decision
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Final Decision</DialogTitle>
          <DialogDescription>
            Make a final decision for: {paperTitle}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="decision">Decision</Label>
            <Select
              value={decision}
              onValueChange={(value: "accept" | "reject" | "revise") =>
                setDecision(value)
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select decision" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="accept">Accept</SelectItem>
                <SelectItem value="revise">Request revision</SelectItem>
                <SelectItem value="reject">Reject</SelectItem>
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
