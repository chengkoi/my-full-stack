import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { type InvoiceCreate, ContractsService } from "@/client"
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
  invoice_number: z.string().min(1, { message: "发票号码不能为空" }),
  invoice_code: z.string().min(1, { message: "发票代码不能为空" }),
  amount: z.number().min(0, { message: "金额必须大于等于0" }),
  invoice_date: z.string().optional(),
  seller: z.string().optional(),
  buyer: z.string().optional(),
  tax_amount: z.number().min(0).optional(),
  remark: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

type SubmitData = FormData & {
  file?: File | null
}

interface AddInvoiceProps {
  contractId: string
  triggerLabel?: string
}

const AddInvoice = ({ contractId, triggerLabel = "上传发票" }: AddInvoiceProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [invoiceFile, setInvoiceFile] = useState<File | null>(null)
  const [fileInputKey, setFileInputKey] = useState(0)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      invoice_number: "",
      invoice_code: "",
      amount: 0,
      invoice_date: "",
      seller: "",
      buyer: "",
      tax_amount: undefined,
      remark: "",
    },
  })

  const mutation = useMutation({
    mutationFn: ({ file, ...data }: SubmitData) => {
      const invoiceIn: InvoiceCreate = {
        ...data,
        contract_id: contractId,
      }

      return ContractsService.createInvoice({
        formData: {
          invoice_in: invoiceIn,
          file: file ?? undefined,
        },
      })
    },
    onSuccess: () => {
      showSuccessToast("发票创建成功")
      form.reset()
      setInvoiceFile(null)
      setFileInputKey((current) => current + 1)
      setIsOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices", contractId] })
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate({ ...data, file: invoiceFile })
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        setIsOpen(open)
        if (!open) {
          form.reset()
          setInvoiceFile(null)
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
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>上传发票</DialogTitle>
          <DialogDescription>
            填写发票信息，可选择性上传发票文件以自动解析
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="invoice_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      发票号码 <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="例如：12345678" type="text" {...field} required />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="invoice_code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      发票代码 <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="例如：012345678901" type="text" {...field} required />
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
                        onChange={(event) =>
                          field.onChange(parseFloat(event.target.value) || 0)
                        }
                        required
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="invoice_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>开票日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="seller"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>销售方</FormLabel>
                    <FormControl>
                      <Input placeholder="销售方名称" type="text" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="buyer"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>购买方</FormLabel>
                    <FormControl>
                      <Input placeholder="购买方名称" type="text" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="tax_amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>税额（元）</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="0.00"
                        type="number"
                        step="0.01"
                        {...field}
                        value={field.value ?? ""}
                        onChange={(event) => {
                          const value = event.target.value
                          field.onChange(value === "" ? undefined : parseFloat(value) || 0)
                        }}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="remark"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>备注</FormLabel>
                    <FormControl>
                      <Input placeholder="备注信息" type="text" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormItem>
                <FormLabel>发票文件</FormLabel>
                <FormControl>
                  <Input
                    key={fileInputKey}
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={(event) => {
                      const file = event.target.files?.[0] ?? null
                      setInvoiceFile(file)
                    }}
                  />
                </FormControl>
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

export default AddInvoice
