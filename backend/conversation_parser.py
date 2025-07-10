"""
对话解析器 - 解析Augment对话数据结构

这个模块负责:
1. 解析复杂的Augment对话JSON结构
2. 提取有意义的对话内容
3. 清理技术性元数据
4. 构建结构化的对话对象
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ToolUse:
    """工具使用记录"""
    tool_name: str
    tool_use_id: str
    input_json: str
    result: Optional[str] = None
    is_error: bool = False


@dataclass
class Message:
    """单条消息"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    request_id: str
    tool_uses: List[ToolUse] = field(default_factory=list)
    rich_text_content: Optional[Dict] = None
    workspace_files: List[str] = field(default_factory=list)


@dataclass
class Conversation:
    """完整对话"""
    id: str
    created_at: datetime
    last_interacted_at: datetime
    messages: List[Message] = field(default_factory=list)
    is_pinned: bool = False
    is_shareable: bool = False


class ConversationParser:
    """Augment对话数据解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_conversations(self, raw_data: Dict[str, Any]) -> List[Conversation]:
        """
        解析原始数据中的所有对话
        
        Args:
            raw_data: 从数据库提取的原始数据
            
        Returns:
            解析后的对话列表
        """
        conversations = []
        
        # 查找主要的聊天数据
        main_chat_key = 'memento/webviewView.augment-chat'
        
        if main_chat_key not in raw_data:
            self.logger.warning("未找到主要聊天数据")
            return conversations
        
        chat_data = raw_data[main_chat_key]
        parsed_data = chat_data.get('parsed_data')
        
        if not parsed_data:
            self.logger.error("聊天数据解析失败")
            return conversations
        
        # 提取webviewState
        webview_state = parsed_data.get('webviewState')
        if not webview_state:
            self.logger.error("未找到webviewState")
            return conversations
        
        # 解析conversations
        conversations_data = webview_state.get('conversations', {})
        
        for conv_id, conv_data in conversations_data.items():
            try:
                conversation = self._parse_single_conversation(conv_id, conv_data)
                if conversation and conversation.messages:
                    conversations.append(conversation)
                    self.logger.debug(f"成功解析对话 {conv_id[:8]}...")
            except Exception as e:
                self.logger.error(f"解析对话 {conv_id} 失败: {e}")
        
        self.logger.info(f"成功解析 {len(conversations)} 个对话")
        return conversations
    
    def _parse_single_conversation(self, conv_id: str, conv_data: Dict) -> Optional[Conversation]:
        """
        解析单个对话
        
        Args:
            conv_id: 对话ID
            conv_data: 对话数据
            
        Returns:
            解析后的对话对象或None
        """
        try:
            # 解析基本信息
            created_at = self._parse_datetime(conv_data.get('createdAtIso'))
            last_interacted_at = self._parse_datetime(conv_data.get('lastInteractedAtIso'))
            
            conversation = Conversation(
                id=conv_id,
                created_at=created_at,
                last_interacted_at=last_interacted_at,
                is_pinned=conv_data.get('isPinned', False),
                is_shareable=conv_data.get('isShareable', False)
            )
            
            # 解析聊天历史
            chat_history = conv_data.get('chatHistory', [])
            
            for chat_item in chat_history:
                message = self._parse_message(chat_item)
                if message:
                    conversation.messages.append(message)
            
            return conversation
            
        except Exception as e:
            self.logger.error(f"解析对话失败: {e}")
            return None
    
    def _parse_message(self, chat_item: Dict) -> Optional[Message]:
        """
        解析单条消息

        Args:
            chat_item: 聊天项数据

        Returns:
            解析后的消息对象或None
        """
        try:
            # 提取基本信息
            request_id = chat_item.get('request_id', '')
            timestamp = self._parse_datetime(chat_item.get('timestamp'))

            # 提取用户消息
            user_message = chat_item.get('request_message', '')
            assistant_message = chat_item.get('response_text', '')

            messages = []

            # 创建用户消息
            if user_message.strip():
                user_msg = Message(
                    role='user',
                    content=user_message.strip(),
                    timestamp=timestamp,
                    request_id=request_id,
                    rich_text_content=chat_item.get('rich_text_json_repr')
                )

                # 提取工作区文件信息
                workspace_files = self._extract_workspace_files(chat_item)
                user_msg.workspace_files = workspace_files

                messages.append(user_msg)

            # 创建助手消息 - 增强版本，包含structured_output_nodes内容
            if assistant_message.strip() or chat_item.get('structured_output_nodes'):
                # 提取并合并所有内容
                structured_content = self._extract_structured_content(chat_item)
                complete_content = self._merge_message_content(assistant_message, structured_content)

                # 只有在有实际内容时才创建消息
                if complete_content.strip():
                    assistant_msg = Message(
                        role='assistant',
                        content=complete_content,
                        timestamp=timestamp,
                        request_id=request_id
                    )

                    # 提取工具使用信息
                    tool_uses = self._extract_tool_uses(chat_item)
                    assistant_msg.tool_uses = tool_uses

                    messages.append(assistant_msg)

            return messages[0] if messages else None

        except Exception as e:
            self.logger.error(f"解析消息失败: {e}")
            return None
    
    def _extract_tool_uses(self, chat_item: Dict) -> List[ToolUse]:
        """
        提取工具使用信息
        
        Args:
            chat_item: 聊天项数据
            
        Returns:
            工具使用列表
        """
        tool_uses = []
        
        # 从structured_output_nodes提取工具使用
        output_nodes = chat_item.get('structured_output_nodes', [])
        
        for node in output_nodes:
            if node.get('type') == 5 and 'tool_use' in node:  # type 5 表示工具使用
                tool_use_data = node['tool_use']
                
                tool_use = ToolUse(
                    tool_name=tool_use_data.get('tool_name', ''),
                    tool_use_id=tool_use_data.get('tool_use_id', ''),
                    input_json=tool_use_data.get('input_json', '')
                )
                
                tool_uses.append(tool_use)
        
        # 从toolUseStates提取结果
        tool_states = chat_item.get('toolUseStates', {})
        
        for tool_use in tool_uses:
            state_key = f"{chat_item.get('request_id')};{tool_use.tool_use_id}"
            if state_key in tool_states:
                state = tool_states[state_key]
                result = state.get('result', {})
                tool_use.result = result.get('text', '')
                tool_use.is_error = result.get('isError', False)
        
        return tool_uses

    def _extract_structured_content(self, chat_item: Dict) -> str:
        """
        提取并合并structured_output_nodes中的所有内容

        Args:
            chat_item: 聊天项数据

        Returns:
            合并后的内容字符串
        """
        try:
            content_parts = []

            # 处理structured_output_nodes
            output_nodes = chat_item.get('structured_output_nodes', [])
            if output_nodes:
                # 按照id排序节点，确保内容顺序正确
                sorted_nodes = sorted(output_nodes, key=lambda x: x.get('id', 0))

                for node in sorted_nodes:
                    node_type = node.get('type')
                    node_content = node.get('content', '')

                    if node_type == 0:  # 文本内容节点
                        if node_content and node_content.strip():
                            # 检查是否是JSON格式的Mermaid图表
                            try:
                                import json
                                if isinstance(node_content, str) and node_content.strip().startswith('{'):
                                    content_data = json.loads(node_content)
                                    if isinstance(content_data, dict) and content_data.get('type') == 'mermaid_diagram':
                                        mermaid_content = self._process_mermaid_node(content_data)
                                        if mermaid_content:
                                            content_parts.append(mermaid_content)
                                            continue  # 已处理，跳过后续逻辑
                            except (json.JSONDecodeError, TypeError):
                                pass  # 不是JSON，继续作为普通文本处理

                            # 作为普通文本内容处理
                            content_parts.append(node_content.strip())

                    elif node_type == 5:  # 工具使用节点 - 检查是否是render-mermaid
                        tool_use = node.get('tool_use', {})
                        tool_name = tool_use.get('tool_name', '')

                        if tool_name == 'render-mermaid':
                            # 处理render-mermaid工具的输入数据
                            input_json = tool_use.get('input_json', '')
                            if input_json:
                                try:
                                    import json
                                    input_data = json.loads(input_json)

                                    # 构建mermaid_diagram格式的数据
                                    mermaid_data = {
                                        'type': 'mermaid_diagram',
                                        'diagram_definition': input_data.get('diagram_definition', ''),
                                        'title': input_data.get('title', '')
                                    }

                                    mermaid_content = self._process_mermaid_node(mermaid_data)
                                    if mermaid_content:
                                        content_parts.append(mermaid_content)
                                        self.logger.debug(f"成功处理render-mermaid工具，内容长度: {len(mermaid_content)}")
                                except (json.JSONDecodeError, TypeError) as e:
                                    self.logger.debug(f"解析render-mermaid输入失败: {e}")

                        continue  # 跳过其他工具使用节点

                    else:  # 其他类型节点，检查是否包含特殊内容
                        # 检查是否是Mermaid图表
                        if node_content:
                            try:
                                # 尝试解析content为JSON
                                import json
                                if isinstance(node_content, str):
                                    content_data = json.loads(node_content)
                                else:
                                    content_data = node_content

                                if isinstance(content_data, dict) and content_data.get('type') == 'mermaid_diagram':
                                    mermaid_content = self._process_mermaid_node(content_data)
                                    if mermaid_content:
                                        content_parts.append(mermaid_content)
                                        continue  # 已处理，跳过后续逻辑
                            except (json.JSONDecodeError, TypeError) as e:
                                self.logger.debug(f"节点内容不是JSON格式: {e}")

                            # 如果不是Mermaid图表或解析失败，直接添加文本内容
                            if node_content.strip():
                                content_parts.append(node_content.strip())

            # 处理structured_request_nodes中的工具结果节点（可能包含Mermaid图表）
            structured_request_nodes = chat_item.get('structured_request_nodes', [])
            self.logger.debug(f"处理structured_request_nodes，数量: {len(structured_request_nodes)}")

            for node in structured_request_nodes:
                node_type = node.get('type', 0)
                self.logger.debug(f"处理节点类型: {node_type}")

                if node_type == 1:  # tool_result_node
                    tool_result_node = node.get('tool_result_node', {})
                    content = tool_result_node.get('content', '')
                    self.logger.debug(f"工具结果节点内容长度: {len(content) if content else 0}")

                    # 检查是否包含Mermaid图表数据
                    if content and isinstance(content, str):
                        try:
                            # 尝试解析JSON格式的Mermaid数据
                            import json
                            mermaid_data = json.loads(content)
                            self.logger.debug(f"解析JSON成功，类型: {mermaid_data.get('type') if isinstance(mermaid_data, dict) else 'unknown'}")

                            if isinstance(mermaid_data, dict) and mermaid_data.get('type') == 'mermaid_diagram':
                                mermaid_content = self._process_mermaid_node(mermaid_data)
                                if mermaid_content:
                                    self.logger.debug(f"成功处理Mermaid节点，内容长度: {len(mermaid_content)}")
                                    content_parts.append(mermaid_content)
                                    continue
                        except (json.JSONDecodeError, TypeError) as e:
                            self.logger.debug(f"JSON解析失败: {e}")

                        # 如果不是Mermaid数据，但有内容，也可以添加（根据需要）
                        # 注意：这里可能包含大量工具输出，需要谨慎处理
                        # if content.strip() and len(content) < 1000:  # 限制长度避免过长内容
                        #     content_parts.append(content.strip())

            return '\n\n'.join(content_parts)

        except Exception as e:
            self.logger.error(f"提取structured_output_nodes内容失败: {e}")
            return ""

    def _process_mermaid_node(self, mermaid_data: Dict) -> str:
        """
        处理Mermaid图表节点，转换为markdown格式

        Args:
            mermaid_data: Mermaid图表数据

        Returns:
            markdown格式的Mermaid图表
        """
        try:
            diagram_definition = mermaid_data.get('diagram_definition', '')
            title = mermaid_data.get('title', '')

            if not diagram_definition:
                return ""

            # 构建markdown格式的Mermaid图表
            mermaid_block = "```mermaid\n" + diagram_definition + "\n```"

            if title:
                return f"**{title}**\n\n{mermaid_block}"
            else:
                return mermaid_block

        except Exception as e:
            self.logger.error(f"处理Mermaid节点失败: {e}")
            return ""

    def _merge_message_content(self, response_text: str, structured_content: str) -> str:
        """
        合并基础文本和结构化内容，避免重复

        Args:
            response_text: 基础响应文本
            structured_content: 结构化内容

        Returns:
            合并后的完整内容
        """
        # 清理输入
        response_text = response_text.strip() if response_text else ""
        structured_content = structured_content.strip() if structured_content else ""

        # 如果都为空，返回空字符串
        if not response_text and not structured_content:
            self.logger.debug("消息内容为空")
            return ""

        # 如果只有一个有内容，直接返回
        if not response_text:
            return structured_content
        if not structured_content:
            return response_text

        # 检查重复内容：如果structured_content包含response_text，只使用structured_content
        if response_text in structured_content:
            self.logger.debug("检测到重复内容，只使用structured_content")
            return structured_content

        # 检查反向包含：如果response_text包含structured_content，只使用response_text
        if structured_content in response_text:
            self.logger.debug("检测到反向重复内容，只使用response_text")
            return response_text

        # 没有重复，正常合并
        return '\n\n'.join([response_text, structured_content])

    def _extract_workspace_files(self, chat_item: Dict) -> List[str]:
        """
        提取工作区文件信息
        
        Args:
            chat_item: 聊天项数据
            
        Returns:
            文件路径列表
        """
        files = []
        
        workspace_chunks = chat_item.get('workspace_file_chunks', [])
        
        for chunk in workspace_chunks:
            file_info = chunk.get('file', {})
            path_name = file_info.get('pathName')
            if path_name:
                files.append(path_name)
        
        return files
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> datetime:
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
            # 处理ISO格式的日期时间
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1] + '+00:00'
            
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            
        except ValueError:
            self.logger.warning(f"无法解析日期时间: {datetime_str}")
            return datetime.now()
    
    def get_conversation_summary(self, conversations: List[Conversation]) -> Dict[str, Any]:
        """
        获取对话统计摘要
        
        Args:
            conversations: 对话列表
            
        Returns:
            统计摘要
        """
        if not conversations:
            return {}
        
        total_messages = sum(len(conv.messages) for conv in conversations)
        user_messages = sum(
            len([msg for msg in conv.messages if msg.role == 'user']) 
            for conv in conversations
        )
        assistant_messages = total_messages - user_messages
        
        # 时间范围
        all_times = []
        for conv in conversations:
            all_times.append(conv.created_at)
            all_times.append(conv.last_interacted_at)
            for msg in conv.messages:
                all_times.append(msg.timestamp)
        
        return {
            'total_conversations': len(conversations),
            'total_messages': total_messages,
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'earliest_conversation': min(all_times) if all_times else None,
            'latest_conversation': max(all_times) if all_times else None
        }
