import tkinter as tk
from tkinter import ttk, messagebox
from db_manager import DBManager

class ToolTip:
    """工具提示类
    数据结构：
    - self.widget: 需要显示提示的控件
    - self.text: 提示文本内容
    - self.tooltip: 提示窗口实例
    
    功能：
    - 当鼠标悬停在控件上时显示提示文本
    - 当鼠标离开时自动隐藏提示
    """
    def __init__(self, widget, text):
        """初始化工具提示
        参数：
            widget: 需要添加提示的控件
            text: 提示文本内容
        """
        self.widget = widget
        self.text = text
        self.tooltip = None
        # 绑定鼠标事件
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)

    def show_tooltip(self, event=None):
        """显示提示窗口
        数据流向：
        1. 计算提示窗口显示位置
        2. 创建顶层窗口
        3. 配置窗口样式
        4. 显示提示文本
        """
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        # 创建工具提示窗口
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)  # 移除窗口装饰
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(self.tooltip, text=self.text, 
                         background="#ffffe0", relief='solid', borderwidth=1)
        label.pack()

    def hide_tooltip(self, event=None):
        """隐藏提示窗口
        功能：
        - 销毁提示窗口
        - 重置tooltip属性
        """
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

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
        self.tags = {}  # {tag_name: context} 存储标签名和对应的文本内容
        for tag_name, context in self.db_manager.get_all_tags():
            self.tags[tag_name] = context
        self.tag_brackets = {tag_name: 0 for tag_name in self.tags.keys()}  # 所有标签的括号数量
        self.selected_tags = []  # 当前选中的标签
        self.remembered_brackets = {}  # 新增：记住每个标签的括号数量
        
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
        """创建添加新标签区域"""
        add_frame = ttk.LabelFrame(self.main_frame, text="添加新标签")
        add_frame.pack(padx=10, pady=5, fill="x")
        
        # 创建标签名称输入区域
        name_frame = ttk.Frame(add_frame)
        name_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(name_frame, text="标签名称:").pack(side="left")
        self.new_tag_entry = ttk.Entry(name_frame)
        self.new_tag_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # 创建标签内容输入区域
        context_frame = ttk.Frame(add_frame)
        context_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(context_frame, text="标签内容:").pack(side="left")
        self.context_entry = ttk.Entry(context_frame)
        self.context_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # 添加提示文本
        ttk.Label(add_frame, 
                 text="注：标签内容为空时将使用标签名称",
                 font=("", 8),
                 foreground="gray").pack(pady=(0,5))
        
        # 创建添加按钮
        add_btn = ttk.Button(add_frame, text="添加标签", command=self.add_new_tag)
        add_btn.pack(pady=5)

    def create_tag_area(self):
        """创建标签区域"""
        tag_frame = ttk.LabelFrame(self.main_frame, text="选择标签")
        tag_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        # 创建搜索框
        search_frame = ttk.Frame(tag_frame)
        search_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(search_frame, text="搜索:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_tags)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True)
        
        # 创建标签显示区域
        self.tags_canvas = tk.Canvas(tag_frame)
        scrollbar_y = ttk.Scrollbar(tag_frame, orient="vertical", 
                                   command=self.tags_canvas.yview)
        scrollbar_x = ttk.Scrollbar(tag_frame, orient="horizontal", 
                                   command=self.tags_canvas.xview)
        
        # 创建网格布局框架
        self.tags_frame = ttk.Frame(self.tags_canvas)
        self.tags_per_row = 6  # 每行显示的标签数
        
        # 初始显示所有标签
        self.update_tags_display()
        
        # 配置滚动
        self.tags_canvas.create_window((0, 0), window=self.tags_frame, anchor="nw")
        self.tags_frame.bind("<Configure>", 
                            lambda e: self.tags_canvas.configure(
                                scrollregion=self.tags_canvas.bbox("all")))
        
        # 布局组件
        self.tags_canvas.configure(yscrollcommand=scrollbar_y.set,
                                 xscrollcommand=scrollbar_x.set)
        self.tags_canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

    def update_tags_display(self, filtered_tags=None):
        """更新标签显示
        参数:
            filtered_tags: 过滤后的标签列表，None表示显示所有标签
        """
        # 清除现有标签
        for widget in self.tags_frame.winfo_children():
            widget.destroy()
        
        # 确定要显示的标签
        tags_to_show = filtered_tags if filtered_tags is not None else self.tags
        
        # 计算最长标签名的长度
        max_length = max(len(tag) for tag in tags_to_show) if tags_to_show else 10
        button_width = min(max_length, 20)  # 限制最大宽度为20
        
        # 使用网格布局放置标签
        for i, tag in enumerate(tags_to_show):
            row = i // self.tags_per_row
            col = i % self.tags_per_row
            
            # 创建标签容器
            tag_container = ttk.Frame(self.tags_frame)
            tag_container.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            
            # 标签按钮
            btn = tk.Button(tag_container, 
                          text=tag,
                          width=10,  # 固定宽度为10
                          anchor="w",
                          justify="left",
                          command=lambda t=tag: self.toggle_tag(t))
            
            # 添加工具提示
            self.create_tooltip(btn, tag)
            btn.pack(side="left", padx=1)
            
            # 括号计数和控制按钮
            count_frame = ttk.Frame(tag_container)
            count_frame.pack(side="left")
            
            # 显示记忆的括号数量（如果有）或0
            initial_count = "0"
            if tag in self.selected_tags:
                initial_count = str(self.tag_brackets[tag])
            elif tag in self.remembered_brackets:
                initial_count = str(self.remembered_brackets[tag])
            
            count_label = ttk.Label(count_frame, text=initial_count, width=2)
            count_label.pack(side="left")
            
            ttk.Button(count_frame, text="+", width=2,
                    command=lambda t=tag: self.add_brackets(t)).pack(side="left")
            ttk.Button(count_frame, text="-", width=2,
                    command=lambda t=tag: self.remove_brackets(t)).pack(side="left")
            
            self.tag_buttons[tag] = btn
            self.bracket_counts[tag] = count_label

    def filter_tags(self, *args):
        """根据搜索文本过滤标签"""
        search_text = self.search_var.get().lower()
        if not search_text:
            self.update_tags_display()
        else:
            filtered = [tag for tag in self.tags 
                       if search_text in tag.lower()]
            self.update_tags_display(filtered)

    def add_new_tag(self):
        """添加新标签的方法
        数据流向：
        1. 获取输入的标签名和内容
        2. 验证输入有效性
        3. 保存到数据库
        4. 更新内存中的数据结构
        5. 重建界面显示
        """
        new_tag = self.new_tag_entry.get().strip()
        context = self.context_entry.get().strip()  # 获取context内容
        
        if new_tag:
            if new_tag not in self.tags:
                # 如果context为空，使用tag_name作为context
                if not context:
                    context = new_tag
                    
                if self.db_manager.add_tag(new_tag, context):
                    # 更新内存中的数据
                    self.tags[new_tag] = context  # 使用字典的赋值而不是append
                    
                    # 重建整个界面以显示新标签
                    for widget in self.main_frame.winfo_children():
                        widget.destroy()
                    
                    # 重新创建所有界面组件
                    self.create_add_tag_area()
                    self.create_tag_area()
                    self.create_output_area()
                    self.create_clear_button()
                    
                    # 清空输入框
                    self.new_tag_entry.delete(0, tk.END)
                    self.context_entry.delete(0, tk.END)
                else:
                    messagebox.showerror("错误", "添加标签失败！")
            else:
                messagebox.showwarning("警告", "该标签已存在！")

    def add_brackets(self, tag):
        """为指定标签添加一对花括号
        数据流向：
        1. self.tag_brackets[tag] 增加括号计数
        2. self.bracket_counts[tag] 更新显示的数字
        3. update_output() 重新生成输出文本
        """
        if tag in self.selected_tags:
            self.tag_brackets[tag] += 1  # 括号计数加1
            # Tkinter的Label需要字符串类型，所以用str()转换数字
            self.bracket_counts[tag].configure(text=str(self.tag_brackets[tag]))
            self.update_output()

    def update_output(self):
        """更新输出文本
        数据处理流程：
        1. 按括号数量对标签分组 -> bracket_groups
        2. 为每组标签添加对应数量的括号
        3. 将所有组合并为最终输出
        """
        # 按括号数量分组 {count: [contexts]}
        bracket_groups = {}
        for tag in self.selected_tags:
            count = self.tag_brackets[tag]
            if count not in bracket_groups:
                bracket_groups[count] = []
            bracket_groups[count].append(self.tags[tag])
        
        # 生成输出文本
        output_parts = []
        for count, contexts in sorted(bracket_groups.items()):
            group_text = ", ".join(contexts)  # 同组标签用逗号连接
            # 添加指定数量的花括号
            for _ in range(count):
                group_text = "{" + group_text + "}"
            if group_text:
                output_parts.append(group_text)
        
        # 更新文本框显示
        output = ", ".join(output_parts)  # 不同组用逗号连接
        self.output_text.delete(1.0, tk.END)
        if output:
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
        """清除所有选择和括号数量"""
        self.selected_tags.clear()
        self.remembered_brackets.clear()  # 清除记忆的括号数量
        # 重置所有标签的括号数量
        for tag in self.tag_brackets:
            self.tag_brackets[tag] = 0
            self.bracket_counts[tag].configure(text="0")
        self.output_text.delete(1.0, tk.END)

    def toggle_tag(self, tag):
        """切换标签选中状态
        数据流向：
        1. self.selected_tags 更新选中状态
        2. self.tag_buttons[tag] 更新按钮显示
        3. self.remembered_brackets[tag] 保存/恢复括号数量
        4. self.bracket_counts[tag] 更新显示的数字
        """
        if tag in self.selected_tags:
            # 取消选中
            self.selected_tags.remove(tag)
            self.tag_buttons[tag].configure(bg="SystemButtonFace")  # 设置按钮回到默认颜色
            # 保存当前括号数量
            self.remembered_brackets[tag] = self.tag_brackets[tag]
        else:
            # 选中标签
            self.selected_tags.append(tag)
            self.tag_buttons[tag].configure(bg="lightblue")  # 设置按钮为选中颜色
            # 恢复之前的括号数量（如果有）
            if tag in self.remembered_brackets:
                self.tag_brackets[tag] = self.remembered_brackets[tag]
            else:
                self.tag_brackets[tag] = 0
            self.db_manager.update_tag_usage(tag)
        
        # 更新显示的数字
        self.bracket_counts[tag].configure(text=str(self.tag_brackets[tag]))
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

    def create_tooltip(self, widget, text):
        """为控件创建工具提示"""
        ToolTip(widget, text)

def main():
    root = tk.Tk()
    app = TextGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main() 