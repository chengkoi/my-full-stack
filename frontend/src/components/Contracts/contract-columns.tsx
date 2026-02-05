import { ColumnDef } from "@tanstack/react-table"
import { FileText, MoreHorizontal, Receipt, Trash2 } from "lucide-react"

import type { ContractPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard"

export interface ContractColumnsProps {
  onViewInvoices: (contract: ContractPublic) => void
  onViewParsedData: (contract: ContractPublic) => void
  onDelete: (contract: ContractPublic) => void
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

const getParseStatusBadge = (contract: ContractPublic) => {
  if (!contract.file_path) {
    return { label: "未上传", variant: "outline" as const }
  }

  const parsedData = contract.parsed_data as Record<string, unknown> | null
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

export const getContractColumns = ({
  onViewInvoices,
  onViewParsedData,
  onDelete,
}: ContractColumnsProps): ColumnDef<ContractPublic>[] => [
  {
    accessorKey: "id",
    header: "ID",
    cell: ({ row }) => <CopyId id={row.original.id} />,
  },
  {
    accessorKey: "contract_number",
    header: "合同编号",
    cell: ({ row }) => (
      <span className="font-medium">
        {row.original.contract_number || "-"}
      </span>
    ),
  },
  {
    accessorKey: "contract_name",
    header: "合同名称",
    cell: ({ row }) => <span>{row.original.contract_name || "-"}</span>,
  },
  {
    accessorKey: "amount",
    header: "金额",
    cell: ({ row }) => (
      <span className="font-medium">
        {row.original.amount == null
          ? "-"
          : `¥${row.original.amount.toLocaleString("zh-CN", { minimumFractionDigits: 2 })}`}
      </span>
    ),
  },
  {
    accessorKey: "sign_date",
    header: "签约日期",
    cell: ({ row }) => (
      <span>
        {row.original.sign_date
          ? new Date(row.original.sign_date).toLocaleDateString("zh-CN")
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
      <ContractActionsMenu
        contract={row.original}
        onViewInvoices={onViewInvoices}
        onViewParsedData={onViewParsedData}
        onDelete={onDelete}
      />
    ),
  },
]

function ContractActionsMenu({
  contract,
  onViewInvoices,
  onViewParsedData,
  onDelete,
}: {
  contract: ContractPublic
  onViewInvoices: (contract: ContractPublic) => void
  onViewParsedData: (contract: ContractPublic) => void
  onDelete: (contract: ContractPublic) => void
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => onViewParsedData(contract)}>
          <FileText className="mr-2 h-4 w-4" />
          查看解析
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onViewInvoices(contract)}>
          <Receipt className="mr-2 h-4 w-4" />
          管理发票
        </DropdownMenuItem>
        <DropdownMenuItem
          className="text-destructive"
          onClick={() => onDelete(contract)}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          删除合同
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
