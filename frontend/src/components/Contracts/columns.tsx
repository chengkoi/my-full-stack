import { ColumnDef } from "@tanstack/react-table"
import { ArrowRight, Calendar, FileText, MoreHorizontal, Trash2 } from "lucide-react"

import type { ContractProjectPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard"

export interface ContractProjectColumnsProps {
  onSelectProject: (id: string) => void
}

function CopyId({ id }: { id: string }) {
  const [copiedText, copy] = useCopyToClipboard()
  const isCopied = copiedText === id

  return (
    <div className="flex items-center gap-1.5 group">
      <span className="font-mono text-xs text-muted-foreground">{id}</span>
      <Button
        variant="ghost"
        size="icon"
        className="size-6 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={() => copy(id)}
      >
        {isCopied ? (
          <span className="text-green-500 text-xs">✓</span>
        ) : (
          <MoreHorizontal className="size-3" />
        )}
        <span className="sr-only">Copy ID</span>
      </Button>
    </div>
  )
}

export const getContractProjectColumns = ({
  onSelectProject,
}: ContractProjectColumnsProps): ColumnDef<ContractProjectPublic>[] => [
  {
    accessorKey: "id",
    header: "ID",
    cell: ({ row }) => <CopyId id={row.original.id} />,
  },
  {
    accessorKey: "code",
    header: "项目编号",
    cell: ({ row }) => <span className="font-medium">{row.original.code}</span>,
  },
  {
    accessorKey: "name",
    header: "项目名称",
    cell: ({ row }) => (
      <button
        onClick={() => onSelectProject(row.original.id)}
        className="text-primary hover:underline flex items-center gap-2 bg-transparent border-0 cursor-pointer text-left"
      >
        {row.original.name}
        <ArrowRight className="h-4 w-4" />
      </button>
    ),
  },
  {
    accessorKey: "description",
    header: "描述",
    cell: ({ row }) => (
      <span>{row.original.description || "暂无描述"}</span>
    ),
  },
  {
    accessorKey: "created_at",
    header: "创建时间",
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <Calendar className="h-4 w-4 text-muted-foreground" />
        {row.original.created_at
          ? new Date(row.original.created_at).toLocaleDateString("zh-CN")
          : "-"}
      </div>
    ),
  },
  {
    id: "actions",
    cell: ({ row }) => (
      <ContractProjectActionsMenu
        project={row.original}
        onSelectProject={onSelectProject}
      />
    ),
  },
]

function ContractProjectActionsMenu({
  project,
  onSelectProject,
}: {
  project: ContractProjectPublic
  onSelectProject?: (id: string) => void
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => onSelectProject?.(project.id)}>
          <FileText className="mr-2 h-4 w-4" />
          查看详情
        </DropdownMenuItem>
        <DropdownMenuItem className="text-destructive">
          <Trash2 className="mr-2 h-4 w-4" />
          删除项目
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
