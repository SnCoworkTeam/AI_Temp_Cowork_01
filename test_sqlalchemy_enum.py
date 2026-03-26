"""
测试SQLAlchemy枚举处理方式
深入分析为什么传递'DRAFT'而不是'draft'
"""
from enum import Enum
from sqlalchemy import Column, String, Enum as SQLEnum, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# 定义枚举（与项目中相同的方式）
class WorkflowStatus(str, Enum):
    """工作流状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

# 测试不同的列定义方式
class TestModel1(Base):
    """使用SQLEnum，默认值为枚举对象"""
    __tablename__ = "test1"
    id = Column(String, primary_key=True)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.DRAFT)

class TestModel2(Base):
    """使用SQLEnum，默认值为枚举的value"""
    __tablename__ = "test2"
    id = Column(String, primary_key=True)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.DRAFT.value)

class TestModel3(Base):
    """使用SQLEnum with values_callable"""
    __tablename__ = "test3"
    id = Column(String, primary_key=True)
    status = Column(SQLEnum(WorkflowStatus, values_callable=lambda x: [e.value for e in x]))

class TestModel4(Base):
    """使用String类型"""
    __tablename__ = "test4"
    id = Column(String, primary_key=True)
    status = Column(String(20), default="draft")

# 创建内存数据库测试
engine = create_engine("sqlite:///:memory:", echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

print("\n" + "="*80)
print("测试1: SQLEnum + 枚举对象作为默认值")
print("="*80)
try:
    obj1 = TestModel1(id="1")
    session.add(obj1)
    session.flush()
    print(f"✅ 默认值: {obj1.status}")
    print(f"   类型: {type(obj1.status)}")
    print(f"   值: {obj1.status.value if hasattr(obj1.status, 'value') else obj1.status}")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "="*80)
print("测试2: SQLEnum + 枚举的.value作为默认值")
print("="*80)
try:
    obj2 = TestModel2(id="2")
    session.add(obj2)
    session.flush()
    print(f"✅ 默认值: {obj2.status}")
    print(f"   类型: {type(obj2.status)}")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "="*80)
print("测试3: 显式传递枚举的.value")
print("="*80)
try:
    obj3 = TestModel1(id="3", status=WorkflowStatus.DRAFT.value)
    session.add(obj3)
    session.flush()
    print(f"✅ 传递的值: {obj3.status}")
    print(f"   类型: {type(obj3.status)}")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "="*80)
print("测试4: 直接传递字符串 'draft'")
print("="*80)
try:
    obj4 = TestModel1(id="4", status="draft")
    session.add(obj4)
    session.flush()
    print(f"✅ 传递的值: {obj4.status}")
    print(f"   类型: {type(obj4.status)}")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "="*80)
print("关键发现总结")
print("="*80)
print(f"WorkflowStatus.DRAFT = {WorkflowStatus.DRAFT}")
print(f"WorkflowStatus.DRAFT.name = {WorkflowStatus.DRAFT.name}")
print(f"WorkflowStatus.DRAFT.value = {WorkflowStatus.DRAFT.value}")
print(f"str(WorkflowStatus.DRAFT) = {str(WorkflowStatus.DRAFT)}")
print(f"repr(WorkflowStatus.DRAFT) = {repr(WorkflowStatus.DRAFT)}")

# 测试SQLAlchemy如何序列化枚举
print("\n" + "="*80)
print("SQLAlchemy枚举序列化测试")
print("="*80)
from sqlalchemy.types import Enum as SQLAlchemyEnum
enum_type = SQLAlchemyEnum(WorkflowStatus)
print(f"默认行为 - 枚举成员: {enum_type.process_bind_param(WorkflowStatus.DRAFT, None)}")
print(f"直接字符串: {enum_type.process_bind_param('draft', None)}")

enum_type_with_values = SQLAlchemyEnum(WorkflowStatus, values_callable=lambda x: [e.value for e in x])
print(f"使用values_callable - 枚举成员: {enum_type_with_values.process_bind_param(WorkflowStatus.DRAFT, None)}")
