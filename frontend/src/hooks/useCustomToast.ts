import { toast } from "sonner"

const useCustomToast = () => {
  const showSuccessToast = (description: string) => {
    toast.success("Success!", {
      description,
    })
  }

  const showErrorToast = (description: string) => {
    toast.error("出了点问题!", {
      description,
    })
  }

  return { showSuccessToast, showErrorToast }
}

export default useCustomToast
