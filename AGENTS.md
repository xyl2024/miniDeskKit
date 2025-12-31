# AGENTS.md - miniDeskKit 开发指南

## 开发要求

- 每次生成完代码，需要进行代码检查与格式化
- 如果需要添加依赖，则使用 `uv add package-name` 的方式，不要手动修改 `pyproject.toml` 文件
- 生成完代码后，无需进行运行测试

## 项目概述

miniDeskKit 是一个基于 PySide6 的桌面小部件应用程序，用于在 Windows 上显示系统监控和天气小部件。该应用程序使用无边框半透明窗口，并集成了系统托盘功能。

## 构建、代码检查和测试命令

### 运行应用程序
```bash
uv run src/main.py
```

### 代码检查和格式化
```bash
# 对整个项目运行 ruff linter
uv run ruff check src/

# 使用自动修复运行 ruff
uv run ruff check --fix src/

# 使用 ruff 格式化代码
uv run ruff format src/

# 检查单个文件
uv run ruff check src/utils/logger.py

# 格式化单个文件
uv run ruff format src/utils/logger.py
```

## 代码规范

### 命名规范
- **类名**: PascalCase (如 `SystemMonitorWidget`, `ConfigManager`)
- **函数名/方法名**: snake_case (如 `setup_window`, `update_initial_info`)
- **变量名**: snake_case (如 `cpu_label`, `monitored_disks`)
- **常量**: UPPER_SNAKE_CASE (如 `_logger_instance`)
- **私有方法**: 以 `_` 前缀开头 (如 `_check_hefeng_api_config`)

### 导入规范
- 使用绝对导入，从项目根目录开始 (如 `from utils.config_manager import ConfigManager`)
- 标准库导入放在最前面
- 第三方库导入放在中间
- 本地项目导入放在最后
- 每组导入之间用空行分隔

### 类型提示
- 所有公共函数和方法都应该使用类型提示
- 示例:
```python
def get_window_position(self) -> QPoint:
    """获取窗口位置"""
    pos = self.config.get("window", {}).get("position", {"x": 100, "y": 100})
    return QPoint(pos["x"], pos["y"])
```

### 文档字符串
- 所有公共方法、类和模块都应包含中文 docstring
- 使用简洁的描述说明函数用途
- 示例:
```python
def setup_window(self):
    """设置窗口属性"""
```

### 错误处理
- 使用 try-except 块处理可能抛出异常的代码
- 捕获具体的异常类型，避免使用裸 `except Exception`
- 记录错误日志而不是 print
- 示例:
```python
try:
    with open(self.config_file, "w", encoding="utf-8") as f:
        json.dump(self.config, f, ensure_ascii=False, indent=2)
except Exception as e:
    print(f"保存配置失败: {e}")
```

### PySide6/Qt 编码规范
- 所有 QWidget 子类在 `__init__` 中调用 `super().__init__()`
- 使用信号槽机制进行组件间通信
- 在 `closeEvent` 中清理资源（停止 worker 线程等）
- 示例:
```python
def closeEvent(self, event):
    """窗口关闭事件"""
    if self.worker:
        self.worker.stop()
        self.worker.wait()
    event.accept()
```

### 项目结构
- `src/` - 主要源代码目录
  - `main.py` - 应用程序入口
  - `utils/` - 工具模块 (logger, config_manager, utils)
  - `system_monitor/` - 系统监控模块
  - `weather/` - 天气相关模块
- `configs/` - 配置文件目录
- `.logs/` - 日志文件目录

### 配置管理
- 使用 `ConfigManager` 类统一管理所有配置
- 配置文件默认存储在 `configs/window_config.json`
- 获取配置使用 `get_*_config()` 方法
- 示例:
```python
self.config_manager = ConfigManager()
self.progress_config = self.config_manager.get_progress_bar_config()
```

### 日志记录
- 使用 `utils.logger` 中的 `logger` 实例
- 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
- 示例:
```python
from utils.logger import logger
logger.info("退出应用")
logger.error(f"天气组件错误: {error_msg}")
```

### 线程安全
- 使用 QThread 进行后台任务（如数据获取）
- 使用信号槽机制传递数据，避免直接操作 UI
- 在 closeEvent 中正确停止和等待线程结束
- 示例:
```python
self.worker = SystemInfoWorker(interval, disks)
self.worker.system_percent_updated.connect(self.update_all_system_info)
self.worker.start()
```

### 布局和样式
- 使用 QVBoxLayout, QHBoxLayout 等布局管理器
- 通过 `setContentsMargins()` 和 `setSpacing()` 控制间距
- 使用 StyleManager 统一管理样式
- 避免硬编码颜色和尺寸，使用配置文件

### 单元测试（如果添加）
- 目前项目不要求运行测试
- 如需添加测试，使用 pytest 框架
- 测试文件放在 `tests/` 目录下
- 测试命令: `uv run pytest tests/`
- 运行单个测试: `uv run pytest tests/test_module.py::test_function`

### 代码质量
- 遵循 PEP 8 规范
- 使用 ruff 进行代码检查和格式化
- 每次修改代码后运行 `uv run ruff check --fix src/` 和 `uv run ruff format src/`
