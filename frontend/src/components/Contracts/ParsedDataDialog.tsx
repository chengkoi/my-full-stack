import { FileText, Info } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

type ParsedData = Record<string, unknown> | null | undefined

type ParsedKind = "contract" | "invoice"

interface ParsedDataDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  kind: ParsedKind
  title: string
  parsedData: ParsedData
}

const getParseStatusBadge = (parsedData: ParsedData) => {
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
      return { label: "未解析", variant: "outline" as const }
  }
}

const formatDate = (value: unknown) => {
  if (typeof value !== "string" || !value) {
    return "-"
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleDateString("zh-CN")
}

const formatMoney = (value: unknown) => {
  if (typeof value !== "number") {
    return "-"
  }
  return `¥${value.toLocaleString("zh-CN", { minimumFractionDigits: 2 })}`
}

const formatText = (value: unknown) => {
  if (value === null || value === undefined || value === "") {
    return "-"
  }
  if (Array.isArray(value)) {
    return value.join(", ")
  }
  if (typeof value === "object") {
    return JSON.stringify(value)
  }
  return String(value)
}

const getSummaryRows = (kind: ParsedKind, parsedData: ParsedData) => {
  if (!parsedData) {
    return []
  }

  if (kind === "contract") {
    const stampPages = Array.isArray(parsedData.stamp_pages)
      ? parsedData.stamp_pages
          .filter((value) => typeof value === "number")
          .map((value) => value + 1)
          .join(", ")
      : "-"

    return [
      { label: "甲方", value: formatText(parsedData.party_a) },
      { label: "乙方", value: formatText(parsedData.party_b) },
      { label: "合同编号", value: formatText(parsedData.contract_number) },
      { label: "签约日期", value: formatDate(parsedData.sign_date) },
      { label: "生效日期", value: formatDate(parsedData.effective_date) },
      { label: "到期日期", value: formatDate(parsedData.expiry_date) },
      { label: "合同金额", value: formatMoney(parsedData.amount) },
      { label: "盖章页", value: stampPages || "-" },
    ]
  }

  return [
    { label: "发票号码", value: formatText(parsedData.invoice_number) },
    { label: "发票代码", value: formatText(parsedData.invoice_code) },
    { label: "开票日期", value: formatDate(parsedData.invoice_date) },
    { label: "销售方", value: formatText(parsedData.seller) },
    { label: "购买方", value: formatText(parsedData.buyer) },
    { label: "发票金额", value: formatMoney(parsedData.amount) },
    { label: "税额", value: formatMoney(parsedData.tax_amount) },
  ]
}

const getParseMessage = (parsedData: ParsedData) => {
  if (!parsedData || typeof parsedData.parse_message !== "string") {
    return "暂无解析信息"
  }
  return parsedData.parse_message
}

const getRawText = (parsedData: ParsedData) => {
  if (!parsedData || typeof parsedData.raw_text !== "string") {
    return ""
  }
  return parsedData.raw_text
}

const getJsonText = (parsedData: ParsedData) => {
  if (!parsedData) {
    return ""
  }
  return JSON.stringify(parsedData, null, 2)
}

const ParsedDataDialog = ({
  open,
  onOpenChange,
  kind,
  title,
  parsedData,
}: ParsedDataDialogProps) => {
  const badge = getParseStatusBadge(parsedData)
  const summaryRows = getSummaryRows(kind, parsedData)
  const parseMessage = getParseMessage(parsedData)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {title}
          </DialogTitle>
          <DialogDescription className="flex items-center gap-2">
            <Badge variant={badge.variant}>{badge.label}</Badge>
            <span className="text-muted-foreground">{parseMessage}</span>
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="summary">
          <TabsList>
            <TabsTrigger value="summary">解析结果</TabsTrigger>
            <TabsTrigger value="raw">原始文本</TabsTrigger>
            <TabsTrigger value="json">原始JSON</TabsTrigger>
          </TabsList>
          <TabsContent value="summary">
            {summaryRows.length === 0 ? (
              <div className="flex items-center gap-2 text-muted-foreground py-6">
                <Info className="h-4 w-4" />
                暂无解析数据
              </div>
            ) : (
              <div className="grid gap-3 md:grid-cols-2">
                {summaryRows.map((row) => (
                  <div
                    key={row.label}
                    className="rounded-lg border bg-muted/30 p-3"
                  >
                    <div className="text-xs text-muted-foreground">{row.label}</div>
                    <div className="text-sm font-medium text-foreground">
                      {row.value}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
          <TabsContent value="raw">
            <pre className="whitespace-pre-wrap rounded-lg border bg-muted/20 p-4 text-sm text-foreground">
              {getRawText(parsedData) || "暂无原始文本"}
            </pre>
          </TabsContent>
          <TabsContent value="json">
            <pre className="whitespace-pre-wrap rounded-lg border bg-muted/20 p-4 text-sm text-foreground">
              {getJsonText(parsedData) || "暂无原始JSON"}
            </pre>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}

export default ParsedDataDialog
