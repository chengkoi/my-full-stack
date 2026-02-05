"""
合同和发票文档解析服务
"""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import docx2txt
import pdfplumber
import pytesseract
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class ContractParser:
    """合同解析器"""

    @staticmethod
    def parse_file(file_path: str) -> dict[str, Any]:
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return ContractParser.parse_pdf(file_path)
        if ext == ".docx":
            return ContractParser.parse_docx(file_path)
        if ext in {".jpg", ".jpeg", ".png"}:
            return ContractParser.parse_image(file_path)
        if ext == ".doc":
            raise ValueError("暂不支持doc格式解析")
        raise ValueError(f"不支持的文件类型: {ext}")

    @staticmethod
    def parse_pdf(file_path: str) -> dict[str, Any]:
        """
        解析合同PDF文件，提取关键信息

        Args:
            file_path: PDF文件路径

        Returns:
            解析结果字典，包含：
            - party_a: 甲方
            - party_b: 乙方
            - contract_number: 合同编号
            - sign_date: 签约日期
            - effective_date: 生效日期
            - expiry_date: 到期日期
            - stamp_pages: 盖章页面列表（页码）
            - amount: 合同金额
            - raw_text: 原始文本（用于人工审核）
        """
        full_path = Path(settings.UPLOAD_DIR) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        result: dict[str, Any] = {
            "party_a": None,
            "party_b": None,
            "contract_number": None,
            "sign_date": None,
            "effective_date": None,
            "expiry_date": None,
            "stamp_pages": [],
            "amount": None,
            "raw_text": "",
            "parse_status": "partial",  # full, partial, failed
            "parse_message": "自动解析完成，请人工审核",
        }

        try:
            # 使用 pdfplumber 提取文本
            with pdfplumber.open(full_path) as pdf:
                all_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    all_text += page_text + "\n\n"

                result["raw_text"] = all_text.strip()

                # 提取关键信息
                result.update(ContractParser._extract_contract_info(all_text))

                # 检测盖章页面（简单实现：查找包含印章关键词的页面）
                result["stamp_pages"] = ContractParser._detect_stamp_pages(pdf)

        except Exception as e:
            logger.error(f"解析合同PDF失败: {e}")
            result["parse_status"] = "failed"
            result["parse_message"] = f"解析失败: {str(e)}"

        return result

    @staticmethod
    def parse_docx(file_path: str) -> dict[str, Any]:
        full_path = Path(settings.UPLOAD_DIR) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        result: dict[str, Any] = {
            "party_a": None,
            "party_b": None,
            "contract_number": None,
            "contract_name": None,
            "sign_date": None,
            "effective_date": None,
            "expiry_date": None,
            "stamp_pages": [],
            "amount": None,
            "raw_text": "",
            "parse_status": "partial",
            "parse_message": "自动解析完成，请人工审核",
        }

        try:
            text = docx2txt.process(str(full_path)) or ""
            result["raw_text"] = text.strip()
            result.update(ContractParser._extract_contract_info(text))
        except Exception as e:
            logger.error(f"解析合同DOCX失败: {e}")
            result["parse_status"] = "failed"
            result["parse_message"] = f"解析失败: {str(e)}"

        return result

    @staticmethod
    def parse_image(file_path: str) -> dict[str, Any]:
        full_path = Path(settings.UPLOAD_DIR) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        result: dict[str, Any] = {
            "party_a": None,
            "party_b": None,
            "contract_number": None,
            "contract_name": None,
            "sign_date": None,
            "effective_date": None,
            "expiry_date": None,
            "stamp_pages": [],
            "amount": None,
            "raw_text": "",
            "parse_status": "partial",
            "parse_message": "自动解析完成，请人工审核",
        }

        try:
            with Image.open(full_path) as image:
                text = pytesseract.image_to_string(image, lang="chi_sim+eng")
            result["raw_text"] = text.strip()
            result.update(ContractParser._extract_contract_info(text))
        except Exception as e:
            logger.error(f"OCR解析合同图片失败: {e}")
            result["parse_status"] = "failed"
            result["parse_message"] = f"OCR解析失败: {str(e)}"

        return result

    @staticmethod
    def _extract_contract_info(text: str) -> dict[str, Any]:
        """从合同文本中提取关键信息"""
        info: dict[str, Any] = {}

        # 提取甲方
        party_a_patterns = [
            r"甲\s*方[：:：\s]*([^\n\r]{2,50}?)[\n\r，,。]",
            r"委托人[：:：\s]*([^\n\r]{2,50}?)[\n\r，,。]",
        ]
        for pattern in party_a_patterns:
            match = re.search(pattern, text)
            if match:
                info["party_a"] = match.group(1).strip()
                break

        # 提取乙方
        party_b_patterns = [
            r"乙\s*方[：:：\s]*([^\n\r]{2,50}?)[\n\r，,。]",
            r"受托人[：:：\s]*([^\n\r]{2,50}?)[\n\r，,。]",
        ]
        for pattern in party_b_patterns:
            match = re.search(pattern, text)
            if match:
                info["party_b"] = match.group(1).strip()
                break

        # 提取合同编号
        contract_number_patterns = [
            r"合同编[号码][：:：\s]*([A-Za-z0-9\-_/]{5,50})",
            r"合同号[：:：\s]*([A-Za-z0-9\-_/]{5,50})",
            r"协议编号[：:：\s]*([A-Za-z0-9\-_/]{5,50})",
        ]
        for pattern in contract_number_patterns:
            match = re.search(pattern, text)
            if match:
                info["contract_number"] = match.group(1).strip()
                break

        # 提取合同名称
        contract_name_patterns = [
            r"合同名称[：:：\s]*([^\n\r]{2,50})",
            r"项目名称[：:：\s]*([^\n\r]{2,50})",
        ]
        for pattern in contract_name_patterns:
            match = re.search(pattern, text)
            if match:
                info["contract_name"] = match.group(1).strip()
                break

        # 提取签约日期
        date_patterns = [
            r"签约日期[：:：\s]*(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})",
            r"签订日期[：:：\s]*(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})",
            r"签署日期[：:：\s]*(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                info["sign_date"] = ContractParser._parse_date(match.group(1))
                break

        # 提取生效日期
        effective_patterns = [
            r"生效日期[：:：\s]*(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})",
            r"本合同自.*?(\d{4}年\d{1,2}月\d{1,2}日).*?起生效",
        ]
        for pattern in effective_patterns:
            match = re.search(pattern, text)
            if match:
                info["effective_date"] = ContractParser._parse_date(match.group(1))
                break

        # 提取到期日期
        expiry_patterns = [
            r"到期日期[：:：\s]*(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})",
            r"有效期至[：:：\s]*(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})",
        ]
        for pattern in expiry_patterns:
            match = re.search(pattern, text)
            if match:
                info["expiry_date"] = ContractParser._parse_date(match.group(1))
                break

        # 提取金额
        amount_patterns = [
            r"合同金额[：:：\s]*[￥¥]?\s*([0-9,]+\.\d{2})",
            r"总金额[：:：\s]*[￥¥]?\s*([0-9,]+\.\d{2})",
            r"价款[：:：\s]*[￥¥]?\s*([0-9,]+\.\d{2})",
            r"人民币[：:：\s]*[￥¥]?\s*([0-9,]+\.\d{2})",
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    info["amount"] = float(amount_str)
                except ValueError:
                    pass
                break

        return info

    @staticmethod
    def _parse_date(date_str: str) -> str | None:
        """解析日期字符串为ISO格式"""
        try:
            # 处理 "2024年1月15日" 格式
            if "年" in date_str:
                date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "")
            # 尝试解析日期
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.isoformat()
        except ValueError:
            return None

    @staticmethod
    def _detect_stamp_pages(pdf: pdfplumber.PDF) -> list[int]:
        """
        检测盖章页面（简单实现）

        Args:
            pdf: pdfplumber PDF对象

        Returns:
            可能盖章的页面索引列表（从0开始）
        """
        stamp_pages = []
        stamp_keywords = ["盖章", "签字", "印章", "双方", "签署", "生效"]

        for i, page in enumerate(pdf):
            text = page.extract_text() or ""
            # 检查是否包含盖章相关关键词
            for keyword in stamp_keywords:
                if keyword in text:
                    stamp_pages.append(i)
                    break

        return stamp_pages


class InvoiceParser:
    """发票解析器"""

    @staticmethod
    def parse_file(file_path: str) -> dict[str, Any]:
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return InvoiceParser.parse_pdf(file_path)
        if ext == ".docx":
            return InvoiceParser.parse_docx(file_path)
        if ext in {".jpg", ".jpeg", ".png"}:
            return InvoiceParser.parse_image(file_path)
        if ext == ".doc":
            raise ValueError("暂不支持doc格式解析")
        raise ValueError(f"不支持的文件类型: {ext}")

    @staticmethod
    def parse_pdf(file_path: str) -> dict[str, Any]:
        """
        解析发票PDF文件，提取关键信息

        Args:
            file_path: PDF文件路径

        Returns:
            解析结果字典，包含：
            - invoice_number: 发票号码
            - invoice_code: 发票代码
            - amount: 发票金额
            - invoice_date: 开票日期
            - seller: 销售方
            - buyer: 购买方
            - tax_amount: 税额
            - raw_text: 原始文本
        """
        full_path = Path(settings.UPLOAD_DIR) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        result: dict[str, Any] = {
            "invoice_number": None,
            "invoice_code": None,
            "amount": None,
            "invoice_date": None,
            "seller": None,
            "buyer": None,
            "tax_amount": None,
            "raw_text": "",
            "parse_status": "partial",
            "parse_message": "自动解析完成，请人工审核",
        }

        try:
            # 使用 pdfplumber 提取文本
            with pdfplumber.open(full_path) as pdf:
                all_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    all_text += page_text + "\n\n"

                result["raw_text"] = all_text.strip()

                # 提取关键信息
                result.update(InvoiceParser._extract_invoice_info(all_text))

        except Exception as e:
            logger.error(f"解析发票PDF失败: {e}")
            result["parse_status"] = "failed"
            result["parse_message"] = f"解析失败: {str(e)}"

        return result

    @staticmethod
    def parse_docx(file_path: str) -> dict[str, Any]:
        full_path = Path(settings.UPLOAD_DIR) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        result: dict[str, Any] = {
            "invoice_number": None,
            "invoice_code": None,
            "amount": None,
            "invoice_date": None,
            "seller": None,
            "buyer": None,
            "tax_amount": None,
            "raw_text": "",
            "parse_status": "partial",
            "parse_message": "自动解析完成，请人工审核",
        }

        try:
            text = docx2txt.process(str(full_path)) or ""
            result["raw_text"] = text.strip()
            result.update(InvoiceParser._extract_invoice_info(text))
        except Exception as e:
            logger.error(f"解析发票DOCX失败: {e}")
            result["parse_status"] = "failed"
            result["parse_message"] = f"解析失败: {str(e)}"

        return result

    @staticmethod
    def parse_image(file_path: str) -> dict[str, Any]:
        full_path = Path(settings.UPLOAD_DIR) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        result: dict[str, Any] = {
            "invoice_number": None,
            "invoice_code": None,
            "amount": None,
            "invoice_date": None,
            "seller": None,
            "buyer": None,
            "tax_amount": None,
            "raw_text": "",
            "parse_status": "partial",
            "parse_message": "自动解析完成，请人工审核",
        }

        try:
            with Image.open(full_path) as image:
                text = pytesseract.image_to_string(image, lang="chi_sim+eng")
            result["raw_text"] = text.strip()
            result.update(InvoiceParser._extract_invoice_info(text))
        except Exception as e:
            logger.error(f"OCR解析发票图片失败: {e}")
            result["parse_status"] = "failed"
            result["parse_message"] = f"OCR解析失败: {str(e)}"

        return result

    @staticmethod
    def _extract_invoice_info(text: str) -> dict[str, Any]:
        """从发票文本中提取关键信息"""
        info: dict[str, Any] = {}

        # 提取发票号码
        invoice_number_patterns = [
            r"发票号码[：:：\s]*([0-9]{8,20})",
            r"No[：:：\s]*([0-9]{8,20})",
        ]
        for pattern in invoice_number_patterns:
            match = re.search(pattern, text)
            if match:
                info["invoice_number"] = match.group(1).strip()
                break

        # 提取发票代码
        invoice_code_patterns = [
            r"发票代码[：:：\s]*([0-9]{10,20})",
            r"代码[：:：\s]*([0-9]{10,20})",
        ]
        for pattern in invoice_code_patterns:
            match = re.search(pattern, text)
            if match:
                info["invoice_code"] = match.group(1).strip()
                break

        # 提取金额
        amount_patterns = [
            r"价税合计[：:：\s]*[￥¥]?\s*([0-9,]+\.\d{2})",
            r"合计金额[：:：\s]*[￥¥]?\s*([0-9,]+\.\d{2})",
            r"金额[：:：\s]*[￥¥]?\s*([0-9,]+\.\d{2})",
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    info["amount"] = float(amount_str)
                except ValueError:
                    pass
                break

        # 提取税额
        tax_patterns = [
            r"税额[：:：\s]*[￥¥]?\s*([0-9,]+\.\d{2})",
            r"增值税[：:：\s]*[￥¥]?\s*([0-9,]+\.\d{2})",
        ]
        for pattern in tax_patterns:
            match = re.search(pattern, text)
            if match:
                tax_str = match.group(1).replace(",", "")
                try:
                    info["tax_amount"] = float(tax_str)
                except ValueError:
                    pass
                break

        # 提取开票日期
        date_patterns = [
            r"开票日期[：:：\s]*(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})",
            r"日期[：:：\s]*(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                info["invoice_date"] = InvoiceParser._parse_date(match.group(1))
                break

        # 提取销售方
        seller_patterns = [
            r"销售方[：:：\s]*名称[：:：\s]*([^\n\r]{2,50})",
            r"收款方[：:：\s]*([^\n\r]{2,50})",
        ]
        for pattern in seller_patterns:
            match = re.search(pattern, text)
            if match:
                info["seller"] = match.group(1).strip()
                break

        # 提取购买方
        buyer_patterns = [
            r"购买方[：:：\s]*名称[：:：\s]*([^\n\r]{2,50})",
            r"付款方[：:：\s]*([^\n\r]{2,50})",
        ]
        for pattern in buyer_patterns:
            match = re.search(pattern, text)
            if match:
                info["buyer"] = match.group(1).strip()
                break

        return info

    @staticmethod
    def _parse_date(date_str: str) -> str | None:
        """解析日期字符串为ISO格式"""
        try:
            if "年" in date_str:
                date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "")
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.isoformat()
        except ValueError:
            return None
