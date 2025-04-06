from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# Configure OAuth
config = Config(environ=os.environ)
oauth = OAuth(config)
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Set up Jinja2 templates
templates = Jinja2Templates(directory="/Users/hlathirinaing/CS/GitHub/sfhacks-2025/templates")

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    """
    Home page with a login button.
    """
    user = request.session.get("user")
    if user:
        return templates.TemplateResponse("home.html", {"request": request, "user": user})
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login")
async def login(request: Request):
    """
    Redirects the user to the Google OAuth login page.
    """
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request):
    """
    Handles the callback from Google OAuth and retrieves user information.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        user = await oauth.google.parse_id_token(request, token)
        request.session["user"] = user
    except Exception as e:
        return {"error": str(e)}
    return RedirectResponse(url="/")

@app.get("/logout")
async def logout(request: Request):
    """
    Logs the user out by clearing the session.
    """
    request.session.pop("user", None)
    return RedirectResponse(url="/")

@app.get("/home", response_class=HTMLResponse)
async def home():
    """
    Home endpoint that displays 'Hello, World!'.
    """
    return HTMLResponse(content="<h1>Hello, World!</h1>", status_code=200)