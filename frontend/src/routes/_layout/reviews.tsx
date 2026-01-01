import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { ClipboardList } from "lucide-react"
import { Suspense } from "react"

import { ReviewerAssignmentsService } from "@/client"
import PendingItems from "@/components/Pending/PendingItems"
import ReviewerAssignmentList from "@/components/Reviews/ReviewerAssignmentList"

function getAssignmentsQueryOptions() {
  return {
    queryFn: () => ReviewerAssignmentsService.listMyAssignments(),
    queryKey: ["reviewer-assignments"],
  }
}

export const Route = createFileRoute("/_layout/reviews")({
  component: Reviews,
  head: () => ({
    meta: [
      {
        title: "My Reviews - Alignment Journal",
      },
    ],
  }),
})

function ReviewsContent() {
  const { data: assignments } = useSuspenseQuery(getAssignmentsQueryOptions())

  if (assignments.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <ClipboardList className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No review assignments</h3>
        <p className="text-muted-foreground">
          You'll see papers here when invited to review
        </p>
      </div>
    )
  }

  return <ReviewerAssignmentList assignments={assignments.data} />
}

function ReviewsDashboard() {
  return (
    <Suspense fallback={<PendingItems />}>
      <ReviewsContent />
    </Suspense>
  )
}

function Reviews() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Reviews</h1>
        <p className="text-muted-foreground">
          Manage your review invitations and assignments
        </p>
      </div>
      <ReviewsDashboard />
    </div>
  )
}
