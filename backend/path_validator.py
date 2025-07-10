"""
路径验证器 - 验证cursor-view项目中各种数据源的路径有效性

这个模块负责：
1. 验证路径是否存在且可访问
2. 检查路径是否包含有效的数据源文件
3. 提供详细的验证结果和错误信息
4. 支持不同数据源的特定验证逻辑
"""

import os
import logging
import pathlib
import sqlite3
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """路径验证结果"""
    is_valid: bool
    path: str
    data_source: str
    message: str
    details: Optional[Dict[str, Any]] = None
    found_files: Optional[List[str]] = None

class PathValidator:
    """路径验证器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_path(self, data_source: str, path: str) -> ValidationResult:
        """
        验证指定数据源的路径
        
        Args:
            data_source: 数据源标识
            path: 要验证的路径
            
        Returns:
            ValidationResult: 验证结果
        """
        self.logger.info(f"验证{data_source}数据源路径: {path}")
        
        # 基础路径检查
        if not path:
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source=data_source,
                message="路径不能为空"
            )
        
        path_obj = Path(path)
        
        # 检查路径是否存在
        if not path_obj.exists():
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source=data_source,
                message=f"路径不存在: {path}"
            )
        
        # 检查是否为目录
        if not path_obj.is_dir():
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source=data_source,
                message=f"路径不是目录: {path}"
            )
        
        # 根据数据源类型进行特定验证
        if data_source == "cursor":
            return self._validate_cursor_path(path)
        elif data_source == "augment":
            return self._validate_vscode_augment_path(path)
        elif data_source == "cursor-augment":
            return self._validate_cursor_augment_path(path)
        elif data_source == "idea-augment":
            return self._validate_idea_augment_path(path)
        elif data_source == "pycharm-augment":
            return self._validate_pycharm_augment_path(path)
        else:
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source=data_source,
                message=f"不支持的数据源类型: {data_source}"
            )
    
    def _validate_cursor_path(self, path: str) -> ValidationResult:
        """验证Cursor路径"""
        path_obj = Path(path)
        found_files = []
        details = {}
        
        try:
            # 检查Cursor特有的目录结构
            user_dir = path_obj / "User"
            if user_dir.exists():
                found_files.append("User/")
                details["user_dir"] = True
                
                # 检查workspaceStorage
                workspace_storage = user_dir / "workspaceStorage"
                if workspace_storage.exists():
                    found_files.append("User/workspaceStorage/")
                    details["workspace_storage"] = True
                    
                    # 统计workspace数量
                    workspaces = [d for d in workspace_storage.iterdir() if d.is_dir()]
                    details["workspace_count"] = len(workspaces)
                    
                    if workspaces:
                        # 检查是否有state.vscdb文件
                        vscdb_count = 0
                        for workspace in workspaces:
                            vscdb_file = workspace / "state.vscdb"
                            if vscdb_file.exists():
                                vscdb_count += 1
                        
                        details["vscdb_count"] = vscdb_count
                        
                        if vscdb_count > 0:
                            found_files.append(f"{vscdb_count} state.vscdb files")
                            return ValidationResult(
                                is_valid=True,
                                path=path,
                                data_source="cursor",
                                message=f"有效的Cursor路径，找到{len(workspaces)}个工作区，{vscdb_count}个数据库文件",
                                details=details,
                                found_files=found_files
                            )
            
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source="cursor",
                message="未找到有效的Cursor数据文件",
                details=details,
                found_files=found_files
            )
            
        except Exception as e:
            self.logger.error(f"验证Cursor路径时出错: {e}")
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source="cursor",
                message=f"验证过程中出错: {str(e)}"
            )
    
    def _validate_vscode_augment_path(self, path: str) -> ValidationResult:
        """验证VSCode Augment路径"""
        path_obj = Path(path)
        found_files = []
        details = {}
        
        try:
            # 检查workspaceStorage目录
            if not path_obj.name == "workspaceStorage":
                return ValidationResult(
                    is_valid=False,
                    path=path,
                    data_source="augment",
                    message="路径应该指向VSCode的workspaceStorage目录"
                )
            
            # 统计workspace数量
            workspaces = [d for d in path_obj.iterdir() if d.is_dir()]
            details["workspace_count"] = len(workspaces)
            
            augment_data_count = 0
            for workspace in workspaces:
                vscdb_file = workspace / "state.vscdb"
                if vscdb_file.exists():
                    # 检查是否包含Augment数据
                    if self._check_augment_data_in_vscdb(vscdb_file):
                        augment_data_count += 1
            
            details["augment_workspace_count"] = augment_data_count
            
            if augment_data_count > 0:
                found_files.append(f"{augment_data_count} workspaces with Augment data")
                return ValidationResult(
                    is_valid=True,
                    path=path,
                    data_source="augment",
                    message=f"有效的VSCode Augment路径，找到{augment_data_count}个包含Augment数据的工作区",
                    details=details,
                    found_files=found_files
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    path=path,
                    data_source="augment",
                    message="未找到包含Augment数据的工作区",
                    details=details,
                    found_files=found_files
                )
                
        except Exception as e:
            self.logger.error(f"验证VSCode Augment路径时出错: {e}")
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source="augment",
                message=f"验证过程中出错: {str(e)}"
            )
    
    def _validate_cursor_augment_path(self, path: str) -> ValidationResult:
        """验证Cursor Augment路径"""
        path_obj = Path(path)
        found_files = []
        details = {}
        
        try:
            # 检查workspaceStorage目录
            if not path_obj.name == "workspaceStorage":
                return ValidationResult(
                    is_valid=False,
                    path=path,
                    data_source="cursor-augment",
                    message="路径应该指向Cursor的workspaceStorage目录"
                )
            
            # 统计workspace数量
            workspaces = [d for d in path_obj.iterdir() if d.is_dir()]
            details["workspace_count"] = len(workspaces)
            
            augment_data_count = 0
            for workspace in workspaces:
                vscdb_file = workspace / "state.vscdb"
                if vscdb_file.exists():
                    # 检查是否包含Augment数据
                    if self._check_augment_data_in_vscdb(vscdb_file):
                        augment_data_count += 1
            
            details["augment_workspace_count"] = augment_data_count
            
            if augment_data_count > 0:
                found_files.append(f"{augment_data_count} workspaces with Augment data")
                return ValidationResult(
                    is_valid=True,
                    path=path,
                    data_source="cursor-augment",
                    message=f"有效的Cursor Augment路径，找到{augment_data_count}个包含Augment数据的工作区",
                    details=details,
                    found_files=found_files
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    path=path,
                    data_source="cursor-augment",
                    message="未找到包含Augment数据的工作区",
                    details=details,
                    found_files=found_files
                )
                
        except Exception as e:
            self.logger.error(f"验证Cursor Augment路径时出错: {e}")
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source="cursor-augment",
                message=f"验证过程中出错: {str(e)}"
            )
    
    def _validate_idea_augment_path(self, path: str) -> ValidationResult:
        """验证IDEA Augment路径"""
        path_obj = Path(path)
        found_files = []
        details = {}
        
        try:
            # 检查是否为IDEA配置目录
            if not path_obj.name.startswith('IntelliJIdea'):
                return ValidationResult(
                    is_valid=False,
                    path=path,
                    data_source="idea-augment",
                    message="路径应该指向IntelliJ IDEA配置目录"
                )
            
            # 检查options目录
            options_dir = path_obj / "options"
            if options_dir.exists():
                found_files.append("options/")
                details["options_dir"] = True
                
                # 检查recentProjects.xml
                recent_projects_file = options_dir / "recentProjects.xml"
                if recent_projects_file.exists():
                    found_files.append("options/recentProjects.xml")
                    details["recent_projects_file"] = True
                    
                    # 查找包含Augment数据的项目
                    augment_projects = self._find_idea_augment_projects(recent_projects_file)
                    details["augment_project_count"] = len(augment_projects)
                    
                    if augment_projects:
                        found_files.extend([f"Project: {proj}" for proj in augment_projects[:3]])  # 只显示前3个
                        return ValidationResult(
                            is_valid=True,
                            path=path,
                            data_source="idea-augment",
                            message=f"有效的IDEA Augment路径，找到{len(augment_projects)}个包含Augment数据的项目",
                            details=details,
                            found_files=found_files
                        )
            
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source="idea-augment",
                message="未找到有效的IDEA Augment数据",
                details=details,
                found_files=found_files
            )
            
        except Exception as e:
            self.logger.error(f"验证IDEA Augment路径时出错: {e}")
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source="idea-augment",
                message=f"验证过程中出错: {str(e)}"
            )
    
    def _validate_pycharm_augment_path(self, path: str) -> ValidationResult:
        """验证PyCharm Augment路径"""
        path_obj = Path(path)
        found_files = []
        details = {}
        
        try:
            # 检查是否为PyCharm配置目录
            if not path_obj.name.startswith('PyCharm'):
                return ValidationResult(
                    is_valid=False,
                    path=path,
                    data_source="pycharm-augment",
                    message="路径应该指向PyCharm配置目录"
                )
            
            # 检查options目录
            options_dir = path_obj / "options"
            if options_dir.exists():
                found_files.append("options/")
                details["options_dir"] = True
                
                # 检查recentProjects.xml
                recent_projects_file = options_dir / "recentProjects.xml"
                if recent_projects_file.exists():
                    found_files.append("options/recentProjects.xml")
                    details["recent_projects_file"] = True
                    
                    # 查找包含Augment数据的项目
                    augment_projects = self._find_pycharm_augment_projects(recent_projects_file)
                    details["augment_project_count"] = len(augment_projects)
                    
                    if augment_projects:
                        found_files.extend([f"Project: {proj}" for proj in augment_projects[:3]])  # 只显示前3个
                        return ValidationResult(
                            is_valid=True,
                            path=path,
                            data_source="pycharm-augment",
                            message=f"有效的PyCharm Augment路径，找到{len(augment_projects)}个包含Augment数据的项目",
                            details=details,
                            found_files=found_files
                        )
            
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source="pycharm-augment",
                message="未找到有效的PyCharm Augment数据",
                details=details,
                found_files=found_files
            )
            
        except Exception as e:
            self.logger.error(f"验证PyCharm Augment路径时出错: {e}")
            return ValidationResult(
                is_valid=False,
                path=path,
                data_source="pycharm-augment",
                message=f"验证过程中出错: {str(e)}"
            )

    def _check_augment_data_in_vscdb(self, vscdb_file: Path) -> bool:
        """检查VSCode数据库文件是否包含Augment数据"""
        try:
            con = sqlite3.connect(f"file:{vscdb_file}?mode=ro", uri=True)
            cur = con.cursor()

            # 检查是否有ItemTable
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ItemTable'")
            if not cur.fetchone():
                con.close()
                return False

            # 查找Augment相关的键
            augment_patterns = [
                'memento/webviewView.augment-chat',
                'workbench.view.extension.augment-chat',
                'workbench.view.extension.augment-panel'
            ]

            for pattern in augment_patterns:
                cur.execute("SELECT key FROM ItemTable WHERE key = ?", (pattern,))
                if cur.fetchone():
                    con.close()
                    return True

            con.close()
            return False

        except Exception as e:
            self.logger.error(f"检查Augment数据时出错: {e}")
            return False

    def _find_idea_augment_projects(self, recent_projects_file: Path) -> List[str]:
        """查找包含Augment数据的IDEA项目"""
        projects = []

        try:
            tree = ET.parse(recent_projects_file)
            root = tree.getroot()

            for entry in root.findall(".//entry"):
                key = entry.get('key')
                if key and not key.startswith('$'):  # 排除特殊路径
                    # 检查项目是否包含Augment数据
                    augment_file = Path(key) / '.idea' / 'AugmentWebviewStateStore.xml'
                    if augment_file.exists():
                        project_name = Path(key).name
                        projects.append(project_name)

        except Exception as e:
            self.logger.error(f"查找IDEA Augment项目时出错: {e}")

        return projects

    def _find_pycharm_augment_projects(self, recent_projects_file: Path) -> List[str]:
        """查找包含Augment数据的PyCharm项目"""
        projects = []

        try:
            tree = ET.parse(recent_projects_file)
            root = tree.getroot()

            for entry in root.findall(".//entry"):
                key = entry.get('key')
                if key and not key.startswith('$'):  # 排除特殊路径
                    # 检查项目是否包含Augment数据
                    augment_file = Path(key) / '.idea' / 'AugmentWebviewStateStore.xml'
                    if augment_file.exists():
                        project_name = Path(key).name
                        projects.append(project_name)

        except Exception as e:
            self.logger.error(f"查找PyCharm Augment项目时出错: {e}")

        return projects

    def validate_all_paths(self, paths: Dict[str, str]) -> Dict[str, ValidationResult]:
        """
        批量验证多个数据源的路径

        Args:
            paths: 数据源路径字典

        Returns:
            Dict: 验证结果字典
        """
        results = {}

        for data_source, path in paths.items():
            if path:  # 只验证非空路径
                results[data_source] = self.validate_path(data_source, path)
            else:
                results[data_source] = ValidationResult(
                    is_valid=True,  # 空路径表示使用默认值，认为是有效的
                    path="",
                    data_source=data_source,
                    message="使用默认路径"
                )

        return results
