"""
数据库连接管理
"""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# 当使用 sqlite 时，提前创建目录并将路径转换为绝对路径，避免 “unable to open database file”
database_url = settings.DATABASE_URL
if database_url.startswith("sqlite"):
    url = make_url(database_url)
    db_path = url.database
    if db_path:
        abs_path = Path(db_path).expanduser().resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        url = url.set(database=str(abs_path))
        database_url = url.render_as_string(hide_password=False)

# 创建数据库引擎
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

