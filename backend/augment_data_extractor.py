"""
Augment数据提取器 - 从SQLite数据库中提取Augment相关数据

这个模块负责:
1. 连接SQLite数据库
2. 查询Augment相关的记录
3. 解析JSON数据
4. 提供清洁的数据给后续处理
"""

import json
import logging
from typing import Dict, List, Any, Optional


class AugmentDataExtractor:
    """从SQLite数据库中提取Augment数据的类"""

    # Augment相关的key模式
    AUGMENT_KEY_PATTERNS = [
        'augment',
        'Augment',
        'memento/webviewView.augment-chat',
        'workbench.view.extension.augment-chat',
        'workbench.view.extension.augment-panel'
    ]

    def __init__(self, db_path: str = None):
        """
        初始化数据提取器

        Args:
            db_path: SQLite数据库文件路径（当前版本使用MCP工具，此参数保留兼容性）
        """
        self.logger = logging.getLogger(__name__)
        # 注意：当前版本使用MCP SQLite工具，不需要直接文件访问
    
    def _find_augment_keys(self) -> List[str]:
        """
        查找所有Augment相关的key
        
        Returns:
            Augment相关key的列表
        """
        augment_keys = []
        
        try:
            with self._connect_db() as conn:
                cursor = conn.cursor()
                
                # 查询所有包含augment的key
                for pattern in self.AUGMENT_KEY_PATTERNS:
                    cursor.execute(
                        "SELECT key FROM ItemTable WHERE key LIKE ? OR key LIKE ?",
                        (f'%{pattern}%', f'%{pattern.lower()}%')
                    )
                    
                    rows = cursor.fetchall()
                    for row in rows:
                        if row['key'] not in augment_keys:
                            augment_keys.append(row['key'])
                
                self.logger.info(f"找到 {len(augment_keys)} 个Augment相关的key")
                return augment_keys
                
        except sqlite3.Error as e:
            self.logger.error(f"查询Augment keys失败: {e}")
            return []
    
    def _extract_key_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        提取指定key的数据
        
        Args:
            key: 要提取的key
            
        Returns:
            包含key和解析后数据的字典，或None
        """
        try:
            with self._connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM ItemTable WHERE key = ?", (key,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                value = row['value']
                
                # 尝试解析JSON
                parsed_data = self._parse_json_value(value)
                
                return {
                    'key': key,
                    'raw_value': value,
                    'parsed_data': parsed_data,
                    'size': len(value) if value else 0
                }
                
        except sqlite3.Error as e:
            self.logger.error(f"提取key '{key}' 数据失败: {e}")
            return None
    
    def _parse_json_value(self, value: Any) -> Any:
        """
        解析JSON值，支持嵌套JSON字符串
        
        Args:
            value: 要解析的值
            
        Returns:
            解析后的数据
        """
        if not value:
            return None
        
        # 如果是字节类型，先转换为字符串
        if isinstance(value, bytes):
            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                self.logger.warning("无法解码字节数据为UTF-8")
                return None
        
        # 如果不是字符串，直接返回
        if not isinstance(value, str):
            return value
        
        try:
            # 第一层JSON解析
            parsed = json.loads(value)
            
            # 如果解析结果包含webviewState字符串，进行二次解析
            if isinstance(parsed, dict) and 'webviewState' in parsed:
                webview_state = parsed['webviewState']
                if isinstance(webview_state, str):
                    try:
                        parsed['webviewState'] = json.loads(webview_state)
                    except json.JSONDecodeError:
                        self.logger.warning("webviewState不是有效的JSON")
            
            return parsed
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON解析失败: {e}")
            return value  # 返回原始值
    
    def extract_augment_data(self) -> Dict[str, Any]:
        """
        提取所有Augment相关数据
        
        Returns:
            包含所有Augment数据的字典
        """
        self.logger.info("开始提取Augment数据...")
        
        # 查找所有Augment相关的key
        augment_keys = self._find_augment_keys()
        
        if not augment_keys:
            self.logger.warning("未找到任何Augment相关的key")
            return {}
        
        # 提取每个key的数据
        extracted_data = {}
        
        for key in augment_keys:
            self.logger.debug(f"提取key: {key}")
            key_data = self._extract_key_data(key)
            
            if key_data:
                extracted_data[key] = key_data
                self.logger.debug(f"成功提取key '{key}', 数据大小: {key_data['size']} 字节")
            else:
                self.logger.warning(f"无法提取key '{key}' 的数据")
        
        self.logger.info(f"成功提取 {len(extracted_data)} 个Augment记录")
        return extracted_data
    
    def get_main_chat_data(self) -> Optional[Dict[str, Any]]:
        """
        获取主要的聊天数据 (memento/webviewView.augment-chat)
        
        Returns:
            主要聊天数据或None
        """
        main_key = 'memento/webviewView.augment-chat'
        return self._extract_key_data(main_key)
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库基本信息
        
        Returns:
            数据库信息字典
        """
        try:
            with self._connect_db() as conn:
                cursor = conn.cursor()
                
                # 获取表信息
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row['name'] for row in cursor.fetchall()]
                
                # 获取ItemTable记录数
                cursor.execute("SELECT COUNT(*) as count FROM ItemTable")
                total_records = cursor.fetchone()['count']
                
                # 获取Augment相关记录数
                augment_keys = self._find_augment_keys()
                
                return {
                    'database_path': str(self.db_path),
                    'tables': tables,
                    'total_records': total_records,
                    'augment_records': len(augment_keys),
                    'augment_keys': augment_keys
                }
                
        except sqlite3.Error as e:
            self.logger.error(f"获取数据库信息失败: {e}")
            return {}
