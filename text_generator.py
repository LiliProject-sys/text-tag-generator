import tkinter as tk
from tkinter import ttk, messagebox
from db_manager import DBManager

class TextGenerator:
    def __init__(self, root):
        """初始化文本生成器
        参数:
            root: tkinter的根窗口对象
        功能:
            1. 初始化数据库连接
            2. 加载标签数据
            3. 创建GUI界面
        """
        self.root = root
        self.root.title("文本生成器")
        
        # 设置窗口大小和位置
        window_width = 800
        window_height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        # 计算窗口居中的位置
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        # 设置窗口大小和位置
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        # 禁止调整窗口大小
        self.root.resizable(False, False)
        
        # 初始化数据库管理器并加载数据
        self.db_manager = DBManager()
        self.tags = self.db_manager.get_all_tags()  # 从数据库获取所有标签
        self.tag_brackets = {tag: 0 for tag in self.tags}  # 为每个标签初始化括号计数
        self.selected_tags = []  # 存储用户选择的标签
        
        # 创建主界面框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        # 创建各个界面组件
        self.create_add_tag_area()   # 创建添加标签区域
        self.create_tag_area()       # 创建标签显示区域
        self.create_output_area()    # 创建文本输出区域
        self.create_clear_button()   # 创建清除按钮

    def create_add_tag_area(self):
        # 创建添加新标签的框架
        add_frame = ttk.LabelFrame(self.main_frame, text="添加新标签")
        add_frame.pack(padx=10, pady=5, fill="x")
        
        # 创建输入框
        self.new_tag_entry = ttk.Entry(add_frame)
        self.new_tag_entry.pack(side="left", padx=5, pady=5)
        
        # 创建添加按钮
        add_btn = ttk.Button(add_frame, text="添加标签", command=self.add_new_tag)
        add_btn.pack(side="left", padx=5, pady=5)

    def create_tag_area(self):
        """创建标签区域"""
        tag_frame = ttk.LabelFrame(self.main_frame, text="选择标签")
        tag_frame.pack(padx=10, pady=5, fill="x")
        
        # 使用Canvas和Scrollbar创建可滚动区域
        canvas = tk.Canvas(tag_frame, height=150)  # 设置固定高度
        scrollbar = ttk.Scrollbar(tag_frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas)

        canvas.configure(xscrollcommand=scrollbar.set)
        
        # 创建标签按钮和括号按钮
        for tag in self.tags:
            tag_container = ttk.Frame(scrollable_frame)
            tag_container.pack(side="left", padx=5, pady=5)
            
            # 标签按钮
            btn = ttk.Button(tag_container, text=tag, 
                           command=lambda t=tag: self.add_tag(t))
            btn.pack(side="left")
            
            # 括号按钮
            bracket_btn = ttk.Button(tag_container, text="{ }", 
                                   command=lambda t=tag: self.add_brackets(t))
            bracket_btn.pack(side="left")

        # 配置滚动区域
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind("<Configure>", 
                            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.pack(fill="x", expand=True)
        scrollbar.pack(fill="x")

    def add_new_tag(self):
        """添加新标签的方法
        1. 检查输入的标签是否有效
        2. 保存到数据库
        3. 更新内存中的数据结构
        4. 重建界面显示新标签
        """
        new_tag = self.new_tag_entry.get().strip()  # 获取输入框的内容并去除首尾空格
        if new_tag:  # 如果输入不为空
            if new_tag not in self.tags:  # 检查标签是否已存在
                # 先尝试保存到数据库
                if self.db_manager.add_tag(new_tag):
                    # 数据库保存成功后，更新内存中的数据结构
                    self.tags.append(new_tag)  # self.tags 是内存中的标签列表，与数据库同步
                    self.tag_brackets[new_tag] = 0  # 初始化新标签的括号计数器
                    
                    # 重建整个界面以显示新标签
                    for widget in self.main_frame.winfo_children():
                        widget.destroy()  # 清除所有现有组件
                    
                    # 重新创建所有界面组件
                    self.create_add_tag_area()   # 重建添加标签区域
                    self.create_tag_area()       # 重建标签按钮区域
                    self.create_output_area()    # 重建输出文本区域
                    self.create_clear_button()   # 重建清除按钮
                    
                    self.new_tag_entry.delete(0, tk.END)  # 清空输入框
                else:
                    messagebox.showerror("错误", "添加标签失败！")  # 数据库操作失败时显示错误
            else:
                messagebox.showwarning("警告", "该标签已存在！")  # 标签重复时显示警告

    def add_brackets(self, tag):
        """为指定标签添加一对花括号
        参数:
            tag: 要添加括号的标签名
        功能:
            1. 检查标签是否被选中
            2. 增加标签的括号计数
            3. 更新输出文本
        """
        if tag in self.selected_tags:  # 只处理已选中的标签
            self.tag_brackets[tag] += 1  # 增加括号计数
            self.update_output()  # 更新显示的文本

    def add_tag(self, tag):
        """添加标签到选中列表
        参数:
            tag: 要添加的标签名
        功能:
            1. 检查标签是否已选中
            2. 添加到选中列表
            3. 重置括号计数
            4. 更新数据库使用统计
            5. 更新输出文本
        """
        if tag not in self.selected_tags:
            self.selected_tags.append(tag)  # 添加到选中列表
            self.tag_brackets[tag] = 0  # 重置括号计数
            self.db_manager.update_tag_usage(tag)  # 更新数据库中的使用次数
            self.update_output()  # 更新显示的文本

    def update_output(self):
        """更新输出文本
        功能:
            1. 处理每个选中的标签
            2. 添加指定数量的括号
            3. 用逗号连接所有标签
            4. 更新显示
        """
        output_parts = []  # 存储处理后的标签文本
        for tag in self.selected_tags:
            tag_text = tag
            # 根据括号计数添加相应数量的括号
            for _ in range(self.tag_brackets[tag]):
                tag_text = "{" + tag_text + "}"
            output_parts.append(tag_text)
        
        # 用逗号连接所有标签并更新显示
        output = ", ".join(output_parts)
        self.output_text.delete(1.0, tk.END)  # 清除现有文本
        self.output_text.insert(tk.END, output)  # 插入新文本

    def create_output_area(self):
        """创建输出区域"""
        output_frame = ttk.LabelFrame(self.main_frame, text="生成的文本")
        output_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        # 设置更大的文本框
        self.output_text = tk.Text(output_frame, height=10, width=60)
        self.output_text.pack(padx=5, pady=5, fill="both", expand=True)

    def create_clear_button(self):
        clear_btn = ttk.Button(self.main_frame, text="清除", command=self.clear_all)
        clear_btn.pack(pady=5)

    def clear_all(self):
        self.selected_tags.clear()
        # 重置所有标签的括号数量
        for tag in self.tag_brackets:
            self.tag_brackets[tag] = 0
        self.output_text.delete(1.0, tk.END)

    def __del__(self):
        # 关闭数据库连接
        if hasattr(self, 'db_manager'):
            self.db_manager.close()

def main():
    root = tk.Tk()
    app = TextGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main() 