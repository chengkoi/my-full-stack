import uuid
from datetime import datetime, timezone

from pydantic import EmailStr
from sqlalchemy import DateTime, JSON
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    contract_projects: list["ContractProject"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ==================== 合同审批功能模型 ====================

# 合同项目基础属性
class ContractProjectBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=100)  # 项目编号
    description: str | None = Field(default=None, max_length=1000)


# 合同项目创建模式
class ContractProjectCreate(ContractProjectBase):
    pass


# 合同项目更新模式
class ContractProjectUpdate(ContractProjectBase):
    name: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    code: str | None = Field(default=None, min_length=1, max_length=100)  # type: ignore


# 数据库模型：合同项目
class ContractProject(ContractProjectBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="contract_projects")
    contracts: list["Contract"] = Relationship(back_populates="project", cascade_delete=True)


# 公共响应模式：合同项目
class ContractProjectPublic(ContractProjectBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ContractProjectsPublic(SQLModel):
    data: list[ContractProjectPublic]
    count: int


# 合同基础属性
class ContractBase(SQLModel):
    contract_number: str | None = Field(default=None, max_length=100)  # 合同编号
    contract_name: str | None = Field(default=None, max_length=255)  # 合同名称
    amount: float | None = Field(default=None, ge=0)  # 合同金额
    sign_date: datetime | None = None  # 签约日期
    effective_date: datetime | None = None  # 生效日期
    expiry_date: datetime | None = None  # 到期日期


# 合同创建模式
class ContractCreate(ContractBase):
    project_id: uuid.UUID  # 关联的合同项目


# 合同更新模式
class ContractUpdate(ContractBase):
    contract_number: str | None = Field(default=None, min_length=1, max_length=100)  # type: ignore
    contract_name: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    amount: float | None = None
    sign_date: datetime | None = None
    effective_date: datetime | None = None
    expiry_date: datetime | None = None


# 数据库模型：合同
class Contract(ContractBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    project_id: uuid.UUID = Field(foreign_key="contractproject.id", nullable=False, ondelete="CASCADE")
    project: ContractProject | None = Relationship(back_populates="contracts")
    file_path: str | None = None  # 合同文件路径
    parsed_data: dict | None = Field(default=None, sa_type=JSON)  # 解析的JSON数据（甲方、乙方、时间、盖章页面等）
    invoices: list["Invoice"] = Relationship(back_populates="contract", cascade_delete=True)


# 公共响应模式：合同
class ContractPublic(ContractBase):
    id: uuid.UUID
    project_id: uuid.UUID
    file_path: str | None = None
    parsed_data: dict | None = None
    created_at: datetime | None = None


class ContractsPublic(SQLModel):
    data: list[ContractPublic]
    count: int


# 发票基础属性
class InvoiceBase(SQLModel):
    invoice_number: str = Field(min_length=1, max_length=100)  # 发票号码
    invoice_code: str = Field(min_length=1, max_length=100)  # 发票代码
    amount: float = Field(ge=0)  # 发票金额
    invoice_date: datetime | None = None  # 开票日期
    seller: str | None = Field(default=None, max_length=255)  # 销售方
    buyer: str | None = Field(default=None, max_length=255)  # 购买方
    tax_amount: float | None = Field(default=None, ge=0)  # 税额
    remark: str | None = Field(default=None, max_length=1000)  # 备注


# 发票创建模式
class InvoiceCreate(InvoiceBase):
    contract_id: uuid.UUID  # 关联的合同


# 发票更新模式
class InvoiceUpdate(InvoiceBase):
    invoice_number: str | None = Field(default=None, min_length=1, max_length=100)  # type: ignore
    invoice_code: str | None = Field(default=None, min_length=1, max_length=100)  # type: ignore
    amount: float | None = None
    invoice_date: datetime | None = None
    seller: str | None = None
    buyer: str | None = None
    tax_amount: float | None = None
    remark: str | None = None


# 数据库模型：发票
class Invoice(InvoiceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    contract_id: uuid.UUID = Field(foreign_key="contract.id", nullable=False, ondelete="CASCADE")
    contract: Contract | None = Relationship(back_populates="invoices")
    file_path: str | None = None  # 发票文件路径
    parsed_data: dict | None = Field(default=None, sa_type=JSON)  # 解析的JSON数据


# 公共响应模式：发票
class InvoicePublic(InvoiceBase):
    id: uuid.UUID
    contract_id: uuid.UUID
    file_path: str | None = None
    parsed_data: dict | None = None
    created_at: datetime | None = None


class InvoicesPublic(SQLModel):
    data: list[InvoicePublic]
    count: int
