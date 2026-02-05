"""
合同审批功能路由
"""
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Contract,
    ContractCreate,
    ContractProject,
    ContractProjectCreate,
    ContractProjectPublic,
    ContractProjectUpdate,
    ContractPublic,
    ContractUpdate,
    ContractsPublic,
    ContractProjectsPublic,
    Invoice,
    InvoiceCreate,
    InvoicePublic,
    InvoiceUpdate,
    InvoicesPublic,
    Message,
)
from app.services.contract_parser import ContractParser, InvoiceParser
from app.utils import delete_file, save_upload_file

router = APIRouter(prefix="/contracts", tags=["contracts"])


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def apply_parsed_contract(contract: Contract, parsed_data: dict[str, Any] | None) -> None:
    if not parsed_data:
        return
    if not contract.contract_number and parsed_data.get("contract_number"):
        contract.contract_number = str(parsed_data["contract_number"])
    if not contract.contract_name and parsed_data.get("contract_name"):
        contract.contract_name = str(parsed_data["contract_name"])
    if contract.amount is None and isinstance(parsed_data.get("amount"), (int, float)):
        contract.amount = float(parsed_data["amount"])
    if not contract.sign_date:
        contract.sign_date = parse_iso_datetime(parsed_data.get("sign_date"))
    if not contract.effective_date:
        contract.effective_date = parse_iso_datetime(parsed_data.get("effective_date"))
    if not contract.expiry_date:
        contract.expiry_date = parse_iso_datetime(parsed_data.get("expiry_date"))


def parse_contract_in(contract_in: str = Form(...)) -> ContractCreate:
    try:
        return ContractCreate.model_validate_json(contract_in)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid contract_in JSON: {exc}") from exc


def parse_contract_update_in(contract_in: str = Form(...)) -> ContractUpdate:
    try:
        return ContractUpdate.model_validate_json(contract_in)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid contract_in JSON: {exc}") from exc


def parse_invoice_in(invoice_in: str = Form(...)) -> InvoiceCreate:
    try:
        return InvoiceCreate.model_validate_json(invoice_in)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid invoice_in JSON: {exc}") from exc


def parse_invoice_update_in(invoice_in: str = Form(...)) -> InvoiceUpdate:
    try:
        return InvoiceUpdate.model_validate_json(invoice_in)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid invoice_in JSON: {exc}") from exc


# ==================== 合同项目 CRUD ====================

@router.get("/projects", response_model=ContractProjectsPublic)
def read_contract_projects(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    获取合同项目列表
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(ContractProject)
        count = session.exec(count_statement).one()
        statement = (
            select(ContractProject)
            .order_by(ContractProject.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        projects = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(ContractProject)
            .where(ContractProject.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(ContractProject)
            .where(ContractProject.owner_id == current_user.id)
            .order_by(ContractProject.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        projects = session.exec(statement).all()

    return ContractProjectsPublic(data=projects, count=count)


@router.get("/projects/{id}", response_model=ContractProjectPublic)
def read_contract_project(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    获取单个合同项目
    """
    project = session.get(ContractProject, id)
    if not project:
        raise HTTPException(status_code=404, detail="Contract project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return project


@router.post("/projects", response_model=ContractProjectPublic)
def create_contract_project(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_in: ContractProjectCreate,
) -> Any:
    """
    创建新的合同项目
    """
    project = ContractProject.model_validate(
        project_in, update={"owner_id": current_user.id}
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.put("/projects/{id}", response_model=ContractProjectPublic)
def update_contract_project(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    project_in: ContractProjectUpdate,
) -> Any:
    """
    更新合同项目
    """
    project = session.get(ContractProject, id)
    if not project:
        raise HTTPException(status_code=404, detail="Contract project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    update_dict = project_in.model_dump(exclude_unset=True)
    project.sqlmodel_update(update_dict)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.delete("/projects/{id}")
def delete_contract_project(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    删除合同项目（级联删除相关合同和发票）
    """
    project = session.get(ContractProject, id)
    if not project:
        raise HTTPException(status_code=404, detail="Contract project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(project)
    session.commit()
    return Message(message="Contract project deleted successfully")


# ==================== 合同 CRUD ====================

@router.get("/project/{project_id}", response_model=ContractsPublic)
def read_contracts_by_project(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    获取指定项目的合同列表
    """
    # 验证项目存在且有权限访问
    project = session.get(ContractProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Contract project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    count_statement = (
        select(func.count())
        .select_from(Contract)
        .where(Contract.project_id == project_id)
    )
    count = session.exec(count_statement).one()
    statement = (
        select(Contract)
        .where(Contract.project_id == project_id)
        .order_by(Contract.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    contracts = session.exec(statement).all()

    return ContractsPublic(data=contracts, count=count)


@router.get("/{id}", response_model=ContractPublic)
def read_contract(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    获取单个合同
    """
    contract = session.get(Contract, id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    # 检查项目访问权限
    project = session.get(ContractProject, contract.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return contract


@router.post("/", response_model=ContractPublic)
async def create_contract(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    contract_in: ContractCreate = Depends(parse_contract_in),
    file: UploadFile | None = File(None),
) -> Any:
    """
    创建新合同（可选上传文件并自动解析）
    """
    # 验证项目存在且有权限访问
    project = session.get(ContractProject, contract_in.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Contract project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 创建合同对象
    contract_data = contract_in.model_dump()
    contract = Contract.model_validate(contract_data)

    # 处理文件上传和解析
    parsed_data = None
    if file:
        original_filename = file.filename or "contract.pdf"
        file_content = await file.read()
        file_path = save_upload_file(
            file_content=file_content,
            filename=original_filename,
            subfolder="contracts",
        )
        contract.file_path = file_path

        try:
            parsed_data = ContractParser.parse_file(file_path)
        except ValueError as e:
            parsed_data = {
                "parse_status": "unsupported",
                "parse_message": str(e),
            }
        except Exception as e:
            parsed_data = {
                "parse_status": "failed",
                "parse_message": f"解析失败: {str(e)}",
            }

    contract.parsed_data = parsed_data
    apply_parsed_contract(contract, parsed_data)
    session.add(contract)
    session.commit()
    session.refresh(contract)
    return contract


@router.put("/{id}", response_model=ContractPublic)
async def update_contract(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    contract_in: ContractUpdate = Depends(parse_contract_update_in),
    file: UploadFile | None = File(None),
) -> Any:
    """
    更新合同（可选重新上传文件并解析）
    """
    contract = session.get(Contract, id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    # 检查项目访问权限
    project = session.get(ContractProject, contract.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 更新字段
    update_dict = contract_in.model_dump(exclude_unset=True)
    contract.sqlmodel_update(update_dict)

    # 处理新文件上传
    if file:
        # 删除旧文件
        if contract.file_path:
            delete_file(contract.file_path)

        original_filename = file.filename or "contract.pdf"
        file_content = await file.read()
        file_path = save_upload_file(
            file_content=file_content,
            filename=original_filename,
            subfolder="contracts",
        )
        contract.file_path = file_path

        try:
            parsed_data = ContractParser.parse_file(file_path)
            contract.parsed_data = parsed_data
            apply_parsed_contract(contract, parsed_data)
        except ValueError as e:
            contract.parsed_data = {
                "parse_status": "unsupported",
                "parse_message": str(e),
            }
        except Exception as e:
            contract.parsed_data = {
                "parse_status": "failed",
                "parse_message": f"解析失败: {str(e)}",
            }

    session.add(contract)
    session.commit()
    session.refresh(contract)
    return contract


@router.delete("/{id}")
def delete_contract(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    删除合同（级联删除相关发票）
    """
    contract = session.get(Contract, id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    # 检查项目访问权限
    project = session.get(ContractProject, contract.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 删除关联的文件
    if contract.file_path:
        delete_file(contract.file_path)

    session.delete(contract)
    session.commit()
    return Message(message="Contract deleted successfully")


# ==================== 发票 CRUD ====================

@router.get("/{contract_id}/invoices", response_model=InvoicesPublic)
def read_invoices_by_contract(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    contract_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    获取指定合同的发票列表
    """
    # 验证合同存在且有权限访问
    contract = session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    # 检查项目访问权限
    project = session.get(ContractProject, contract.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    count_statement = (
        select(func.count())
        .select_from(Invoice)
        .where(Invoice.contract_id == contract_id)
    )
    count = session.exec(count_statement).one()
    statement = (
        select(Invoice)
        .where(Invoice.contract_id == contract_id)
        .order_by(Invoice.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    invoices = session.exec(statement).all()

    return InvoicesPublic(data=invoices, count=count)


@router.get("/invoices/{id}", response_model=InvoicePublic)
def read_invoice(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    获取单个发票
    """
    invoice = session.get(Invoice, id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    # 检查合同访问权限
    contract = session.get(Contract, invoice.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    # 检查项目访问权限
    project = session.get(ContractProject, contract.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return invoice


@router.post("/invoices", response_model=InvoicePublic)
async def create_invoice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    invoice_in: InvoiceCreate = Depends(parse_invoice_in),
    file: UploadFile | None = File(None),
) -> Any:
    """
    创建新发票（可选上传文件并自动解析）
    """
    # 验证合同存在且有权限访问
    contract = session.get(Contract, invoice_in.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    # 检查项目访问权限
    project = session.get(ContractProject, contract.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 创建发票对象
    invoice_data = invoice_in.model_dump()
    invoice = Invoice.model_validate(invoice_data)

    # 处理文件上传和解析
    parsed_data = None
    if file:
        original_filename = file.filename or "invoice.pdf"
        file_content = await file.read()
        file_path = save_upload_file(
            file_content=file_content,
            filename=original_filename,
            subfolder="invoices",
        )
        invoice.file_path = file_path

        try:
            parsed_data = InvoiceParser.parse_file(file_path)
        except ValueError as e:
            parsed_data = {
                "parse_status": "unsupported",
                "parse_message": str(e),
            }
        except Exception as e:
            parsed_data = {
                "parse_status": "failed",
                "parse_message": f"解析失败: {str(e)}",
            }

    invoice.parsed_data = parsed_data
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice


@router.put("/invoices/{id}", response_model=InvoicePublic)
async def update_invoice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    invoice_in: InvoiceUpdate = Depends(parse_invoice_update_in),
    file: UploadFile | None = File(None),
) -> Any:
    """
    更新发票（可选重新上传文件并解析）
    """
    invoice = session.get(Invoice, id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    # 检查合同访问权限
    contract = session.get(Contract, invoice.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    # 检查项目访问权限
    project = session.get(ContractProject, contract.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 更新字段
    update_dict = invoice_in.model_dump(exclude_unset=True)
    invoice.sqlmodel_update(update_dict)

    # 处理新文件上传
    if file:
        # 删除旧文件
        if invoice.file_path:
            delete_file(invoice.file_path)

        original_filename = file.filename or "invoice.pdf"
        file_content = await file.read()
        file_path = save_upload_file(
            file_content=file_content,
            filename=original_filename,
            subfolder="invoices",
        )
        invoice.file_path = file_path

        try:
            parsed_data = InvoiceParser.parse_file(file_path)
            invoice.parsed_data = parsed_data
        except ValueError as e:
            invoice.parsed_data = {
                "parse_status": "unsupported",
                "parse_message": str(e),
            }
        except Exception as e:
            invoice.parsed_data = {
                "parse_status": "failed",
                "parse_message": f"解析失败: {str(e)}",
            }

    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice


@router.delete("/invoices/{id}")
def delete_invoice(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    删除发票
    """
    invoice = session.get(Invoice, id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    # 检查合同访问权限
    contract = session.get(Contract, invoice.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    # 检查项目访问权限
    project = session.get(ContractProject, contract.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and (project.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 删除关联的文件
    if invoice.file_path:
        delete_file(invoice.file_path)

    session.delete(invoice)
    session.commit()
    return Message(message="Invoice deleted successfully")
