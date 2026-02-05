import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import { FileText } from "lucide-react"
import { useState } from "react"

import { type ContractPublic, type InvoicePublic, ContractsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import AddInvoice from "@/components/Contracts/AddInvoice"
import ParsedDataDialog from "@/components/Contracts/ParsedDataDialog"
import { getInvoiceColumns } from "@/components/Contracts/invoice-columns"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const getInvoicesQueryOptions = (contractId: string) => ({
  queryFn: () =>
    ContractsService.readInvoicesByContract({
      contractId,
      skip: 0,
      limit: 100,
    }),
  queryKey: ["invoices", contractId],
})

interface InvoiceDialogProps {
  contract: ContractPublic
  onClose: () => void
}

const InvoiceDialog = ({ contract, onClose }: InvoiceDialogProps) => {
  const { data: invoicesData } = useSuspenseQuery(
    getInvoicesQueryOptions(contract.id)
  )
  const [invoiceForParse, setInvoiceForParse] = useState<InvoicePublic | null>(null)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const deleteMutation = useMutation({
    mutationFn: (invoiceId: string) =>
      ContractsService.deleteInvoice({ id: invoiceId }),
    onSuccess: () => {
      showSuccessToast("发票已删除")
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices", contract.id] })
    },
  })

  const columns = getInvoiceColumns({
    onViewParsedData: (invoice) => setInvoiceForParse(invoice),
    onDelete: (invoice) => {
      if (!window.confirm(`确定删除发票 ${invoice.invoice_number} 吗？`)) {
        return
      }
      deleteMutation.mutate(invoice.id)
    },
  })

  return (
    <>
      <Dialog
        open={!!contract}
        onOpenChange={(open) => {
          if (!open) {
            onClose()
            setInvoiceForParse(null)
          }
        }}
      >
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-muted-foreground" />
              发票管理
            </DialogTitle>
            <DialogDescription>
              合同：{contract.contract_name || "-"}（{contract.contract_number || "-"}）
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-6 py-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">发票列表</h2>
              <AddInvoice contractId={contract.id} />
            </div>

            {invoicesData.data.length === 0 ? (
              <div className="flex flex-col items-center justify-center text-center py-12">
                <div className="rounded-full bg-muted p-4 mb-4">
                  <FileText className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold">暂无发票</h3>
                <p className="text-muted-foreground">上传一张发票开始使用</p>
              </div>
            ) : (
              <DataTable columns={columns} data={invoicesData.data} />
            )}

            <div className="flex justify-end">
              <Button variant="outline" onClick={onClose}>
                关闭
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <ParsedDataDialog
        open={!!invoiceForParse}
        onOpenChange={(open) => {
          if (!open) {
            setInvoiceForParse(null)
          }
        }}
        kind="invoice"
        title={`发票解析 - ${invoiceForParse?.invoice_number ?? ""}`}
        parsedData={invoiceForParse?.parsed_data}
      />
    </>
  )
}

export default InvoiceDialog
