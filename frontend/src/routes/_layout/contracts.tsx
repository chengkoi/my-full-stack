import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { FileText, FolderOpen } from "lucide-react"
import { Suspense, useState } from "react"

import { type ContractPublic, ContractsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import AddContract from "@/components/Contracts/AddContract"
import AddContractProject from "@/components/Contracts/AddContractProject"
import InvoiceDialog from "@/components/Contracts/InvoiceDialog"
import ParsedDataDialog from "@/components/Contracts/ParsedDataDialog"
import { getContractProjectColumns } from "@/components/Contracts/columns"
import { getContractColumns } from "@/components/Contracts/contract-columns"
import PendingItems from "@/components/Pending/PendingItems"
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

function getContractProjectsQueryOptions() {
  return {
    queryFn: () => ContractsService.readContractProjects({ skip: 0, limit: 100 }),
    queryKey: ["contract-projects"],
  }
}

function getContractProjectQueryOptions(id: string) {
  return {
    queryFn: () => {
      console.log("Fetching contract project with id:", id)
      return ContractsService.readContractProject({ id })
    },
    queryKey: ["contract-project", id],
    throwOnError: true,
  }
}

function getContractsQueryOptions(projectId: string) {
  return {
    queryFn: () => {
      console.log("Fetching contracts with projectId:", projectId)
      return ContractsService.readContractsByProject({
        projectId,
        skip: 0,
        limit: 100,
      })
    },
    queryKey: ["contracts", projectId],
    throwOnError: true,
  }
}

export const Route = createFileRoute("/_layout/contracts")({
  component: ContractProjects,
  head: () => ({
    meta: [
      {
        title: "合同审批 - FastAPI Cloud",
      },
    ],
  }),
})

function ProjectDetailDialog({
  projectId,
  onClose,
}: {
  projectId: string
  onClose: () => void
}) {
  const { data: project } = useSuspenseQuery(getContractProjectQueryOptions(projectId))
  const { data: contractsData } = useSuspenseQuery(
    getContractsQueryOptions(projectId)
  )
  const [contractForInvoices, setContractForInvoices] = useState<ContractPublic | null>(
    null
  )
  const [contractForParse, setContractForParse] = useState<ContractPublic | null>(null)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const deleteMutation = useMutation({
    mutationFn: (contractId: string) =>
      ContractsService.deleteContract({ id: contractId }),
    onSuccess: () => {
      showSuccessToast("合同已删除")
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts", projectId] })
    },
  })

  const contractColumns = getContractColumns({
    onViewInvoices: (contract) => setContractForInvoices(contract),
    onViewParsedData: (contract) => setContractForParse(contract),
    onDelete: (contract) => {
      const contractLabel = contract.contract_name || contract.contract_number || "该合同"
      if (!window.confirm(`确定删除合同 ${contractLabel} 吗？`)) {
        return
      }
      if (contractForInvoices?.id === contract.id) {
        setContractForInvoices(null)
      }
      if (contractForParse?.id === contract.id) {
        setContractForParse(null)
      }
      deleteMutation.mutate(contract.id)
    },
  })

  return (
    <>
      <Dialog
        open={!!projectId}
        onOpenChange={(open) => {
          if (!open) {
            onClose()
            setContractForInvoices(null)
            setContractForParse(null)
          }
        }}
      >
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{project.name}</DialogTitle>
            <DialogDescription>项目编号：{project.code}</DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-6 py-4">
            {project.description && (
              <div>
                <h3 className="text-lg font-semibold mb-2">项目描述</h3>
                <p className="text-muted-foreground">{project.description}</p>
              </div>
            )}

            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <h2 className="text-lg font-semibold">合同列表</h2>
                </div>
                <AddContract projectId={projectId} triggerLabel="上传合同文件" />
              </div>

              {contractsData.data.length === 0 ? (
                <div className="flex flex-col items-center justify-center text-center py-12">
                  <div className="rounded-full bg-muted p-4 mb-4">
                    <FileText className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-semibold">暂无合同</h3>
                  <p className="text-muted-foreground">添加一份合同开始使用</p>
                </div>
              ) : (
                <DataTable columns={contractColumns} data={contractsData.data} />
              )}
            </div>

            <div className="flex justify-end">
              <Button variant="outline" onClick={onClose}>
                关闭
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
      <ParsedDataDialog
        open={!!contractForParse}
        onOpenChange={(open) => {
          if (!open) {
            setContractForParse(null)
          }
        }}
        kind="contract"
        title={`合同解析 - ${contractForParse?.contract_name ?? ""}`}
        parsedData={contractForParse?.parsed_data}
      />
      {contractForInvoices && (
        <InvoiceDialog
          contract={contractForInvoices}
          onClose={() => setContractForInvoices(null)}
        />
      )}
    </>
  )
}

function ContractProjectsTableContent({
  columns,
}: {
  columns: ReturnType<typeof getContractProjectColumns>
}) {
  const { data: projects } = useSuspenseQuery(getContractProjectsQueryOptions())

  if (projects.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <FolderOpen className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">您还没有合同项目</h3>
        <p className="text-muted-foreground">创建一个新的合同项目开始使用</p>
      </div>
    )
  }

  return <DataTable columns={columns} data={projects.data} />
}

function ContractProjectsTable({
  columns,
}: {
  columns: ReturnType<typeof getContractProjectColumns>
}) {
  return (
    <Suspense fallback={<PendingItems />}>
      <ContractProjectsTableContent columns={columns} />
    </Suspense>
  )
}

function ContractProjects() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const columns = getContractProjectColumns({ onSelectProject: setSelectedProjectId })

  return (
    <>
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">合同审批</h1>
            <p className="text-muted-foreground">创建项目并管理合同和发票</p>
          </div>
          <AddContractProject />
        </div>
        <ContractProjectsTable columns={columns} />
      </div>

      {selectedProjectId && (
        <ProjectDetailDialog
          projectId={selectedProjectId}
          onClose={() => setSelectedProjectId(null)}
        />
      )}
    </>
  )
}
