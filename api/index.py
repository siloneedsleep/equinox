from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import os
import json
import time
import redis.asyncio as redis

# Cấu hình từ Vercel Environment Variables
LUMINOUS_CLIENT_ID = os.environ.get("LUMINOUS_CLIENT_ID")
LUMINOUS_CLIENT_SECRET = os.environ.get("LUMINOUS_CLIENT_SECRET")
TENEBRIS_CLIENT_ID = os.environ.get("TENEBRIS_CLIENT_ID")
TENEBRIS_CLIENT_SECRET = os.environ.get("TENEBRIS_CLIENT_SECRET")
OAUTH2_REDIRECT_URI = os.environ.get("OAUTH2_REDIRECT_URI")
REDIS_URI = os.environ.get("REDIS_URI")

app = FastAPI(title="Equinox OAuth2 Callback", version="2.0")

@app.get("/callback", response_class=HTMLResponse)
async def oauth2_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state", "luminous")

    if not code:
        raise HTTPException(status_code=400, detail="Thiếu mã code. Vui lòng thử lại thông qua Discord.")

    if state == "luminous":
        cid, secret = LUMINOUS_CLIENT_ID, LUMINOUS_CLIENT_SECRET
    else:
        cid, secret = TENEBRIS_CLIENT_ID, TENEBRIS_CLIENT_SECRET

    async with httpx.AsyncClient() as client:
        # 1. Trao đổi Token
        token_data = {
            "client_id": cid,
            "client_secret": secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OAUTH2_REDIRECT_URI
        }

        token_resp = await client.post(
            "https://discord.com/api/v10/oauth2/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if token_resp.status_code != 200:
            return HTMLResponse(f"<h1>❌ Lỗi: Không thể lấy token từ Discord.</h1><p>{token_resp.text}</p>", status_code=500)

        token_json = token_resp.json()
        access_token = token_json.get("access_token")

        # 2. Lấy User Info
        user_resp = await client.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_resp.status_code != 200:
            return HTMLResponse("<h1>❌ Lỗi: Không thể lấy thông tin người dùng.</h1>", status_code=500)

        user_data = user_resp.json()
        user_id = user_data["id"]

        # 3. Lưu vào Redis bằng pipeline để tăng tốc
        r = redis.from_url(REDIS_URI, decode_responses=True)
        try:
            async with r.pipeline(transaction=True) as pipe:
                pipe.hset(f"oauth:{user_id}", state, json.dumps({
                    "access_token": access_token,
                    "refresh_token": token_json.get("refresh_token"),
                    "scopes": token_json.get("scope"),
                    "at": int(time.time())
                }))
                # Bắn tín hiệu Pub/Sub để bot biết user đã đăng nhập xong (Tùy chọn cho UI/UX mượt hơn)
                pipe.publish("equinox_oauth", json.dumps({"user_id": user_id, "state": state}))
                await pipe.execute()
        finally:
            await r.aclose()

    # 4. Trả về HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Thành công | Equinox Network</title>
        <style>
            body {{ background-color: #2b2d31; color: white; text-align: center; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding-top: 100px; }}
            h1 {{ color: #2ecc71; font-size: 2.5em; }}
            p {{ color: #a3a6aa; font-size: 1.1em; }}
            .container {{ max-width: 500px; margin: 0 auto; background: #1e1f22; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
            .highlight {{ color: #fce883; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 THÀNH CÔNG!</h1>
            <p>Xác thực OAuth2 cho <span class="highlight">{state.upper()}</span> đã hoàn tất.</p>
            <p>Hệ thống đã ghi nhận quyền truy cập Profile của bạn.</p>
            <p>Bạn có thể đóng trang này và quay lại ứng dụng Discord.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
