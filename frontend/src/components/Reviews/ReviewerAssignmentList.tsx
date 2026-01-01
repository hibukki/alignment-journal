import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Check, X } from "lucide-react"
import { useState } from "react"

import {
  ReviewerAssignmentsService,
  type ReviewerAssignmentWithPaper,
} from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import ReviewFormDialog from "./ReviewFormDialog"

interface ReviewerAssignmentListProps {
  assignments: ReviewerAssignmentWithPaper[]
}

const statusColors: Record<string, string> = {
  invited: "bg-yellow-100 text-yellow-800",
  accepted: "bg-blue-100 text-blue-800",
  declined: "bg-gray-100 text-gray-800",
  completed: "bg-green-100 text-green-800",
}

export default function ReviewerAssignmentList({
  assignments,
}: ReviewerAssignmentListProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [respondingId, setRespondingId] = useState<string | null>(null)

  const respondMutation = useMutation({
    mutationFn: ({
      assignmentId,
      status,
    }: {
      assignmentId: string
      status: "accepted" | "declined"
    }) =>
      ReviewerAssignmentsService.respondToInvitation({
        assignmentId,
        requestBody: { status },
      }),
    onSuccess: (_, variables) => {
      showSuccessToast(
        variables.status === "accepted"
          ? "Invitation accepted"
          : "Invitation declined"
      )
      setRespondingId(null)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["reviewer-assignments"] })
    },
  })

  const handleRespond = (
    assignmentId: string,
    status: "accepted" | "declined"
  ) => {
    setRespondingId(assignmentId)
    respondMutation.mutate({ assignmentId, status })
  }

  return (
    <div className="grid gap-4">
      {assignments.map((assignment) => (
        <Card key={assignment.id}>
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-lg">{assignment.paper_title}</CardTitle>
                <CardDescription>
                  Invited {new Date(assignment.invited_at).toLocaleDateString()}
                </CardDescription>
              </div>
              <Badge className={statusColors[assignment.status]}>
                {assignment.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              {assignment.status === "invited" && (
                <>
                  <Button
                    size="sm"
                    onClick={() => handleRespond(assignment.id, "accepted")}
                    disabled={respondingId === assignment.id}
                  >
                    <Check className="mr-2 h-4 w-4" />
                    Accept
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleRespond(assignment.id, "declined")}
                    disabled={respondingId === assignment.id}
                  >
                    <X className="mr-2 h-4 w-4" />
                    Decline
                  </Button>
                </>
              )}
              {assignment.status === "accepted" && (
                <ReviewFormDialog
                  assignmentId={assignment.id}
                  paperTitle={assignment.paper_title}
                />
              )}
              {assignment.status === "completed" && (
                <span className="text-sm text-muted-foreground">
                  Review submitted
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
