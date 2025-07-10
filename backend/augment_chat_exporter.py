#!/usr/bin/env python3
"""
Augment Chat Exporter - 从VSCode workspaceStorage中提取Augment插件的对话内容

这个程序专门用于从VSCode的workspaceStorage SQLite数据库中筛选和导出
Augment插件的对话记录，支持多种输出格式。

使用方法:
    python augment_chat_exporter.py --db path/to/database.sqlite --output conversations.json
    python augment_chat_exporter.py --db path/to/database.sqlite --format markdown --output conversations.md
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from augment_data_extractor import AugmentDataExtractor
from conversation_parser import ConversationParser
from output_formatter import OutputFormatter


class AugmentChatExporter:
    """Augment对话导出器主类"""
    
    def __init__(self, db_path: str):
        """
        初始化导出器
        
        Args:
            db_path: SQLite数据库文件路径
        """
        self.db_path = Path(db_path)
        self.extractor = AugmentDataExtractor(db_path)
        self.parser = ConversationParser()
        self.formatter = OutputFormatter()
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def export_conversations(
        self, 
        output_path: str, 
        format_type: str = 'json',
        include_metadata: bool = False
    ) -> bool:
        """
        导出Augment对话
        
        Args:
            output_path: 输出文件路径
            format_type: 输出格式 ('json', 'markdown')
            include_metadata: 是否包含技术元数据
            
        Returns:
            bool: 导出是否成功
        """
        try:
            self.logger.info(f"开始从 {self.db_path} 提取Augment对话数据...")
            
            # 步骤1: 提取原始数据
            raw_data = self.extractor.extract_augment_data()
            if not raw_data:
                self.logger.warning("未找到Augment对话数据")
                return False
            
            self.logger.info(f"找到 {len(raw_data)} 个Augment相关记录")
            
            # 步骤2: 解析对话
            conversations = self.parser.parse_conversations(raw_data)
            if not conversations:
                self.logger.warning("未能解析出有效的对话数据")
                return False
            
            self.logger.info(f"成功解析 {len(conversations)} 个对话")
            
            # 步骤3: 格式化输出
            output_content = self.formatter.format_conversations(
                conversations, 
                format_type, 
                include_metadata
            )
            
            # 步骤4: 写入文件
            output_file = Path(output_path)
            output_file.write_text(output_content, encoding='utf-8')
            
            self.logger.info(f"对话已成功导出到: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出过程中发生错误: {e}")
            return False
    
    def list_conversations(self) -> Optional[list]:
        """
        列出所有可用的对话（不导出，仅预览）
        
        Returns:
            对话列表或None
        """
        try:
            raw_data = self.extractor.extract_augment_data()
            if not raw_data:
                return None
            
            conversations = self.parser.parse_conversations(raw_data)
            return conversations
            
        except Exception as e:
            self.logger.error(f"列出对话时发生错误: {e}")
            return None


def main():
    """主函数 - 命令行接口"""
    parser = argparse.ArgumentParser(
        description="从VSCode workspaceStorage中导出Augment插件对话",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s --db workspace.sqlite --output conversations.json
  %(prog)s --db workspace.sqlite --format markdown --output conversations.md
  %(prog)s --db workspace.sqlite --list
        """
    )
    
    parser.add_argument(
        '--db', 
        required=True,
        help='SQLite数据库文件路径'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='输出文件路径'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'markdown'],
        default='json',
        help='输出格式 (默认: json)'
    )
    
    parser.add_argument(
        '--include-metadata',
        action='store_true',
        help='包含技术元数据'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='仅列出对话，不导出'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 验证数据库文件
    if not Path(args.db).exists():
        print(f"错误: 数据库文件不存在: {args.db}")
        sys.exit(1)
    
    # 创建导出器
    exporter = AugmentChatExporter(args.db)
    
    # 执行操作
    if args.list:
        conversations = exporter.list_conversations()
        if conversations:
            print(f"找到 {len(conversations)} 个对话:")
            for i, conv in enumerate(conversations, 1):
                print(f"  {i}. ID: {conv.id[:8]}... "
                      f"创建时间: {conv.created_at} "
                      f"消息数: {len(conv.messages)}")
        else:
            print("未找到对话")
    else:
        if not args.output:
            print("错误: 需要指定输出文件路径 (--output)")
            sys.exit(1)
        
        success = exporter.export_conversations(
            args.output,
            args.format,
            args.include_metadata
        )
        
        if success:
            print(f"导出成功: {args.output}")
        else:
            print("导出失败")
            sys.exit(1)


if __name__ == '__main__':
    main()
