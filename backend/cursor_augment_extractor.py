"""
Cursor Augment数据提取器 - 集成到cursor-view项目

这个模块负责从Cursor IDE的workspaceStorage中提取Augment插件的对话数据，
并将其转换为与现有cursor-view项目兼容的格式。

与VSCode Augment提取器的区别：
- 数据源路径：Cursor的workspaceStorage而不是VSCode的
- 数据格式：完全相同，可以复用所有解析逻辑
"""

import json
import logging
import sqlite3
import platform
import pathlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 复用现有的数据类
from augment_extractor import AugmentMessage, AugmentConversation
# 导入ConversationParser来处理structured_output_nodes
from conversation_parser import ConversationParser

logger = logging.getLogger(__name__)

class CursorAugmentExtractor:
    """从Cursor IDE的workspaceStorage中提取Augment数据的类"""
    
    def __init__(self, custom_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        # 创建ConversationParser实例来处理structured_output_nodes
        self.conversation_parser = ConversationParser()
        self.custom_path = custom_path
    
    def get_cursor_storage_path(self) -> Optional[pathlib.Path]:
        """
        获取Cursor IDE的workspaceStorage路径
        优先使用自定义路径，如果未设置则使用默认路径

        Returns:
            Cursor workspaceStorage路径或None
        """
        try:
            # 如果设置了自定义路径，优先使用
            if self.custom_path:
                custom_path_obj = pathlib.Path(self.custom_path)
                if custom_path_obj.exists():
                    self.logger.info(f"使用自定义Cursor Augment路径: {self.custom_path}")
                    return custom_path_obj
                else:
                    self.logger.warning(f"自定义Cursor Augment路径不存在: {self.custom_path}，回退到默认路径")

            # 使用默认路径
            home = pathlib.Path.home()
            system = platform.system()

            if system == "Darwin":  # macOS
                cursor_path = home / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage"
            elif system == "Windows":
                cursor_path = home / "AppData" / "Roaming" / "Cursor" / "User" / "workspaceStorage"
            elif system == "Linux":
                cursor_path = home / ".config" / "Cursor" / "User" / "workspaceStorage"
            else:
                self.logger.warning(f"不支持的操作系统: {system}")
                return None

            if cursor_path.exists():
                self.logger.info(f"使用默认Cursor Augment路径: {cursor_path}")
                return cursor_path
            else:
                self.logger.warning(f"Cursor workspaceStorage路径不存在: {cursor_path}")
                return None

        except Exception as e:
            self.logger.error(f"获取Cursor存储路径失败: {e}")
            return None
    
    def find_all_augment_databases(self) -> List[Dict[str, Any]]:
        """
        查找所有包含Augment数据的SQLite数据库

        Returns:
            包含数据库路径和workspace信息的字典列表
        """
        storage_path = self.get_cursor_storage_path()
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
            
            # 检查是否存在Augment相关的键
            cursor.execute("""
                SELECT COUNT(*) FROM ItemTable 
                WHERE key = 'memento/webviewView.augment-chat'
            """)
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            self.logger.debug(f"检查数据库 {db_path} 时出错: {e}")
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

        self.logger.info(f"总共成功提取 {len(all_conversations)} 个Cursor Augment对话")
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
                # 解析JSON数据
                webview_data = json.loads(row[0])

                # 提取对话数据
                webview_state_raw = webview_data.get('webviewState', {})

                # 如果webviewState是字符串，需要再次解析JSON
                if isinstance(webview_state_raw, str):
                    webview_state = json.loads(webview_state_raw)
                else:
                    webview_state = webview_state_raw

                conversations_data = webview_state.get('conversations', {})

                if not conversations_data:
                    self.logger.debug(f"workspace {workspace_id} 中未找到对话数据")
                    return conversations

                self.logger.info(f"workspace {workspace_id} 中找到 {len(conversations_data)} 个对话")

                # 解析每个对话
                for conv_id, conv_data in conversations_data.items():
                    try:
                        # 检查conv_data的类型，如果是字符串则尝试解析JSON
                        if isinstance(conv_data, str):
                            self.logger.debug(f"conv_data是字符串，尝试解析JSON: {conv_id}")
                            conv_data = json.loads(conv_data)

                        conversation = self._parse_conversation(conv_id, conv_data, workspace_id)
                        if conversation and conversation.messages:
                            conversations.append(conversation)
                            self.logger.debug(f"成功解析对话: {conv_id[:8]}... (workspace: {workspace_id})")
                    except Exception as e:
                        self.logger.error(f"解析对话 {conv_id} 失败: {e}, conv_data类型: {type(conv_data)}")
                        continue

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
            workspace_id: workspace ID
            
        Returns:
            解析后的对话对象或None
        """
        try:
            # 解析时间戳
            created_at = self._parse_datetime(conv_data.get('createdAtIso'))
            last_interacted_at = self._parse_datetime(conv_data.get('lastInteractedAtIso'))
            
            # 解析消息
            messages = []
            chat_history = conv_data.get('chatHistory', [])

            for chat_item in chat_history:
                try:
                    # 检查chat_item的类型，如果是字符串则尝试解析JSON
                    if isinstance(chat_item, str):
                        self.logger.debug(f"chat_item是字符串，尝试解析JSON")
                        chat_item = json.loads(chat_item)

                    # 确保chat_item是字典类型
                    if not isinstance(chat_item, dict):
                        self.logger.warning(f"chat_item不是字典类型: {type(chat_item)}")
                        continue

                    # 获取时间戳
                    timestamp = self._parse_datetime(chat_item.get('timestamp'))
                    request_id = chat_item.get('request_id', '')

                    # 解析用户消息
                    user_message = chat_item.get('request_message', '').strip()
                    if user_message:
                        messages.append(AugmentMessage(
                            role='user',
                            content=user_message,
                            timestamp=timestamp,
                            request_id=request_id
                        ))

                    # 解析助手消息 - 使用ConversationParser处理structured_output_nodes
                    assistant_message = chat_item.get('response_text', '').strip()

                    # 提取并合并structured_output_nodes内容（包括mermaid图表）
                    structured_content = self.conversation_parser._extract_structured_content(chat_item)
                    complete_content = self.conversation_parser._merge_message_content(assistant_message, structured_content)

                    # 只有在有实际内容时才创建消息
                    if complete_content.strip():
                        messages.append(AugmentMessage(
                            role='assistant',
                            content=complete_content,
                            timestamp=timestamp,
                            request_id=request_id
                        ))
                except Exception as e:
                    self.logger.error(f"解析chat_item失败: {e}, chat_item类型: {type(chat_item)}")
                    continue

            # 创建对话对象
            conversation = AugmentConversation(
                id=conv_id,
                created_at=created_at,
                last_interacted_at=last_interacted_at,
                messages=messages,
                is_pinned=conv_data.get('isPinned', False),
                is_shareable=conv_data.get('isShareable', True),
                workspace_id=workspace_id
            )

            return conversation

        except Exception as e:
            self.logger.error(f"解析对话 {conv_id} 失败: {e}")
            return None
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """
        解析日期时间字符串
        
        Args:
            datetime_str: ISO格式的日期时间字符串
            
        Returns:
            datetime对象
        """
        if not datetime_str:
            return datetime.now()
        
        try:
            # 处理ISO格式的时间戳
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1] + '+00:00'
            
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception as e:
            self.logger.warning(f"解析时间戳失败: {datetime_str}, 错误: {e}")
            return datetime.now()
    
    def convert_to_cursor_view_format(self, conversations: List[AugmentConversation]) -> List[Dict[str, Any]]:
        """
        将Augment对话转换为cursor-view兼容的格式
        
        Args:
            conversations: Augment对话列表
            
        Returns:
            cursor-view格式的对话数据列表
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
                        'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
                    })
                
                # 使用实际的workspace信息
                workspace_id = conv.workspace_id or 'unknown'
                project_name = f"Cursor Augment Chat ({workspace_id[:8]}...)" if len(workspace_id) > 8 else f"Cursor Augment Chat ({workspace_id})"

                # 构建cursor-view格式的对话数据
                chat_data = {
                    'session': {
                        'composerId': conv.id,
                        'title': f"Cursor Augment Chat {conv.id[:8]}...",
                        'createdAt': conv.created_at.timestamp(),
                        'lastUpdatedAt': conv.last_interacted_at.timestamp()
                    },
                    'project': {
                        'name': project_name,
                        'rootPath': f'/cursor-augment/{workspace_id}',
                        'workspace_id': workspace_id
                    },
                    'messages': messages,
                    'date': conv.created_at.timestamp(),
                    'session_id': conv.id,
                    'workspace_id': workspace_id,
                    'db_path': f'cursor_augment_data_{workspace_id}',
                    'source': 'cursor-augment'  # 标识数据来源
                }
                
                cursor_format_chats.append(chat_data)
                
            except Exception as e:
                self.logger.error(f"转换对话 {conv.id} 格式失败: {e}")
                continue
        
        self.logger.info(f"成功转换 {len(cursor_format_chats)} 个Cursor Augment对话为cursor-view格式")
        return cursor_format_chats
