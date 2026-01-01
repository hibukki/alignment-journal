import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { FileText } from "lucide-react"
import { Suspense } from "react"

import { PapersService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import AddPaper from "@/components/Papers/AddPaper"
import { columns } from "@/components/Papers/columns"
import PendingItems from "@/components/Pending/PendingItems"

function getPapersQueryOptions() {
  return {
    queryFn: () => PapersService.listPapers({ skip: 0, limit: 100 }),
    queryKey: ["papers"],
  }
}

export const Route = createFileRoute("/_layout/papers")({
  component: Papers,
  head: () => ({
    meta: [
      {
        title: "Papers - Alignment Journal",
      },
    ],
  }),
})

function PapersTableContent() {
  const { data: papers } = useSuspenseQuery(getPapersQueryOptions())

  if (papers.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No papers yet</h3>
        <p className="text-muted-foreground">Submit a paper to get started</p>
      </div>
    )
  }

  return <DataTable columns={columns} data={papers.data} />
}

function PapersTable() {
  return (
    <Suspense fallback={<PendingItems />}>
      <PapersTableContent />
    </Suspense>
  )
}

function Papers() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Papers</h1>
          <p className="text-muted-foreground">Submit and track your papers</p>
        </div>
        <AddPaper />
      </div>
      <PapersTable />
    </div>
  )
}
