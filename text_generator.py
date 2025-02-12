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
        
        # 添加新的实例变量
        self.tag_buttons = {}      # 存储标签按钮引用
        self.bracket_counts = {}   # 存储括号计数标签引用
        
        # 添加层级管理相关的实例变量
        self.bracket_levels = {}  # 存储层级信息 {level_id: (level_name, bracket_count)}
        self.level_buttons = {}  # 存储层级按钮引用
        
        # 加载层级数据
        self.load_bracket_levels()
        
        # 创建主界面框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        # 创建各个界面组件
        self.create_add_tag_area()   # 创建添加标签区域
        self.create_tag_area()       # 创建标签显示区域
        self.create_output_area()    # 创建文本输出区域
        self.create_clear_button()   # 创建清除按钮
        self.create_level_controls()  # 创建层级控制区域

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
        """创建标签区域
        功能：
            1. 创建可滚动的标签区域
            2. 为每个标签创建状态显示
            3. 显示括号数量
        """
        tag_frame = ttk.LabelFrame(self.main_frame, text="选择标签")
        tag_frame.pack(padx=10, pady=5, fill="x")
        
        # 使用Canvas和Scrollbar创建可滚动区域
        canvas = tk.Canvas(tag_frame, height=150)
        scrollbar = ttk.Scrollbar(tag_frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas)

        canvas.configure(xscrollcommand=scrollbar.set)
        
        # 创建标签按钮和状态显示
        for tag in self.tags:
            tag_container = ttk.Frame(scrollable_frame)
            tag_container.pack(side="left", padx=5, pady=5)
            
            # 创建标签状态容器
            status_frame = ttk.Frame(tag_container)
            status_frame.pack(side="top")
            
            # 标签按钮 - 使用tk.Button以支持背景色变化
            btn = tk.Button(status_frame, text=tag,
                          command=lambda t=tag: self.toggle_tag(t))
            btn.pack(side="left")
            
            # 括号计数显示
            count_label = ttk.Label(status_frame, text="0")
            count_label.pack(side="left")
            
            # 保存组件引用以便更新
            self.tag_buttons[tag] = btn
            self.bracket_counts[tag] = count_label
            
            # 括号按钮区域
            bracket_frame = ttk.Frame(tag_container)
            bracket_frame.pack(side="left")
            
            # 增加括号按钮
            add_bracket_btn = ttk.Button(bracket_frame, text="+{ }", 
                                      command=lambda t=tag: self.add_brackets(t))
            add_bracket_btn.pack(side="left")
            
            # 减少括号按钮
            sub_bracket_btn = ttk.Button(bracket_frame, text="-{ }", 
                                      command=lambda t=tag: self.remove_brackets(t))
            sub_bracket_btn.pack(side="left")

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
            1. 按层级对标签进行分组
            2. 为每组添加相应数量的括号
            3. 更新显示
        """
        # 按括号数量分组
        bracket_groups = {}  # {bracket_count: [tags]}
        for tag in self.selected_tags:
            count = self.tag_brackets[tag]
            if count not in bracket_groups:
                bracket_groups[count] = []
            bracket_groups[count].append(tag)
        
        # 生成输出文本
        output_parts = []
        for count, tags in bracket_groups.items():
            # 将同组标签用逗号连接
            group_text = ", ".join(tags)
            # 添加括号
            for _ in range(count):
                group_text = "{" + group_text + "}"
            output_parts.append(group_text)
        
        # 用逗号连接不同组
        output = ", ".join(output_parts)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, output)

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

    def toggle_tag(self, tag):
        """切换标签选中状态
        参数：
            tag: 要切换的标签名
        功能：
            1. 切换选中状态
            2. 更新按钮显示
            3. 更新输出文本
        """
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)
            self.tag_buttons[tag].configure(bg="SystemButtonFace")  # 默认颜色
        else:
            self.selected_tags.append(tag)
            self.tag_buttons[tag].configure(bg="lightblue")  # 选中颜色
            self.db_manager.update_tag_usage(tag)
        
        self.update_output()

    def load_bracket_levels(self):
        """加载括号层级数据"""
        levels = self.db_manager.get_all_levels()
        for level_id, name, count in levels:
            self.bracket_levels[level_id] = (name, count)

    def create_level_controls(self):
        """创建层级控制区域"""
        level_frame = ttk.LabelFrame(self.main_frame, text="括号层级")
        level_frame.pack(padx=10, pady=5, fill="x")
        
        # 创建一个Frame来容纳所有层级按钮
        buttons_frame = ttk.Frame(level_frame)
        buttons_frame.pack(fill="x", expand=True)
        
        # 创建层级按钮
        for level_id, (name, count) in self.bracket_levels.items():
            btn = ttk.Button(buttons_frame, 
                          text=f"{name} ({count}层)",
                          command=lambda lid=level_id: self.apply_level(lid))
            btn.pack(side="left", padx=5, pady=5)
            self.level_buttons[level_id] = btn
        
        # 添加"新建层级"按钮
        add_level_btn = ttk.Button(buttons_frame, 
                                  text="新建层级",
                                  command=self.show_add_level_dialog)
        add_level_btn.pack(side="left", padx=5, pady=5)

    def show_add_level_dialog(self):
        """显示新建层级对话框"""
        # 创建对话框窗口
        dialog = tk.Toplevel(self.root)
        dialog.title("新建括号层级")
        dialog.geometry("300x150")
        dialog.transient(self.root)  # 设置为主窗口的临时窗口
        
        # 层级名称输入
        name_frame = ttk.Frame(dialog)
        name_frame.pack(padx=10, pady=5, fill="x")
        ttk.Label(name_frame, text="层级名称:").pack(side="left")
        name_entry = ttk.Entry(name_frame)
        name_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # 括号数量输入
        count_frame = ttk.Frame(dialog)
        count_frame.pack(padx=10, pady=5, fill="x")
        ttk.Label(count_frame, text="括号数量:").pack(side="left")
        count_var = tk.StringVar(value="1")
        count_entry = ttk.Spinbox(count_frame, from_=1, to=10, textvariable=count_var)
        count_entry.pack(side="left", padx=5)
        
        def save_level():
            """保存新层级"""
            name = name_entry.get().strip()
            try:
                count = int(count_var.get())
                if name and count > 0:
                    if self.db_manager.create_bracket_level(name, count):
                        # 重新加载层级数据
                        self.bracket_levels.clear()
                        self.load_bracket_levels()
                        # 重建层级控制区域
                        for widget in self.level_buttons.values():
                            widget.destroy()
                        self.level_buttons.clear()
                        self.create_level_controls()
                        dialog.destroy()
                    else:
                        messagebox.showerror("错误", "创建层级失败！")
                else:
                    messagebox.showwarning("警告", "请输入有效的层级名称和括号数量！")
            except ValueError:
                messagebox.showwarning("警告", "括号数量必须是有效的数字！")
        
        # 按钮区域
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="保存", command=save_level).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side="left", padx=5)

    def apply_level(self, level_id, decrease=False):
        """应用括号层级到选中的标签
        参数：
            level_id: 层级ID
            decrease: 是否减少括号数量（降级）
        """
        if not self.selected_tags:
            messagebox.showinfo("提示", "请先选择要添加括号的标签！")
            return
        
        level_name, bracket_count = self.bracket_levels[level_id]
        
        # 为选中的标签添加或减少括号
        for tag in self.selected_tags:
            current_count = self.tag_brackets[tag]  # 当前括号数
            if decrease:
                # 降级：减少一层括号
                new_count = max(0, current_count - 1)  # 确保不小于0
            else:
                # 升级：增加到指定层级的括号数
                new_count = bracket_count
                
            self.tag_brackets[tag] = new_count
            # 更新括号计数显示
            self.bracket_counts[tag].configure(text=str(new_count))
        
        # 更新输出文本
        self.update_output()

    def delete_level(self, level_id):
        """删除括号层级
        参数：
            level_id: 要删除的层级ID
        """
        if messagebox.askyesno("确认", "确定要删除这个层级吗？"):
            if self.db_manager.delete_bracket_level(level_id):
                # 更新界面
                if level_id in self.level_buttons:
                    self.level_buttons[level_id].destroy()
                    del self.level_buttons[level_id]
                del self.bracket_levels[level_id]
            else:
                messagebox.showerror("错误", "删除层级失败！")

    def edit_level(self, level_id):
        """编辑括号层级
        参数：
            level_id: 要编辑的层级ID
        """
        level_name, bracket_count = self.bracket_levels[level_id]
        dialog = tk.Toplevel(self.root)
        dialog.title(f"编辑层级 - {level_name}")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        
        # 层级名称输入
        name_frame = ttk.Frame(dialog)
        name_frame.pack(padx=10, pady=5, fill="x")
        ttk.Label(name_frame, text="层级名称:").pack(side="left")
        name_entry = ttk.Entry(name_frame)
        name_entry.insert(0, level_name)
        name_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # 括号数量输入
        count_frame = ttk.Frame(dialog)
        count_frame.pack(padx=10, pady=5, fill="x")
        ttk.Label(count_frame, text="括号数量:").pack(side="left")
        count_var = tk.StringVar(value=str(bracket_count))
        count_entry = ttk.Spinbox(count_frame, from_=1, to=10, textvariable=count_var)
        count_entry.pack(side="left", padx=5)
        
        def save_changes():
            """保存修改"""
            new_name = name_entry.get().strip()
            try:
                new_count = int(count_var.get())
                if new_name and new_count > 0:
                    if self.db_manager.update_bracket_level(level_id, new_name, new_count):
                        # 更新内存中的数据
                        self.bracket_levels[level_id] = (new_name, new_count)
                        # 更新按钮文本
                        self.level_buttons[level_id].configure(
                            text=f"{new_name} ({new_count}个括号)")
                        dialog.destroy()
                    else:
                        messagebox.showerror("错误", "更新层级失败！")
                else:
                    messagebox.showwarning("警告", "请输入有效的层级名称和括号数量！")
            except ValueError:
                messagebox.showwarning("警告", "括号数量必须是有效的数字！")
        
        # 按钮区域
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="保存", command=save_changes).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side="left", padx=5)

    def remove_brackets(self, tag):
        """为指定标签减少一对花括号
        参数:
            tag: 要减少括号的标签名
        """
        if tag in self.selected_tags and self.tag_brackets[tag] > 0:
            self.tag_brackets[tag] -= 1  # 减少括号计数
            # 更新括号计数显示
            self.bracket_counts[tag].configure(text=str(self.tag_brackets[tag]))
            self.update_output()  # 更新显示的文本

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