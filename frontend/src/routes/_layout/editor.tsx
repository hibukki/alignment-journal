import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { FileText } from "lucide-react"
import { Suspense } from "react"

import { PapersService } from "@/client"
import PendingItems from "@/components/Pending/PendingItems"
import EditorPaperList from "@/components/Editor/EditorPaperList"

function getPapersQueryOptions() {
  return {
    queryFn: () => PapersService.listPapers({ skip: 0, limit: 100 }),
    queryKey: ["papers"],
  }
}

export const Route = createFileRoute("/_layout/editor")({
  component: Editor,
  head: () => ({
    meta: [
      {
        title: "Editor Dashboard - Alignment Journal",
      },
    ],
  }),
})

function EditorContent() {
  const { data: papers } = useSuspenseQuery(getPapersQueryOptions())

  if (papers.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No papers to review</h3>
        <p className="text-muted-foreground">Papers will appear here when submitted</p>
      </div>
    )
  }

  return <EditorPaperList papers={papers.data} />
}

function EditorDashboard() {
  return (
    <Suspense fallback={<PendingItems />}>
      <EditorContent />
    </Suspense>
  )
}

function Editor() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Editor Dashboard</h1>
        <p className="text-muted-foreground">Review and manage paper submissions</p>
      </div>
      <EditorDashboard />
    </div>
  )
}
