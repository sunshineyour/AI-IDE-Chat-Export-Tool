"""
IDEA Augment数据提取器 - 集成到cursor-view项目

这个模块负责从JetBrains IDEA项目的.idea目录中提取Augment插件的对话数据，
并将其转换为与现有cursor-view项目兼容的格式。
"""

import json
import logging
import os
import platform
import pathlib
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 导入增强的对话解析器
from conversation_parser import ConversationParser

logger = logging.getLogger(__name__)

@dataclass
class IdeaProject:
    """IDEA项目信息"""
    name: str
    path: str
    augment_data_file: str
    last_modified: datetime

class IdeaAugmentExtractor:
    """IDEA Augment数据提取器"""
    
    def __init__(self, custom_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.conversation_parser = ConversationParser()
        self.custom_path = custom_path
        
    def find_idea_projects(self) -> List[IdeaProject]:
        """
        查找包含Augment数据的IDEA项目
        
        Returns:
            IDEA项目列表
        """
        projects = []
        
        try:
            # 获取IDEA配置目录
            idea_config_dir = self._get_idea_config_directory()
            if not idea_config_dir or not os.path.exists(idea_config_dir):
                self.logger.warning(f"IDEA配置目录不存在: {idea_config_dir}")
                return projects
            
            # 读取最近项目列表
            recent_projects = self._get_recent_projects(idea_config_dir)
            
            # 检查每个项目的Augment数据
            for project_path in recent_projects:
                if os.path.exists(project_path):
                    augment_file = os.path.join(project_path, '.idea', 'AugmentWebviewStateStore.xml')
                    
                    if os.path.exists(augment_file):
                        try:
                            # 获取项目名称
                            project_name = os.path.basename(project_path)
                            
                            # 获取文件修改时间
                            last_modified = datetime.fromtimestamp(os.path.getmtime(augment_file))
                            
                            project = IdeaProject(
                                name=project_name,
                                path=project_path,
                                augment_data_file=augment_file,
                                last_modified=last_modified
                            )
                            
                            projects.append(project)
                            self.logger.info(f"发现IDEA Augment项目: {project_name} ({project_path})")
                            
                        except Exception as e:
                            self.logger.warning(f"处理项目 {project_path} 时出错: {e}")
            
            self.logger.info(f"总共发现 {len(projects)} 个包含Augment数据的IDEA项目")
            return projects
            
        except Exception as e:
            self.logger.error(f"查找IDEA项目失败: {e}")
            return projects
    
    def _get_idea_config_directory(self) -> Optional[str]:
        """
        获取IDEA配置目录路径
        优先使用自定义路径，如果未设置则使用默认路径

        Returns:
            IDEA配置目录路径或None
        """
        try:
            # 如果设置了自定义路径，优先使用
            if self.custom_path:
                if os.path.exists(self.custom_path):
                    self.logger.info(f"使用自定义IDEA Augment路径: {self.custom_path}")
                    return self.custom_path
                else:
                    self.logger.warning(f"自定义IDEA Augment路径不存在: {self.custom_path}，回退到默认路径")

            # 使用默认路径
            system = platform.system()

            if system == "Windows":
                # Windows: %APPDATA%\JetBrains\IntelliJIdea{version}
                appdata = os.environ.get('APPDATA')
                if appdata:
                    jetbrains_dir = os.path.join(appdata, 'JetBrains')
                    if os.path.exists(jetbrains_dir):
                        # 查找最新版本的IDEA目录
                        idea_dirs = [d for d in os.listdir(jetbrains_dir) if d.startswith('IntelliJIdea')]
                        if idea_dirs:
                            # 选择最新版本
                            latest_dir = sorted(idea_dirs)[-1]
                            default_path = os.path.join(jetbrains_dir, latest_dir)
                            self.logger.info(f"使用默认IDEA Augment路径: {default_path}")
                            return default_path

            elif system == "Darwin":  # macOS
                # macOS: ~/Library/Application Support/JetBrains/IntelliJIdea{version}
                home = os.path.expanduser("~")
                jetbrains_dir = os.path.join(home, "Library", "Application Support", "JetBrains")
                if os.path.exists(jetbrains_dir):
                    idea_dirs = [d for d in os.listdir(jetbrains_dir) if d.startswith('IntelliJIdea')]
                    if idea_dirs:
                        latest_dir = sorted(idea_dirs)[-1]
                        default_path = os.path.join(jetbrains_dir, latest_dir)
                        self.logger.info(f"使用默认IDEA Augment路径: {default_path}")
                        return default_path

            elif system == "Linux":
                # Linux: ~/.config/JetBrains/IntelliJIdea{version}
                home = os.path.expanduser("~")
                jetbrains_dir = os.path.join(home, ".config", "JetBrains")
                if os.path.exists(jetbrains_dir):
                    idea_dirs = [d for d in os.listdir(jetbrains_dir) if d.startswith('IntelliJIdea')]
                    if idea_dirs:
                        latest_dir = sorted(idea_dirs)[-1]
                        default_path = os.path.join(jetbrains_dir, latest_dir)
                        self.logger.info(f"使用默认IDEA Augment路径: {default_path}")
                        return default_path

            return None

        except Exception as e:
            self.logger.error(f"获取IDEA配置目录失败: {e}")
            return None
    
    def _expand_idea_path_variables(self, path: str) -> str:
        """
        展开IDEA路径变量

        Args:
            path: 包含变量的路径

        Returns:
            展开后的实际路径
        """
        if not path:
            return path

        # 展开常见的IDEA路径变量
        expanded_path = path

        # $USER_HOME$ -> 用户主目录
        if '$USER_HOME$' in expanded_path:
            user_home = os.path.expanduser('~')
            expanded_path = expanded_path.replace('$USER_HOME$', user_home)

        # $APPLICATION_CONFIG_DIR$ -> IDEA配置目录
        if '$APPLICATION_CONFIG_DIR$' in expanded_path:
            config_dir = self._get_idea_config_directory()
            if config_dir:
                expanded_path = expanded_path.replace('$APPLICATION_CONFIG_DIR$', config_dir)

        # 标准化路径分隔符
        expanded_path = os.path.normpath(expanded_path)

        return expanded_path

    def _get_recent_projects(self, idea_config_dir: str) -> List[str]:
        """
        从IDEA配置中获取最近项目列表

        Args:
            idea_config_dir: IDEA配置目录

        Returns:
            项目路径列表
        """
        projects = []

        try:
            recent_projects_file = os.path.join(idea_config_dir, 'options', 'recentProjects.xml')

            if not os.path.exists(recent_projects_file):
                self.logger.warning(f"最近项目文件不存在: {recent_projects_file}")
                return projects

            # 解析XML文件
            tree = ET.parse(recent_projects_file)
            root = tree.getroot()

            # 查找项目路径 - 在additionalInfo/map/entry中
            additional_info = root.find('.//option[@name="additionalInfo"]')
            if additional_info is not None:
                map_element = additional_info.find('map')
                if map_element is not None:
                    for entry in map_element.findall('entry'):
                        key = entry.get('key')
                        if key:
                            self.logger.debug(f"找到原始项目路径: {key}")

                            # 排除特殊配置路径
                            if 'light-edit' in key:
                                self.logger.debug(f"跳过特殊配置路径: {key}")
                                continue

                            # 展开路径变量
                            expanded_path = self._expand_idea_path_variables(key)
                            self.logger.debug(f"展开后的路径: {expanded_path}")

                            # 检查路径是否存在
                            if os.path.exists(expanded_path):
                                projects.append(expanded_path)
                                self.logger.debug(f"✅ 有效项目路径: {expanded_path}")
                            else:
                                self.logger.debug(f"❌ 路径不存在: {expanded_path}")

            self.logger.info(f"从recentProjects.xml中找到 {len(projects)} 个项目")
            return projects

        except Exception as e:
            self.logger.error(f"读取最近项目列表失败: {e}")
            return projects
    
    def extract_augment_data_from_project(self, project: IdeaProject) -> Optional[Dict[str, Any]]:
        """
        从单个项目中提取Augment数据
        
        Args:
            project: IDEA项目信息
            
        Returns:
            解析后的Augment数据或None
        """
        try:
            self.logger.info(f"提取项目 {project.name} 的Augment数据...")
            
            # 解析XML文件
            tree = ET.parse(project.augment_data_file)
            root = tree.getroot()
            
            # 查找AugmentWebviewStateStore组件
            for component in root.findall('.//component'):
                name = component.get('name')
                if name == 'AugmentWebviewStateStore':
                    self.logger.debug(f"找到AugmentWebviewStateStore组件")
                    
                    # 查找状态数据
                    for option in component.findall('.//option'):
                        option_name = option.get('name')
                        if option_name == 'stateMap':  # 修正：实际的option名称是stateMap
                            # 查找map中的entry
                            for entry in option.findall('.//entry'):
                                key = entry.get('key')
                                value = entry.get('value')

                                if key == 'CHAT_STATE' and value:  # 修正：查找CHAT_STATE键
                                    try:
                                        # 解析JSON数据
                                        augment_data = json.loads(value)
                                        self.logger.info(f"成功解析项目 {project.name} 的Augment数据")
                                        
                                        # 添加项目信息
                                        augment_data['_project_info'] = {
                                            'name': project.name,
                                            'path': project.path,
                                            'last_modified': project.last_modified.isoformat()
                                        }
                                        
                                        return augment_data
                                        
                                    except json.JSONDecodeError as e:
                                        self.logger.error(f"解析JSON数据失败: {e}")
                                        return None
            
            self.logger.warning(f"项目 {project.name} 中未找到有效的Augment数据")
            return None
            
        except Exception as e:
            self.logger.error(f"提取项目 {project.name} 的Augment数据失败: {e}")
            return None
    
    def extract_augment_conversations(self) -> List[Any]:
        """
        提取所有IDEA Augment对话
        
        Returns:
            对话对象列表
        """
        all_conversations = []
        
        try:
            # 查找所有包含Augment数据的项目
            projects = self.find_idea_projects()
            
            if not projects:
                self.logger.warning("未找到任何包含Augment数据的IDEA项目")
                return all_conversations
            
            # 从每个项目中提取对话数据
            for project in projects:
                augment_data = self.extract_augment_data_from_project(project)
                
                if augment_data and 'conversations' in augment_data:
                    conversations_data = augment_data['conversations']
                    project_info = augment_data.get('_project_info', {})
                    
                    # 直接解析对话数据（IDEA格式与VSCode不同，需要直接调用核心解析方法）
                    conversations = []
                    for conv_id, conv_data in conversations_data.items():
                        parsed_conv = self.conversation_parser._parse_single_conversation(conv_id, conv_data)
                        if parsed_conv:
                            conversations.append(parsed_conv)
                    
                    # 为每个对话添加项目信息
                    for conv in conversations:
                        conv.workspace_id = f"idea_{project.name}_{project.path.replace('/', '_').replace('\\', '_')}"
                        conv.project_name = project.name
                        conv.project_path = project.path
                    
                    all_conversations.extend(conversations)
                    self.logger.info(f"从项目 {project.name} 中提取了 {len(conversations)} 个对话")
            
            self.logger.info(f"总共提取了 {len(all_conversations)} 个IDEA Augment对话")
            return all_conversations
            
        except Exception as e:
            self.logger.error(f"提取IDEA Augment对话失败: {e}")
            return all_conversations

    def convert_to_cursor_view_format(self, conversations: List[Any]) -> List[Dict[str, Any]]:
        """
        将IDEA Augment对话转换为cursor-view兼容格式

        Args:
            conversations: 对话对象列表

        Returns:
            cursor-view格式的对话数据列表
        """
        cursor_format_chats = []

        try:
            for conv in conversations:
                # 转换消息格式
                messages = []

                for msg in conv.messages:
                    message_data = {
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                        'request_id': msg.request_id
                    }

                    # 添加工具使用信息
                    if hasattr(msg, 'tool_uses') and msg.tool_uses:
                        message_data['tool_uses'] = [
                            {
                                'tool_name': tool.tool_name,
                                'tool_use_id': tool.tool_use_id,
                                'input_json': tool.input_json,
                                'result': tool.result,
                                'is_error': tool.is_error
                            }
                            for tool in msg.tool_uses
                        ]

                    # 添加工作区文件信息
                    if hasattr(msg, 'workspace_files') and msg.workspace_files:
                        message_data['workspace_files'] = msg.workspace_files

                    messages.append(message_data)

                # 使用项目信息
                workspace_id = getattr(conv, 'workspace_id', 'unknown')
                project_name = getattr(conv, 'project_name', 'Unknown Project')
                project_path = getattr(conv, 'project_path', '')

                # 构建cursor-view格式的对话数据
                chat_data = {
                    'session': {
                        'composerId': conv.id,
                        'title': f"IDEA Augment Chat {conv.id[:8]}...",
                        'createdAt': conv.created_at.timestamp() if conv.created_at else 0,
                        'lastUpdatedAt': conv.last_interacted_at.timestamp() if conv.last_interacted_at else 0
                    },
                    'project': {
                        'name': f"IDEA: {project_name}",
                        'rootPath': project_path,
                        'workspace_id': workspace_id
                    },
                    'messages': messages,
                    'date': conv.created_at.timestamp() if conv.created_at else 0,
                    'session_id': conv.id,
                    'workspace_id': workspace_id,
                    'db_path': f'idea_augment_data_{workspace_id}',
                    'source': 'idea-augment',  # 标识数据来源
                    'project_name': project_name,
                    'project_path': project_path
                }

                cursor_format_chats.append(chat_data)

            self.logger.info(f"成功转换 {len(cursor_format_chats)} 个IDEA Augment对话为cursor-view格式")
            return cursor_format_chats

        except Exception as e:
            self.logger.error(f"转换IDEA Augment对话格式失败: {e}")
            return cursor_format_chats

    def get_demo_data(self) -> Dict[str, Any]:
        """
        获取示例数据用于测试

        Returns:
            示例数据字典
        """
        return {
            'currentConversationId': '7c03e471-9d6e-40d3-a664-2ed95872b0aa',
            'conversations': {
                '7c03e471-9d6e-40d3-a664-2ed95872b0aa': {
                    'id': '7c03e471-9d6e-40d3-a664-2ed95872b0aa',
                    'name': 'IDEA Augment Demo Chat',
                    'createdAtIso': '2025-06-27T10:00:00.000Z',
                    'lastInteractedAtIso': '2025-06-27T10:30:00.000Z',
                    'chatHistory': [
                        {
                            'status': 'success',
                            'request_id': 'demo-request-1',
                            'request_message': '分析这个IDEA项目的结构',
                            'timestamp': '2025-06-27T10:05:00.000Z',
                            'response_text': '我将分析这个IDEA项目的结构。让我查看项目的主要组件和架构。',
                            'structured_output_nodes': [
                                {
                                    'id': 1,
                                    'type': 0,
                                    'content': '我将分析这个IDEA项目的结构。让我查看项目的主要组件和架构。'
                                }
                            ]
                        }
                    ],
                    'isPinned': False,
                    'isShareable': True
                }
            },
            '_project_info': {
                'name': 'DemoProject',
                'path': '/path/to/demo/project',
                'last_modified': '2025-06-27T10:30:00.000Z'
            }
        }
