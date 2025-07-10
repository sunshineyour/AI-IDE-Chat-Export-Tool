"""
输出格式化器 - 将解析后的对话数据格式化为不同输出格式

这个模块负责:
1. 将对话对象转换为JSON格式
2. 将对话对象转换为Markdown格式
3. 支持元数据包含/排除选项
4. 提供美观的格式化输出
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from conversation_parser import Conversation, Message, ToolUse


class OutputFormatter:
    """输出格式化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format_conversations(
        self, 
        conversations: List[Conversation], 
        format_type: str = 'json',
        include_metadata: bool = False
    ) -> str:
        """
        格式化对话数据
        
        Args:
            conversations: 对话列表
            format_type: 输出格式 ('json', 'markdown')
            include_metadata: 是否包含元数据
            
        Returns:
            格式化后的字符串
        """
        if format_type == 'json':
            return self._format_json(conversations, include_metadata)
        elif format_type == 'markdown':
            return self._format_markdown(conversations, include_metadata)
        else:
            raise ValueError(f"不支持的格式类型: {format_type}")
    
    def _format_json(self, conversations: List[Conversation], include_metadata: bool) -> str:
        """
        格式化为JSON格式
        
        Args:
            conversations: 对话列表
            include_metadata: 是否包含元数据
            
        Returns:
            JSON字符串
        """
        data = {
            'export_info': {
                'export_time': datetime.now().isoformat(),
                'total_conversations': len(conversations),
                'format_version': '1.0',
                'source': 'Augment VSCode Plugin'
            },
            'conversations': []
        }
        
        for conv in conversations:
            conv_data = {
                'id': conv.id,
                'created_at': conv.created_at.isoformat(),
                'last_interacted_at': conv.last_interacted_at.isoformat(),
                'message_count': len(conv.messages),
                'messages': []
            }
            
            if include_metadata:
                conv_data.update({
                    'is_pinned': conv.is_pinned,
                    'is_shareable': conv.is_shareable
                })
            
            for msg in conv.messages:
                msg_data = {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'request_id': msg.request_id
                }
                
                if include_metadata:
                    if msg.tool_uses:
                        msg_data['tool_uses'] = [
                            {
                                'tool_name': tool.tool_name,
                                'tool_use_id': tool.tool_use_id,
                                'input_json': tool.input_json,
                                'result': tool.result,
                                'is_error': tool.is_error
                            }
                            for tool in msg.tool_uses
                        ]
                    
                    if msg.workspace_files:
                        msg_data['workspace_files'] = msg.workspace_files
                    
                    if msg.rich_text_content:
                        msg_data['rich_text_content'] = msg.rich_text_content
                
                conv_data['messages'].append(msg_data)
            
            data['conversations'].append(conv_data)
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _format_markdown(self, conversations: List[Conversation], include_metadata: bool) -> str:
        """
        格式化为Markdown格式
        
        Args:
            conversations: 对话列表
            include_metadata: 是否包含元数据
            
        Returns:
            Markdown字符串
        """
        lines = []
        
        # 标题和摘要
        lines.append("# Augment 对话导出")
        lines.append("")
        lines.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**对话总数**: {len(conversations)}")
        lines.append(f"**数据源**: Augment VSCode Plugin")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 对话列表
        for i, conv in enumerate(conversations, 1):
            lines.append(f"## 对话 {i}: {conv.id[:8]}...")
            lines.append("")
            
            if include_metadata:
                lines.append("### 对话信息")
                lines.append(f"- **ID**: `{conv.id}`")
                lines.append(f"- **创建时间**: {conv.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append(f"- **最后交互**: {conv.last_interacted_at.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append(f"- **消息数量**: {len(conv.messages)}")
                lines.append(f"- **已固定**: {'是' if conv.is_pinned else '否'}")
                lines.append(f"- **可分享**: {'是' if conv.is_shareable else '否'}")
                lines.append("")
            
            lines.append("### 对话内容")
            lines.append("")
            
            for j, msg in enumerate(conv.messages, 1):
                # 消息角色标识
                role_icon = "🧑" if msg.role == "user" else "🤖"
                role_name = "用户" if msg.role == "user" else "助手"
                
                lines.append(f"#### {role_icon} {role_name} - 消息 {j}")
                lines.append("")
                lines.append(f"**时间**: {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append("")
                
                # 消息内容
                content = msg.content.strip()
                if content:
                    lines.append("**内容**:")
                    lines.append("")
                    # 将内容按行分割并添加适当的缩进
                    for line in content.split('\n'):
                        lines.append(line)
                    lines.append("")
                
                # 元数据信息
                if include_metadata:
                    if msg.workspace_files:
                        lines.append("**相关文件**:")
                        for file_path in msg.workspace_files:
                            lines.append(f"- `{file_path}`")
                        lines.append("")
                    
                    if msg.tool_uses:
                        lines.append("**工具使用**:")
                        for tool in msg.tool_uses:
                            lines.append(f"- **{tool.tool_name}**")
                            if tool.result:
                                result_preview = tool.result[:100] + "..." if len(tool.result) > 100 else tool.result
                                lines.append(f"  - 结果: {result_preview}")
                            if tool.is_error:
                                lines.append("  - ❌ 执行出错")
                        lines.append("")
                
                lines.append("---")
                lines.append("")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def format_summary(self, conversations: List[Conversation]) -> str:
        """
        格式化对话摘要
        
        Args:
            conversations: 对话列表
            
        Returns:
            摘要字符串
        """
        if not conversations:
            return "未找到对话数据"
        
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
        
        earliest = min(all_times) if all_times else None
        latest = max(all_times) if all_times else None
        
        summary_lines = [
            "=== Augment 对话摘要 ===",
            f"对话总数: {len(conversations)}",
            f"消息总数: {total_messages}",
            f"  - 用户消息: {user_messages}",
            f"  - 助手消息: {assistant_messages}",
            ""
        ]
        
        if earliest and latest:
            summary_lines.extend([
                f"时间范围: {earliest.strftime('%Y-%m-%d')} 至 {latest.strftime('%Y-%m-%d')}",
                ""
            ])
        
        summary_lines.append("对话列表:")
        for i, conv in enumerate(conversations, 1):
            summary_lines.append(
                f"  {i}. {conv.id[:8]}... "
                f"({len(conv.messages)} 消息, "
                f"{conv.created_at.strftime('%m-%d %H:%M')})"
            )
        
        return '\n'.join(summary_lines)
    
    def _escape_markdown(self, text: str) -> str:
        """
        转义Markdown特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            转义后的文本
        """
        # 转义常见的Markdown特殊字符
        escape_chars = ['*', '_', '`', '#', '[', ']', '(', ')', '!']
        
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
