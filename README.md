# AI Assistant MCP Server

MCP (Model Context Protocol) Server cho AI Assistant, được xây dựng với **FastMCP** và quản lý bằng **uv**.

## 🚀 Tính năng

- ✅ **FastMCP**: Framework hiện đại cho MCP server
- ✅ **Tools**: Các công cụ để tương tác với AI agent backend
- ✅ **Resources**: Truy cập thông tin agent và conversations
- ✅ **Prompts**: Các prompt templates có sẵn
- ✅ **Async Support**: Hoàn toàn asynchronous
- ✅ **Type Safe**: Type hints đầy đủ

## 📋 Yêu cầu

- Python 3.10+
- uv (Python package manager)
- Backend API đang chạy (port 8000)

## 🛠️ Cài đặt với UV

### 1. Cài đặt UV (nếu chưa có)

```powershell
# Windows PowerShell
irm https://astral.sh/uv/install.ps1 | iex
```

### 2. Tạo virtual environment và cài đặt dependencies

```powershell
cd MCP
uv venv
.venv\Scripts\activate
uv pip install -e .
```

hoặc cài đặt trực tiếp:

```powershell
uv pip install fastmcp python-dotenv pydantic httpx aiofiles
```

### 3. Cấu hình environment variables

```powershell
copy .env.example .env
```

Cập nhật file `.env`:

```env
BACKEND_API_URL=http://localhost:8000
OPENAI_API_KEY=your_key_here
```

## 🚀 Chạy MCP Server

### Với UV (khuyên dùng)

```powershell
uv run server.py
```

hoặc

```powershell
.venv\Scripts\activate
python server.py
```

### Development mode

```powershell
uv run server.py --reload
```

## 📡 MCP Server Capabilities

### Tools (Công cụ)

1. **chat_with_agent**
   - Gửi tin nhắn đến AI agent
   - Tham số: `message`, `conversation_id` (optional), `user_id` (optional)

2. **get_conversation_history**
   - Lấy lịch sử hội thoại
   - Tham số: `conversation_id`

3. **get_agent_status**
   - Lấy trạng thái hiện tại của agent
   - Không cần tham số

4. **get_agent_graph**
   - Lấy cấu trúc LangGraph workflow
   - Không cần tham số

5. **delete_conversation**
   - Xóa một hội thoại
   - Tham số: `conversation_id`

6. **health_check**
   - Kiểm tra sức khỏe backend API
   - Không cần tham số

### Resources (Tài nguyên)

1. **agent://info**
   - Thông tin chi tiết về agent

2. **agent://status**
   - Trạng thái hoạt động của agent

3. **conversations://list**
   - Danh sách các hội thoại (placeholder)

### Prompts (Prompt Templates)

1. **casual_chat** - Trò chuyện thông thường
2. **technical_help** - Hỗ trợ kỹ thuật
3. **creative_writing** - Viết sáng tạo
4. **code_review** - Review code

## 💡 Ví dụ sử dụng

### Từ MCP Client

```python
# Sử dụng tool chat_with_agent
result = await client.call_tool(
    "chat_with_agent",
    arguments={
        "message": "What is LangGraph?",
        "user_id": "user_123"
    }
)

# Lấy thông tin agent
info = await client.read_resource("agent://info")

# Sử dụng prompt
messages = await client.get_prompt("technical_help")
```

### Cấu hình trong Claude Desktop

Thêm vào `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-assistant": {
      "command": "uv",
      "args": [
        "--directory",
        "F:\\UIT\\SE347\\Seminar\\MCP",
        "run",
        "server.py"
      ],
      "env": {
        "BACKEND_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Cấu hình trong Cline (VS Code)

Thêm vào settings:

```json
{
  "mcp.servers": {
    "ai-assistant": {
      "command": "uv",
      "args": [
        "--directory",
        "F:\\UIT\\SE347\\Seminar\\MCP",
        "run",
        "server.py"
      ],
      "env": {
        "BACKEND_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## 🧪 Testing

### Test với MCP Inspector

```powershell
# Cài đặt MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Chạy inspector
mcp-inspector uv --directory F:\UIT\SE347\Seminar\MCP run server.py
```

### Test với curl

```powershell
# Test backend trước
curl http://localhost:8000/health

# Rồi mới chạy MCP server
uv run server.py
```

## 📁 Cấu trúc Project

```
MCP/
├── server.py              # Main MCP server file
├── pyproject.toml         # Project configuration (uv/pip)
├── .env                   # Environment variables
├── .env.example           # Example env file
├── README.md              # Documentation
└── .gitignore            # Git ignore rules
```

## 🔧 Phát triển thêm

### Thêm Tool mới

```python
@mcp.tool()
async def your_new_tool(param: str) -> Dict[str, Any]:
    """
    Description of your tool.
    
    Args:
        param: Parameter description
        
    Returns:
        Result description
    """
    # Your implementation
    return {"result": "data"}
```

### Thêm Resource mới

```python
@mcp.resource("custom://resource")
async def your_resource() -> str:
    """
    Get custom resource data.
    """
    return "Resource content"
```

### Thêm Prompt mới

```python
@mcp.prompt()
async def your_prompt() -> List[Dict[str, str]]:
    """
    Custom prompt template.
    """
    return [
        {
            "role": "user",
            "content": "Your prompt content"
        }
    ]
```

## 📚 Tài liệu

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [UV Documentation](https://docs.astral.sh/uv/)

## 🐛 Troubleshooting

### Lỗi "Backend is not healthy"
- Đảm bảo Backend API đang chạy trên port 8000
- Check: `curl http://localhost:8000/health`

### Lỗi import fastmcp
```powershell
uv pip install fastmcp
```

### Lỗi connection refused
- Kiểm tra BACKEND_API_URL trong .env
- Đảm bảo không có firewall block

### UV command not found
```powershell
# Reinstall UV
irm https://astral.sh/uv/install.ps1 | iex
```

## 📝 License

MIT License
