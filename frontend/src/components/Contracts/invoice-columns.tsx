import { ColumnDef } from "@tanstack/react-table"
import { FileText, MoreHorizontal, Trash2 } from "lucide-react"

import type { InvoicePublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard"

export interface InvoiceColumnsProps {
  onViewParsedData: (invoice: InvoicePublic) => void
  onDelete: (invoice: InvoicePublic) => void
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

const getParseStatusBadge = (invoice: InvoicePublic) => {
  if (!invoice.file_path) {
    return { label: "未上传", variant: "outline" as const }
  }

  const parsedData = invoice.parsed_data as Record<string, unknown> | null
  const status =
    parsedData && typeof parsedData.parse_status === "string"
      ? parsedData.parse_status
      : null

  switch (status) {
    case "full":
      return { label: "已解析", variant: "secondary" as const }
    case "partial":
      return { label: "部分解析", variant: "secondary" as const }
    case "failed":
      return { label: "解析失败", variant: "destructive" as const }
    case "unsupported":
      return { label: "不支持解析", variant: "outline" as const }
    default:
      return { label: "待解析", variant: "outline" as const }
  }
}

export const getInvoiceColumns = ({
  onViewParsedData,
  onDelete,
}: InvoiceColumnsProps): ColumnDef<InvoicePublic>[] => [
  {
    accessorKey: "id",
    header: "ID",
    cell: ({ row }) => <CopyId id={row.original.id} />,
  },
  {
    accessorKey: "invoice_number",
    header: "发票号码",
    cell: ({ row }) => (
      <span className="font-medium">{row.original.invoice_number}</span>
    ),
  },
  {
    accessorKey: "invoice_code",
    header: "发票代码",
    cell: ({ row }) => <span>{row.original.invoice_code}</span>,
  },
  {
    accessorKey: "amount",
    header: "金额",
    cell: ({ row }) => (
      <span className="font-medium">
        ¥{row.original.amount.toLocaleString("zh-CN", { minimumFractionDigits: 2 })}
      </span>
    ),
  },
  {
    accessorKey: "invoice_date",
    header: "开票日期",
    cell: ({ row }) => (
      <span>
        {row.original.invoice_date
          ? new Date(row.original.invoice_date).toLocaleDateString("zh-CN")
          : "-"}
      </span>
    ),
  },
  {
    accessorKey: "file_path",
    header: "文件",
    cell: ({ row }) => (
      <span>
        {row.original.file_path ? (
          <span className="text-green-600">已上传</span>
        ) : (
          <span className="text-muted-foreground">未上传</span>
        )}
      </span>
    ),
  },
  {
    id: "parse_status",
    header: "解析状态",
    cell: ({ row }) => {
      const badge = getParseStatusBadge(row.original)
      return <Badge variant={badge.variant}>{badge.label}</Badge>
    },
  },
  {
    id: "actions",
    cell: ({ row }) => (
      <InvoiceActionsMenu
        invoice={row.original}
        onViewParsedData={onViewParsedData}
        onDelete={onDelete}
      />
    ),
  },
]

function InvoiceActionsMenu({
  invoice,
  onViewParsedData,
  onDelete,
}: {
  invoice: InvoicePublic
  onViewParsedData: (invoice: InvoicePublic) => void
  onDelete: (invoice: InvoicePublic) => void
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => onViewParsedData(invoice)}>
          <FileText className="mr-2 h-4 w-4" />
          查看解析
        </DropdownMenuItem>
        <DropdownMenuItem
          className="text-destructive"
          onClick={() => onDelete(invoice)}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          删除发票
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
