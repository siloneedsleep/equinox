import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from backend.database import KeyDBClient
from config.settings import CLIENT_ID, CLIENT_SECRET, OAUTH2_REDIRECT_URI

app = FastAPI(title="Equinox Quản Gia - OAuth2 Web Server")
db = KeyDBClient()

@app.get("/")
async def root():
    # URL mặc định để Render kiểm tra "Nhịp tim" chống ngủ đông
    return {"status": "online", "message": "Equinox Network - Render Core Active"}

@app.get("/callback")
async def callback(code: str = None, state: str = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code.")
    
    # Giao tiếp siêu tốc với Discord API để đổi Token
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OAUTH2_REDIRECT_URI
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = await client.post("https://discord.com/api/v10/oauth2/token", data=data, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange token.")
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        # Lấy User ID của người dùng vừa xác thực
        user_response = await client.get("https://discord.com/api/v10/users/@me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user profile.")
            
        user_info = user_response.json()
        user_id = user_info.get("id")

        # Đẩy thẳng dữ liệu vào Redis để Bot chính (Presence Proxy) xử lý
        await db.sync_oauth_session(user_id, token_data)
        
    return JSONResponse(content={
        "status": "success",
        "message": f"Xác thực thành công cho tài khoản {user_info.get('username')}! Bạn có thể đóng tab này và quay lại Discord."
    })
