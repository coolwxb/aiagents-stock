"""
用户管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from app.api.response import success_response, error_response
from app.config import settings
from app.core.security import create_access_token, oauth2_scheme


router = APIRouter()

@router.post("/login")
async def login(user_data: dict):
    """登录"""
    username = user_data.get("username")
    password = user_data.get("password")
    if username == "admin" and password == "123456":
        # 生成token
        token = create_access_token(data={"sub": username})
        return success_response(msg="登录成功", data={"token": token})
    else:
        return error_response(msg="登录失败,用户名或密码错误", data={"token": None})

@router.get("/info")
async def info(token: str = Depends(oauth2_scheme)):
    """获取用户信息"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username == "admin":
            return success_response(msg="获取用户信息成功", data={"roles": ["admin"], "name": "Super Admin", "avatar": "https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif"})
        else:
            return error_response(msg="获取用户信息失败", data={"roles": [], "name": None, "avatar": None})
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={
                "code": 401,
                "msg": "Token已过期，请重新登录",
                "data": None
            }
        )
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "code": 401,
                "msg": f"Token验证失败: {str(e)}",
                "data": None
            }
        )

@router.post("/logout")
async def logout():
    """登出"""
    return success_response(msg="登出成功")