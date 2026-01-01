import type { PaperPublic } from "@/client"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import DeskDecisionDialog from "./DeskDecisionDialog"

interface EditorPaperListProps {
  papers: PaperPublic[]
}

export default function EditorPaperList({ papers }: EditorPaperListProps) {
  return (
    <div className="grid gap-4">
      {papers.map((paper) => (
        <Card key={paper.id}>
          <CardHeader>
            <CardTitle className="text-lg">{paper.title}</CardTitle>
            <CardDescription>
              Submitted {new Date(paper.created_at).toLocaleDateString()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-4">
              {paper.abstract && (
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {paper.abstract}
                </p>
              )}
              <div className="flex gap-2">
                <DeskDecisionDialog paperId={paper.id} paperTitle={paper.title} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
