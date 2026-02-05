import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { type ContractCreate, ContractsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  contract_number: z.preprocess(
    (value) => (value === "" ? undefined : value),
    z.string().min(1, { message: "合同编号不能为空" }).optional()
  ),
  contract_name: z.preprocess(
    (value) => (value === "" ? undefined : value),
    z.string().min(1, { message: "合同名称不能为空" }).optional()
  ),
  amount: z.preprocess(
    (value) => {
      if (value === "" || value === undefined || value === null) {
        return undefined
      }
      const parsed = Number(value)
      return Number.isNaN(parsed) ? undefined : parsed
    },
    z.number().min(0, { message: "金额必须大于等于0" }).optional()
  ),
  sign_date: z.preprocess(
    (value) => (value === "" ? undefined : value),
    z.string().optional()
  ),
  effective_date: z.preprocess(
    (value) => (value === "" ? undefined : value),
    z.string().optional()
  ),
  expiry_date: z.preprocess(
    (value) => (value === "" ? undefined : value),
    z.string().optional()
  ),
})

type FormData = z.infer<typeof formSchema>

type SubmitData = FormData & {
  file?: File | null
}

interface AddContractProps {
  projectId: string
  triggerLabel?: string
}

const AddContract = ({ projectId, triggerLabel = "添加合同" }: AddContractProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [contractFile, setContractFile] = useState<File | null>(null)
  const [fileInputKey, setFileInputKey] = useState(0)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      contract_number: "",
      contract_name: "",
      amount: undefined,
      sign_date: "",
      effective_date: "",
      expiry_date: "",
    },
  })

  const mutation = useMutation({
    mutationFn: ({ file, ...data }: SubmitData) => {
      const contractIn: ContractCreate = {
        ...data,
        project_id: projectId,
      }

      return ContractsService.createContract({
        formData: {
          contract_in: contractIn,
          file: file ?? undefined,
        },
      })
    },
    onSuccess: () => {
      showSuccessToast("合同创建成功")
      form.reset()
      setContractFile(null)
      setFileInputKey((current) => current + 1)
      setIsOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts", projectId] })
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate({ ...data, file: contractFile })
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        setIsOpen(open)
        if (!open) {
          form.reset()
          setContractFile(null)
          setFileInputKey((current) => current + 1)
        }
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Plus className="mr-2 h-4 w-4" />
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>添加合同</DialogTitle>
          <DialogDescription>
            直接上传合同文件即可自动解析关键信息；手动填写为可选项
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="contract_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      合同编号 <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="例如：CON-2024-001"
                        type="text"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="contract_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      合同名称 <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="例如：某公司采购合同"
                        type="text"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      金额（元） <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="0.00"
                        type="number"
                        step="0.01"
                        {...field}
                        value={field.value ?? ""}
                        onChange={(event) => {
                          const value = event.target.value
                          field.onChange(value === "" ? undefined : value)
                        }}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="sign_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>签约日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="effective_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>生效日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="expiry_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>到期日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormItem>
                <FormLabel>合同文件</FormLabel>
                <FormControl>
                  <Input
                    key={fileInputKey}
                    type="file"
                    accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
                    onChange={(event) => {
                      const file = event.target.files?.[0] ?? null
                      setContractFile(file)
                    }}
                  />
                </FormControl>
                <p className="text-xs text-muted-foreground">
                  支持 PDF/DOC/DOCX/图片，自动解析仅支持 PDF
                </p>
                <FormMessage />
              </FormItem>
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  取消
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                <Plus className="mr-2 h-4 w-4" />
                创建
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default AddContract
