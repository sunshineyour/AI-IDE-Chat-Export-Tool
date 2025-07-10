"""
配置管理器 - 统一管理cursor-view项目的路径配置

这个模块负责：
1. 读取和写入用户自定义路径配置
2. 提供默认路径回退机制
3. 支持配置文件的创建和初始化
4. 处理跨平台路径格式兼容性
"""

import json
import logging
import os
import platform
import pathlib
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器类"""
    
    CONFIG_FILE = "config.json"
    CONFIG_VERSION = "1.0"
    
    # 默认路径配置
    DEFAULT_PATHS = {
        "cursor": None,
        "augment": None, 
        "cursor-augment": None,
        "idea-augment": None,
        "pycharm-augment": None
    }
    
    def __init__(self, config_file_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file_path: 配置文件路径，默认为项目根目录下的config.json
        """
        self.logger = logging.getLogger(__name__)
        
        # 确定配置文件路径
        if config_file_path:
            self.config_file_path = Path(config_file_path)
        else:
            # 默认使用项目根目录下的config.json
            current_dir = Path(__file__).parent
            project_root = current_dir.parent  # 从backend目录回到项目根目录
            self.config_file_path = project_root / self.CONFIG_FILE
        
        self.logger.info(f"配置文件路径: {self.config_file_path}")
        
        # 初始化配置
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_file_path.exists():
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                    self.logger.info("成功加载配置文件")
                    
                # 验证配置文件格式
                if not self._validate_config():
                    self.logger.warning("配置文件格式无效，将重新初始化")
                    self._create_default_config()
            else:
                self.logger.info("配置文件不存在，创建默认配置")
                self._create_default_config()
                
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            self.logger.info("使用默认配置")
            self._create_default_config()
    
    def _validate_config(self) -> bool:
        """验证配置文件格式"""
        if not isinstance(self._config, dict):
            return False
            
        required_keys = ["version", "paths", "created_at", "updated_at"]
        for key in required_keys:
            if key not in self._config:
                return False
        
        if not isinstance(self._config["paths"], dict):
            return False
            
        # 检查所有必需的数据源路径键
        for data_source in self.DEFAULT_PATHS.keys():
            if data_source not in self._config["paths"]:
                self._config["paths"][data_source] = None
                
        return True
    
    def _create_default_config(self) -> None:
        """创建默认配置"""
        current_time = datetime.now().isoformat()
        
        self._config = {
            "version": self.CONFIG_VERSION,
            "paths": self.DEFAULT_PATHS.copy(),
            "created_at": current_time,
            "updated_at": current_time
        }
        
        # 尝试保存默认配置
        self._save_config()
    
    def _save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 更新修改时间
            self._config["updated_at"] = datetime.now().isoformat()
            
            # 确保目录存在
            self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入配置文件
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            self.logger.info("配置文件保存成功")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get_path(self, data_source: str) -> Optional[str]:
        """
        获取指定数据源的路径配置
        
        Args:
            data_source: 数据源标识
            
        Returns:
            str: 配置的路径，如果未配置则返回None
        """
        if not self._config or "paths" not in self._config:
            return None
            
        return self._config["paths"].get(data_source)
    
    def set_path(self, data_source: str, path: Optional[str]) -> bool:
        """
        设置指定数据源的路径配置
        
        Args:
            data_source: 数据源标识
            path: 路径字符串，None表示使用默认路径
            
        Returns:
            bool: 设置是否成功
        """
        if not self._config:
            self._create_default_config()
        
        if data_source not in self.DEFAULT_PATHS:
            self.logger.error(f"不支持的数据源: {data_source}")
            return False
        
        self._config["paths"][data_source] = path
        return self._save_config()
    
    def get_all_paths(self) -> Dict[str, Optional[str]]:
        """
        获取所有数据源的路径配置
        
        Returns:
            Dict: 所有数据源的路径配置
        """
        if not self._config or "paths" not in self._config:
            return self.DEFAULT_PATHS.copy()
            
        return self._config["paths"].copy()
    
    def set_all_paths(self, paths: Dict[str, Optional[str]]) -> bool:
        """
        批量设置所有数据源的路径配置
        
        Args:
            paths: 路径配置字典
            
        Returns:
            bool: 设置是否成功
        """
        if not self._config:
            self._create_default_config()
        
        # 验证输入的数据源
        for data_source in paths.keys():
            if data_source not in self.DEFAULT_PATHS:
                self.logger.error(f"不支持的数据源: {data_source}")
                return False
        
        # 更新配置
        self._config["paths"].update(paths)
        return self._save_config()
    
    def reset_path(self, data_source: str) -> bool:
        """
        重置指定数据源的路径为默认值
        
        Args:
            data_source: 数据源标识
            
        Returns:
            bool: 重置是否成功
        """
        return self.set_path(data_source, None)
    
    def reset_all_paths(self) -> bool:
        """
        重置所有数据源的路径为默认值
        
        Returns:
            bool: 重置是否成功
        """
        return self.set_all_paths(self.DEFAULT_PATHS.copy())
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        获取配置文件信息
        
        Returns:
            Dict: 配置文件信息
        """
        if not self._config:
            return {}
            
        return {
            "version": self._config.get("version"),
            "created_at": self._config.get("created_at"),
            "updated_at": self._config.get("updated_at"),
            "config_file_path": str(self.config_file_path),
            "config_file_exists": self.config_file_path.exists()
        }
    
    def get_default_path(self, data_source: str) -> Optional[str]:
        """
        获取指定数据源的默认路径
        
        Args:
            data_source: 数据源标识
            
        Returns:
            str: 默认路径，如果不支持则返回None
        """
        # 这里调用各个提取器的默认路径获取方法
        try:
            if data_source == "cursor":
                return str(self._get_cursor_default_path())
            elif data_source == "augment":
                return str(self._get_vscode_default_path())
            elif data_source == "cursor-augment":
                return str(self._get_cursor_augment_default_path())
            elif data_source == "idea-augment":
                return str(self._get_idea_default_path())
            elif data_source == "pycharm-augment":
                return str(self._get_pycharm_default_path())
            else:
                return None
        except Exception as e:
            self.logger.error(f"获取{data_source}默认路径失败: {e}")
            return None
    
    def _get_cursor_default_path(self) -> pathlib.Path:
        """获取Cursor默认路径"""
        h = pathlib.Path.home()
        s = platform.system()
        if s == "Darwin":   
            return h / "Library" / "Application Support" / "Cursor"
        if s == "Windows":  
            return h / "AppData" / "Roaming" / "Cursor"
        if s == "Linux":    
            return h / ".config" / "Cursor"
        raise RuntimeError(f"Unsupported OS: {s}")
    
    def _get_vscode_default_path(self) -> pathlib.Path:
        """获取VSCode默认路径"""
        home = pathlib.Path.home()
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return home / "Library" / "Application Support" / "Code" / "User" / "workspaceStorage"
        elif system == "Windows":
            return home / "AppData" / "Roaming" / "Code" / "User" / "workspaceStorage"
        elif system == "Linux":
            return home / ".config" / "Code" / "User" / "workspaceStorage"
        else:
            raise RuntimeError(f"Unsupported OS: {system}")
    
    def _get_cursor_augment_default_path(self) -> pathlib.Path:
        """获取Cursor Augment默认路径"""
        home = pathlib.Path.home()
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return home / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage"
        elif system == "Windows":
            return home / "AppData" / "Roaming" / "Cursor" / "User" / "workspaceStorage"
        elif system == "Linux":
            return home / ".config" / "Cursor" / "User" / "workspaceStorage"
        else:
            raise RuntimeError(f"Unsupported OS: {system}")

    def _get_idea_default_path(self) -> Optional[pathlib.Path]:
        """获取IDEA默认路径"""
        system = platform.system()

        if system == "Windows":
            appdata = os.environ.get('APPDATA')
            if appdata:
                jetbrains_dir = pathlib.Path(appdata) / "JetBrains"
                if jetbrains_dir.exists():
                    idea_dirs = [d for d in jetbrains_dir.iterdir() if d.is_dir() and d.name.startswith('IntelliJIdea')]
                    if idea_dirs:
                        return sorted(idea_dirs)[-1]  # 选择最新版本

        elif system == "Darwin":  # macOS
            home = pathlib.Path.home()
            jetbrains_dir = home / "Library" / "Application Support" / "JetBrains"
            if jetbrains_dir.exists():
                idea_dirs = [d for d in jetbrains_dir.iterdir() if d.is_dir() and d.name.startswith('IntelliJIdea')]
                if idea_dirs:
                    return sorted(idea_dirs)[-1]

        elif system == "Linux":
            home = pathlib.Path.home()
            jetbrains_dir = home / ".config" / "JetBrains"
            if jetbrains_dir.exists():
                idea_dirs = [d for d in jetbrains_dir.iterdir() if d.is_dir() and d.name.startswith('IntelliJIdea')]
                if idea_dirs:
                    return sorted(idea_dirs)[-1]

        return None

    def _get_pycharm_default_path(self) -> Optional[pathlib.Path]:
        """获取PyCharm默认路径"""
        system = platform.system()

        if system == "Windows":
            appdata = os.environ.get('APPDATA')
            if appdata:
                jetbrains_dir = pathlib.Path(appdata) / "JetBrains"
                if jetbrains_dir.exists():
                    pycharm_dirs = [d for d in jetbrains_dir.iterdir() if d.is_dir() and d.name.startswith('PyCharm')]
                    if pycharm_dirs:
                        return sorted(pycharm_dirs)[-1]  # 选择最新版本

        elif system == "Darwin":  # macOS
            home = pathlib.Path.home()
            jetbrains_dir = home / "Library" / "Application Support" / "JetBrains"
            if jetbrains_dir.exists():
                pycharm_dirs = [d for d in jetbrains_dir.iterdir() if d.is_dir() and d.name.startswith('PyCharm')]
                if pycharm_dirs:
                    return sorted(pycharm_dirs)[-1]

        elif system == "Linux":
            home = pathlib.Path.home()
            jetbrains_dir = home / ".config" / "JetBrains"
            if jetbrains_dir.exists():
                pycharm_dirs = [d for d in jetbrains_dir.iterdir() if d.is_dir() and d.name.startswith('PyCharm')]
                if pycharm_dirs:
                    return sorted(pycharm_dirs)[-1]

        return None
