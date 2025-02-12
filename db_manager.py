import mysql.connector
from mysql.connector import Error
from datetime import datetime

class DBManager:
    def __init__(self):
        # 数据库连接配置
        self.config = {
            'host': 'localhost',
            'port': '3306',
            'user': 'root',
            'password': 'LiliProject',
            'database': 'text_generator'
        }
        self.connection = None
        
    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            print("数据库连接成功！")
        except Error as e:
            print(f"数据库连接错误: {e}")
            return False
        return True

    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("数据库连接已关闭")

    def get_all_tags(self):
        """获取所有标签"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.execute("SELECT tag_name FROM tags ORDER BY use_count DESC")
            tags = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return tags
        except Error as e:
            print(f"获取标签错误: {e}")
            return []

    def add_tag(self, tag_name):
        """添加新标签"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                
            cursor = self.connection.cursor()
            sql = "INSERT IGNORE INTO tags (tag_name) VALUES (%s)"
            cursor.execute(sql, (tag_name,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"添加标签错误: {e}")
            return False

    def update_tag_usage(self, tag_name):
        """更新标签使用次数"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                
            cursor = self.connection.cursor()
            sql = """
                UPDATE tags 
                SET use_count = use_count + 1,
                    last_used_at = CURRENT_TIMESTAMP
                WHERE tag_name = %s
            """
            cursor.execute(sql, (tag_name,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"更新标签使用次数错误: {e}")
            return False

    def create_bracket_level(self, level_name: str, bracket_count: int) -> bool:
        """创建新的括号层级
        参数：
            level_name: 层级名称
            bracket_count: 括号数量
        返回：
            bool: 创建是否成功
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                
            cursor = self.connection.cursor()
            sql = """
                INSERT INTO bracket_levels (level_name, bracket_count)
                VALUES (%s, %s)
            """
            cursor.execute(sql, (level_name, bracket_count))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"创建括号层级错误: {e}")
            return False

    def get_all_levels(self) -> list:
        """获取所有活动的括号层级
        返回：
            list: [(level_id, level_name, bracket_count), ...]
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT level_id, level_name, bracket_count 
                FROM bracket_levels 
                WHERE is_active = TRUE 
                ORDER BY level_id
            """)
            levels = cursor.fetchall()
            cursor.close()
            return levels
        except Error as e:
            print(f"获取括号层级错误: {e}")
            return []

    def delete_bracket_level(self, level_id: int) -> bool:
        """删除括号层级
        参数：
            level_id: 层级ID
        返回：
            bool: 是否删除成功
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                
            cursor = self.connection.cursor()
            sql = "UPDATE bracket_levels SET is_active = FALSE WHERE level_id = %s"
            cursor.execute(sql, (level_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"删除括号层级错误: {e}")
            return False

    def update_bracket_level(self, level_id: int, new_name: str, new_count: int) -> bool:
        """更新括号层级
        参数：
            level_id: 层级ID
            new_name: 新的层级名称
            new_count: 新的括号数量
        返回：
            bool: 是否更新成功
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                
            cursor = self.connection.cursor()
            sql = """
                UPDATE bracket_levels 
                SET level_name = %s, bracket_count = %s
                WHERE level_id = %s
            """
            cursor.execute(sql, (new_name, new_count, level_id))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"更新括号层级错误: {e}")
            return False 