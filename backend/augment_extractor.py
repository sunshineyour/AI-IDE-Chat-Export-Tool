"""
Augment数据提取器 - 集成到cursor-view项目

这个模块负责从VSCode workspaceStorage中提取Augment插件的对话数据，
并将其转换为与现有cursor-view项目兼容的格式。
"""

import json
import logging
import sqlite3
import platform
import pathlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 导入增强的对话解析器
from conversation_parser import ConversationParser

logger = logging.getLogger(__name__)

@dataclass
class AugmentMessage:
    """Augment消息数据类"""
    role: str
    content: str
    timestamp: datetime
    request_id: str

@dataclass
class AugmentConversation:
    """Augment对话数据类"""
    id: str
    created_at: datetime
    last_interacted_at: datetime
    messages: List[AugmentMessage]
    is_pinned: bool = False
    is_shareable: bool = False
    workspace_id: str = None

class AugmentDataExtractor:
    """Augment数据提取器，集成到cursor-view架构中"""
    
    def __init__(self, custom_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.conversation_parser = ConversationParser()
        self.custom_path = custom_path
    
    def get_storage_path(self) -> Optional[pathlib.Path]:
        """
        获取VSCode的workspaceStorage路径
        优先使用自定义路径，如果未设置则使用默认路径

        Returns:
            VSCode workspaceStorage路径或None
        """
        try:
            # 如果设置了自定义路径，优先使用
            if self.custom_path:
                custom_path_obj = pathlib.Path(self.custom_path)
                if custom_path_obj.exists():
                    self.logger.info(f"使用自定义VSCode路径: {self.custom_path}")
                    return custom_path_obj
                else:
                    self.logger.warning(f"自定义VSCode路径不存在: {self.custom_path}，回退到默认路径")

            # 使用默认路径
            home = pathlib.Path.home()
            system = platform.system()

            if system == "Darwin":  # macOS
                vscode_path = home / "Library" / "Application Support" / "Code" / "User" / "workspaceStorage"
            elif system == "Windows":
                vscode_path = home / "AppData" / "Roaming" / "Code" / "User" / "workspaceStorage"
            elif system == "Linux":
                vscode_path = home / ".config" / "Code" / "User" / "workspaceStorage"
            else:
                self.logger.warning(f"不支持的操作系统: {system}")
                return None

            if vscode_path.exists():
                self.logger.info(f"使用默认VSCode路径: {vscode_path}")
                return vscode_path
            else:
                self.logger.warning(f"VSCode workspaceStorage路径不存在: {vscode_path}")
                return None

        except Exception as e:
            self.logger.error(f"获取VSCode存储路径失败: {e}")
            return None
    
    def find_all_augment_databases(self) -> List[Dict[str, Any]]:
        """
        查找所有包含Augment数据的SQLite数据库

        Returns:
            包含数据库路径和workspace信息的字典列表
        """
        storage_path = self.get_storage_path()
        if not storage_path:
            return []

        augment_databases = []

        try:
            # 搜索所有workspace目录中的state.vscdb文件
            for workspace_dir in storage_path.iterdir():
                if workspace_dir.is_dir():
                    state_db = workspace_dir / "state.vscdb"
                    if state_db.exists():
                        # 检查是否包含Augment数据
                        if self._has_augment_data(state_db):
                            workspace_info = {
                                'db_path': state_db,
                                'workspace_id': workspace_dir.name,
                                'workspace_dir': workspace_dir
                            }
                            augment_databases.append(workspace_info)
                            self.logger.info(f"找到包含Augment数据的数据库: {state_db} (workspace: {workspace_dir.name})")

            if not augment_databases:
                self.logger.warning("未找到包含Augment数据的数据库")
            else:
                self.logger.info(f"总共找到 {len(augment_databases)} 个包含Augment数据的workspace")

            return augment_databases

        except Exception as e:
            self.logger.error(f"搜索Augment数据库失败: {e}")
            return []

    def find_augment_database(self) -> Optional[pathlib.Path]:
        """
        查找包含Augment数据的SQLite数据库（保持向后兼容）

        Returns:
            第一个数据库文件路径或None
        """
        databases = self.find_all_augment_databases()
        return databases[0]['db_path'] if databases else None
    
    def _has_augment_data(self, db_path: pathlib.Path) -> bool:
        """
        检查数据库是否包含Augment数据
        
        Args:
            db_path: 数据库文件路径
            
        Returns:
            是否包含Augment数据
        """
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            
            # 查找Augment相关的key
            cursor.execute(
                "SELECT COUNT(*) FROM ItemTable WHERE key LIKE '%augment%' OR key LIKE '%Augment%'"
            )
            count = cursor.fetchone()[0]
            
            conn.close()
            return count > 0
            
        except Exception as e:
            self.logger.debug(f"检查数据库 {db_path} 失败: {e}")
            return False
    
    def extract_augment_conversations(self) -> List[AugmentConversation]:
        """
        提取所有workspace中的Augment对话数据

        Returns:
            Augment对话列表
        """
        all_conversations = []

        # 获取所有包含Augment数据的数据库
        augment_databases = self.find_all_augment_databases()

        if not augment_databases:
            self.logger.warning("未找到任何包含Augment数据的数据库")
            return []

        for db_info in augment_databases:
            try:
                conversations = self._extract_conversations_from_database(db_info)
                all_conversations.extend(conversations)
                self.logger.info(f"从workspace {db_info['workspace_id']} 提取了 {len(conversations)} 个对话")
            except Exception as e:
                self.logger.error(f"从数据库 {db_info['db_path']} 提取对话失败: {e}")
                continue

        self.logger.info(f"总共成功提取 {len(all_conversations)} 个Augment对话")
        return all_conversations
    
    def _extract_conversations_from_database(self, db_info: Dict[str, Any]) -> List[AugmentConversation]:
        """
        从指定数据库中提取Augment对话数据

        Args:
            db_info: 包含数据库路径和workspace信息的字典

        Returns:
            该数据库中的对话列表
        """
        conversations = []
        db_path = db_info['db_path']
        workspace_id = db_info['workspace_id']

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()

            # 专门查找webviewState数据
            cursor.execute("""
                SELECT value FROM ItemTable
                WHERE key = 'memento/webviewView.augment-chat'
            """)

            row = cursor.fetchone()
            conn.close()

            if not row or not row[0]:
                self.logger.debug(f"workspace {workspace_id} 中未找到webviewState数据")
                return conversations

            try:
                # 第一次JSON解析
                data = json.loads(row[0])

                # 获取webviewState（这是一个JSON字符串）
                webview_state_str = data.get('webviewState')
                if not webview_state_str or not isinstance(webview_state_str, str):
                    self.logger.debug(f"workspace {workspace_id} 中webviewState不是字符串")
                    return conversations

                # 第二次JSON解析webviewState字符串
                webview_state = json.loads(webview_state_str)

                # 获取conversations数据
                conversations_data = webview_state.get('conversations', {})
                if not isinstance(conversations_data, dict):
                    self.logger.debug(f"workspace {workspace_id} 中conversations不是字典")
                    return conversations

                self.logger.info(f"workspace {workspace_id} 中找到 {len(conversations_data)} 个对话")

                # 解析每个对话
                for conv_id, conv_data in conversations_data.items():
                    conversation = self._parse_conversation(conv_id, conv_data, workspace_id)
                    if conversation and conversation.messages:
                        conversations.append(conversation)
                        self.logger.debug(f"成功解析对话: {conv_id[:8]}... (workspace: {workspace_id})")

            except json.JSONDecodeError as e:
                self.logger.error(f"解析workspace {workspace_id} 的JSON数据失败: {e}")
            except Exception as e:
                self.logger.error(f"处理workspace {workspace_id} 数据失败: {e}")

            return conversations

        except Exception as e:
            self.logger.error(f"从数据库 {db_path} 提取对话失败: {e}")
            return []
    
    def _parse_conversation(self, conv_id: str, conv_data: Dict, workspace_id: str = None) -> Optional[AugmentConversation]:
        """
        解析单个Augment对话
        
        Args:
            conv_id: 对话ID
            conv_data: 对话数据
            
        Returns:
            解析后的对话对象或None
        """
        try:
            # 解析时间戳
            created_at = self._parse_datetime(conv_data.get('createdAtIso'))
            last_interacted_at = self._parse_datetime(conv_data.get('lastInteractedAtIso'))
            
            # 解析消息 - 使用增强的ConversationParser
            messages = []
            chat_history = conv_data.get('chatHistory', [])

            for chat_item in chat_history:
                # 使用增强的消息解析器，支持structured_output_nodes
                parsed_message = self.conversation_parser._parse_message(chat_item)

                if parsed_message:
                    # 转换为AugmentMessage格式
                    augment_message = AugmentMessage(
                        role=parsed_message.role,
                        content=parsed_message.content,
                        timestamp=parsed_message.timestamp,
                        request_id=parsed_message.request_id
                    )
                    messages.append(augment_message)

                    # 如果解析器返回了多个消息（用户+助手），需要处理
                    # 但由于ConversationParser._parse_message只返回单个消息，这里不需要额外处理
            
            conversation = AugmentConversation(
                id=conv_id,
                created_at=created_at,
                last_interacted_at=last_interacted_at,
                messages=messages,
                is_pinned=conv_data.get('isPinned', False),
                is_shareable=conv_data.get('isShareable', False)
            )

            # 添加workspace信息
            if workspace_id:
                conversation.workspace_id = workspace_id

            return conversation
            
        except Exception as e:
            self.logger.error(f"解析对话 {conv_id} 失败: {e}")
            return None
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> datetime:
        """
        解析ISO格式的日期时间字符串
        
        Args:
            datetime_str: ISO格式的日期时间字符串
            
        Returns:
            datetime对象
        """
        if not datetime_str:
            return datetime.now()
        
        try:
            # 处理ISO格式的日期时间
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1] + '+00:00'
            
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            
        except ValueError:
            self.logger.warning(f"无法解析日期时间: {datetime_str}")
            return datetime.now()
    
    def convert_to_cursor_format(self, conversations: List[AugmentConversation]) -> List[Dict[str, Any]]:
        """
        将Augment对话转换为cursor-view兼容的格式
        
        Args:
            conversations: Augment对话列表
            
        Returns:
            cursor-view格式的对话列表
        """
        cursor_format_chats = []
        
        for conv in conversations:
            try:
                # 转换消息格式
                messages = []
                for msg in conv.messages:
                    messages.append({
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp.timestamp()
                    })
                
                # 使用实际的workspace信息
                workspace_id = conv.workspace_id or 'unknown'
                project_name = f"Augment Chat ({workspace_id[:8]}...)" if len(workspace_id) > 8 else f"Augment Chat ({workspace_id})"

                # 构建cursor-view格式的对话数据
                chat_data = {
                    'session': {
                        'composerId': conv.id,
                        'title': f"Augment Chat {conv.id[:8]}...",
                        'createdAt': conv.created_at.timestamp(),
                        'lastUpdatedAt': conv.last_interacted_at.timestamp()
                    },
                    'project': {
                        'name': project_name,
                        'rootPath': f'/augment/{workspace_id}',
                        'workspace_id': workspace_id
                    },
                    'messages': messages,
                    'date': conv.created_at.timestamp(),
                    'session_id': conv.id,
                    'workspace_id': workspace_id,
                    'db_path': f'augment_data_{workspace_id}',
                    'source': 'augment'  # 标识数据来源
                }
                
                cursor_format_chats.append(chat_data)
                
            except Exception as e:
                self.logger.error(f"转换对话格式失败 {conv.id}: {e}")
                continue
        
        self.logger.info(f"成功转换 {len(cursor_format_chats)} 个Augment对话为cursor格式")
        return cursor_format_chats
