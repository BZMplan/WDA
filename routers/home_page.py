from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

router = APIRouter(
    tags=["home_page"]
)


templates = Jinja2Templates(directory="templates")


services = [
    {
        "title": "数据分析",
        # 使用先进的Python算法处理和分析天气数据，提取有价值的洞察
        "description": "从原始数据中提炼有价值洞察的过程",
        "icon": "📊"
    },
    {
        "title": "数据可视化",
        # 通过精美的图表和图形直观展示天气数据，帮助您更好地理解数据
        "description": "将数据转化为直观图表与图形的艺术",
        "icon": "🖥️"
    },
    {   
        "title": "开源项目",
        # 完全开源的解决方案，欢迎社区贡献和协作，共同改进天气数据分析
        "description": "代码公开，供所有人使用、修改与共享的协作模式",
        "icon": "🔓"
    }
]

@router.get("/",response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request":request,
            "title":"气象数据分析及可视化平台",
            "services": services
        }
    )

@router.post("/contact",response_class=HTMLResponse)
async def contact(
    request:Request,
    name:str = Form(...),
    email:str = Form(...),
    message:str = Form(...)
):
    return templates.TemplateResponse(
        "contact_success.html",
        {
            "request":request,
            "name":name,
            "email":email,
            "message":message
        }
    )
    