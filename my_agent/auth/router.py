import os
import uuid
import logging
import shutil
import httpx
from datetime import datetime, timedelta
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field

from my_agent.auth import database, jwt_service, otp_service, google_oauth

logger = logging.getLogger("auth_server.router")

router = APIRouter()
security = HTTPBearer()


class SendOtpRequest(BaseModel):
    email: EmailStr
    action: Literal["login", "register"] = "login"


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    name: Optional[str] = None


class GoogleCallbackRequest(BaseModel):
    code: str
    state: str


class UpdateProfileRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt_service.verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing subject ID"
            )

        user = database.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in system"
            )
        return user
    except jwt_service.TokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except jwt_service.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/send-otp")
async def send_otp(body: SendOtpRequest):
    email = body.email.strip().lower()
    action = body.action

    user = database.get_user_by_email(email)

    if action == "register":
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản email này đã được tạo. Vui lòng chuyển sang Đăng nhập."
            )
    elif action == "login":
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản email này chưa được đăng ký. Vui lòng chọn Đăng ký."
            )
        if user.get("provider") == "google" and user.get("google_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản này được tạo bằng Google. Vui lòng đăng nhập bằng Google."
            )

    database.cleanup_expired_otps()

    if not database.check_otp_rate_limit(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Bạn đã gửi quá giới hạn 5 mã OTP trong 1 giờ. Vui lòng thử lại sau."
        )

    if database.check_otp_cooldown(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Vui lòng đợi 60 giây trước khi yêu cầu gửi lại mã mới."
        )

    otp_code = otp_service.generate_otp()
    code_hash = otp_service.hash_otp(otp_code)

    otp_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    database.save_otp(otp_id, email, code_hash, expires_at)

    sent = await otp_service.send_otp_email(email, otp_code)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gặp sự cố khi gửi email xác thực. Vui lòng kiểm tra lại cấu hình Brevo."
        )

    return {"message": "Mã xác thực OTP đã được gửi thành công. Hãy kiểm tra hòm thư của bạn."}


@router.post("/verify-otp")
async def verify_otp(body: VerifyOtpRequest):
    email = body.email.strip().lower()
    otp_input = body.code.strip()

    otp_record = database.get_latest_otp(email)
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã OTP không tồn tại hoặc đã hết hạn. Vui lòng yêu cầu mã mới."
        )

    otp_id = otp_record["id"]
    attempts = otp_record["attempts"]

    if attempts >= 5:
        database.mark_otp_used(otp_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã OTP này đã bị khóa do nhập sai quá 5 lần. Vui lòng yêu cầu mã mới."
        )

    input_hash = otp_service.hash_otp(otp_input)
    if input_hash != otp_record["code_hash"]:
        new_attempts = database.increment_otp_attempts(otp_id)

        if new_attempts >= 5:
            database.mark_otp_used(otp_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã OTP đã bị khóa do nhập sai quá 5 lần. Vui lòng yêu cầu mã mới."
            )

        remaining = 5 - new_attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã xác thực không đúng. Bạn còn {remaining} lần nhập."
        )

    user = database.get_user_by_email(email)
    if user:
        database.mark_otp_used(otp_id)
        database.update_last_login(user["id"])
        token = jwt_service.create_token(
            user_id=user["id"],
            email=user["email"],
            name=user["name"],
            provider=user["provider"],
            avatar_url=user["avatar_url"]
        )
        return {
            "token": token,
            "user": user
        }

    if not body.name or not body.name.strip():
        return {
            "status": "requires_register_name",
            "message": "Cần cung cấp tên hiển thị để hoàn tất đăng ký."
        }

    name = body.name.strip()
    if len(name) < 2 or len(name) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên hiển thị phải từ 2 đến 50 ký tự."
        )

    database.mark_otp_used(otp_id)
    user_id = str(uuid.uuid4())
    user = database.create_user(
        user_id=user_id,
        email=email,
        name=name,
        provider="email"
    )

    token = jwt_service.create_token(
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
        provider=user["provider"],
        avatar_url=user["avatar_url"]
    )
    return {
        "token": token,
        "user": user,
        "is_new_user": True
    }


@router.get("/google/url")
async def get_google_url():
    state = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    database.save_oauth_state(state, expires_at)
    url = google_oauth.get_auth_url(state)
    return {"url": url}


@router.post("/google/callback")
async def google_callback(body: GoogleCallbackRequest):
    if not database.verify_and_delete_state(body.state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State xác thực không hợp lệ. Yêu cầu đăng nhập bị từ chối chống CSRF."
        )

    try:
        tokens = await google_oauth.exchange_code(body.code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lỗi khi trao đổi mã xác thực Google: {str(e)}"
        )

    try:
        google_user = await google_oauth.get_user_info(tokens["access_token"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lỗi khi lấy thông tin người dùng Google: {str(e)}"
        )

    email = google_user["email"].strip().lower()
    google_id = google_user["id"]
    name = google_user["name"]
    picture = google_user.get("picture")

    existing_user = database.get_user_by_email(email)
    is_new_user = existing_user is None

    if existing_user:
        # Link Google identity but preserve the original registration method.
        database.merge_google_account(email, google_id, picture)
        database.update_last_login(existing_user["id"])
        user = database.get_user_by_id(existing_user["id"])
    else:
        user_id = str(uuid.uuid4())
        user = database.create_user(
            user_id=user_id,
            email=email,
            name=name,
            provider="google",
            avatar_url=picture,
            google_id=google_id
        )

    token = jwt_service.create_token(
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
        provider=user["provider"],
        avatar_url=user["avatar_url"]
    )

    return {
        "token": token,
        "user": user,
        "is_new_user": is_new_user
    }


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user


@router.put("/profile")
async def update_profile(body: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    name = body.name.strip()
    user_id = user["id"]

    updated = database.update_user_profile(user_id, name)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể cập nhật tên hiển thị trong DB."
        )

    updated_user = database.get_user_by_id(user_id)
    return updated_user


@router.delete("/account")
async def delete_account(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    email = user["email"]

    deleted = database.delete_user_data(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể xóa tài khoản người dùng trong cơ sở dữ liệu."
        )

    try:
        adk_base_url = os.getenv("ADK_BASE_URL", "http://127.0.0.1:8000")

        async with httpx.AsyncClient(timeout=5.0) as client:
            r1 = await client.delete(f"{adk_base_url}/apps/my_agent/users/{user_id}/sessions")
            logger.info(f"ADK session cleanup for {user_id}: {r1.status_code}")

            r2 = await client.delete(f"{adk_base_url}/apps/my_agent/users/{email}/sessions")
            logger.info(f"ADK session cleanup for email {email}: {r2.status_code}")

    except Exception as e:
        logger.error(f"External ADK session API call failed during account deletion: {str(e)}")

    try:
        workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        for dir_name in (user_id, email):
            target_dir = os.path.join(workspace_dir, ".adk", "artifacts", "users", dir_name)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
                logger.info(f"Successfully deleted local artifact directory: {target_dir}")
    except Exception as e:
        logger.error(f"Failed to delete local user artifact directories: {str(e)}")

    return {"message": "Tài khoản và toàn bộ dữ liệu trò chuyện đã được xóa vĩnh viễn khỏi hệ thống."}


@router.post("/logout")
async def logout():
    return {"status": "logged_out", "message": "Đăng xuất thành công."}
