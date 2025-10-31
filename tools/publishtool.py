import json
import os
import shutil
import datetime
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog

class NavigationEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Navigation Editor")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure("TNotebook.Tab", font=("SimHei", 10))
        self.style.configure("TLabel", font=("SimHei", 10))
        self.style.configure("TButton", font=("SimHei", 10))
        
        # 数据存储
        self.navigation_data = None
        self.original_data = None  # 用于检测变化
        self.json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "navsphere", "content", "navigation.json")
        self.backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "navsphere", "content", "backups")
        
        # 创建备份目录
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding=(10, 10, 10, 10))
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建顶部操作栏
        self.create_toolbar()
        
        # 创建标签页控件
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 尝试加载JSON文件
        self.load_navigation_json()
        
        # 窗口关闭时检查是否保存
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_menu(self):
        # 创建菜单栏
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开文件", command=self.open_file_dialog)
        file_menu.add_command(label="保存", command=self.save_json, accelerator="Ctrl+S")
        file_menu.add_command(label="备份当前文件", command=self.backup_current_file)
        file_menu.add_command(label="从备份恢复", command=self.restore_from_backup)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="添加项目", command=self.add_item)
        edit_menu.add_command(label="删除项目", command=self.delete_item)
        edit_menu.add_command(label="复制项目", command=self.copy_item)
        edit_menu.add_command(label="粘贴项目", command=self.paste_item)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        # 设置菜单栏
        self.root.config(menu=menubar)
        
        # 绑定快捷键
        self.root.bind("<Control-s>", lambda event: self.save_json())
    
    def create_toolbar(self):
        # 创建顶部操作栏
        toolbar = ttk.Frame(self.main_frame, padding=(5, 5, 5, 5))
        toolbar.pack(fill=tk.X, pady=5)
        
        # 保存按钮
        save_btn = ttk.Button(toolbar, text="保存", command=self.save_json)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # 备份按钮
        backup_btn = ttk.Button(toolbar, text="备份", command=self.backup_current_file)
        backup_btn.pack(side=tk.LEFT, padx=5)
        
        # 恢复按钮
        restore_btn = ttk.Button(toolbar, text="从备份恢复", command=self.restore_from_backup)
        restore_btn.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        refresh_btn = ttk.Button(toolbar, text="刷新", command=self.load_navigation_json)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(toolbar, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
    
    def open_file_dialog(self):
        # 检查是否有未保存的更改
        if self.has_unsaved_changes():
            response = messagebox.askyesnocancel("未保存的更改", 
                                               "您有未保存的更改。是否保存当前内容？")
            if response is None:  # 取消操作
                return
            if response:  # 保存更改
                self.save_json()
        
        # 打开文件对话框
        file_path = filedialog.askopenfilename(
            title="打开JSON文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            self.json_path = file_path
            self.load_navigation_json()
    
    def load_navigation_json(self):
        try:
            with open(self.json_path, 'r', encoding='utf-8') as file:
                self.navigation_data = json.load(file)
                # 深拷贝原始数据用于比较
                self.original_data = json.dumps(self.navigation_data, ensure_ascii=False)
                
            # 清除现有的标签页
            for tab in self.notebook.tabs():
                self.notebook.forget(tab)
            
            # 处理导航数据
            if "navigationItems" in self.navigation_data:
                self._create_tabs_from_navigation(self.navigation_data["navigationItems"])
                self.status_var.set(f"已加载文件: {os.path.basename(self.json_path)}")
            else:
                self.show_error("JSON格式错误", "未找到 'navigationItems' 字段")
                
        except FileNotFoundError:
            self.show_error("文件未找到", f"无法找到文件: {self.json_path}")
        except json.JSONDecodeError as e:
            self.show_error("JSON解析错误", f"解析JSON文件时出错: {str(e)}")
        except Exception as e:
            self.show_error("加载错误", f"加载文件时出错: {str(e)}")
    
    def _create_tabs_from_navigation(self, navigation_items):
        # 为每个导航项创建标签页
        for nav_item in navigation_items:
            # 创建标签页内容框架
            tab_frame = ttk.Frame(self.notebook)
            tab_frame.pack_propagate(False)
            
            # 设置标签页名称
            tab_title = nav_item.get("title", "未命名")
            self.notebook.add(tab_frame, text=tab_title)
            
            # 在标签页中创建Treeview
            self._create_treeview(tab_frame, nav_item, nav_item)
    
    def _create_treeview(self, parent_frame, data_item, parent_data=None, parent_id=""):
        # 创建框架来容纳Treeview和滚动条
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建垂直滚动条
        yscroll = ttk.Scrollbar(tree_frame)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建水平滚动条
        xscroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 创建Treeview
        tree = ttk.Treeview(tree_frame, yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        tree.pack(fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        yscroll.config(command=tree.yview)
        xscroll.config(command=tree.xview)
        
        # 设置Treeview列
        tree['columns'] = ('key', 'value', 'type')
        tree.column('#0', width=100, minwidth=100)
        tree.column('key', width=150, minwidth=100)
        tree.column('value', width=400, minwidth=200)
        tree.column('type', width=80, minwidth=80)
        
        # 设置列标题
        tree.heading('#0', text='路径')
        tree.heading('key', text='键')
        tree.heading('value', text='值')
        tree.heading('type', text='类型')
        
        # 存储对数据的引用
        tree.data_item = data_item
        tree.parent_data = parent_data
        
        # 填充Treeview - 使用空字符串作为根节点
        self._populate_tree(tree, "", data_item, "")
        
        # 绑定双击事件用于编辑
        tree.bind("<Double-1>", self.on_item_double_click)
        
        # 绑定右键菜单
        tree.bind("<Button-3>", self.show_context_menu)
    
    def _populate_tree(self, tree, parent_id, data, path):
        if isinstance(data, dict):
            for key, value in data.items():
                # 创建新节点
                item_id = f"{parent_id}_{key}" if parent_id else key
                new_path = f"{path}.{key}" if path else key
                
                # 确定值的显示文本
                if isinstance(value, dict):
                    value_text = "{...}"
                    value_type = "对象"
                elif isinstance(value, list):
                    value_text = f"[{len(value)} 项]"
                    value_type = "数组"
                else:
                    value_text = str(value) if value is not None else ""
                    value_type = "字符串" if isinstance(value, str) else "布尔值" if isinstance(value, bool) else "数字" if isinstance(value, (int, float)) else "None"
                
                # 插入节点
                tree.insert(parent_id, "end", item_id, text=new_path, values=(key, value_text, value_type))
                
                # 递归填充子节点
                if isinstance(value, (dict, list)):
                    self._populate_tree(tree, item_id, value, new_path)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                # 创建新节点
                item_id = f"{parent_id}_{i}" if parent_id else str(i)
                new_path = f"{path}[{i}]"
                
                # 确定值的显示文本
                if isinstance(item, dict):
                    value_text = "{...}" if item else "{}"
                    value_type = "对象"
                elif isinstance(item, list):
                    value_text = f"[{len(item)} 项]"
                    value_type = "数组"
                else:
                    value_text = str(item) if item is not None else ""
                    value_type = "字符串" if isinstance(item, str) else "布尔值" if isinstance(value, bool) else "数字" if isinstance(value, (int, float)) else "None"
                
                # 插入节点
                tree.insert(parent_id, "end", item_id, text=new_path, values=(f"[{i}]", value_text, value_type))
                
                # 递归填充子节点
                if isinstance(item, (dict, list)):
                    self._populate_tree(tree, item_id, item, new_path)
    
    def on_item_double_click(self, event):
        # 获取双击的项
        tree = event.widget
        item_id = tree.identify_row(event.y)
        
        if item_id:
            # 获取项的值
            values = tree.item(item_id, "values")
            if not values:
                return
            
            key, current_value, value_type = values
            
            # 确定是否可以编辑（不允许编辑对象和数组的顶层表示）
            if value_type in ["对象", "数组"]:
                return
            
            # 获取该项的数据路径
            path = tree.item(item_id, "text")
            
            # 显示编辑对话框
            new_value = simpledialog.askstring("编辑值", f"编辑 {key} 的值:", initialvalue=current_value)
            
            if new_value is not None:  # 用户没有取消
                # 根据类型转换值
                if value_type == "布尔值":
                    new_value = new_value.lower() in ('true', 'yes', '1', 'y', 't')
                elif value_type == "数字":
                    try:
                        new_value = int(new_value) if '.' not in new_value else float(new_value)
                    except ValueError:
                        messagebox.showerror("类型错误", "输入的值无法转换为数字")
                        return
                
                # 更新Treeview中的显示
                tree.item(item_id, values=(key, str(new_value), value_type))
                
                # 更新数据对象
                self._update_data_at_path(tree.data_item, path, new_value)
                
                # 更新状态
                self.status_var.set("数据已修改（未保存）")
    
    def _update_data_at_path(self, data, path, new_value):
        # 解析路径并更新数据
        parts = path.split('.')
        current = data
        
        # 处理路径的每个部分
        for i, part in enumerate(parts):
            # 检查是否是数组索引
            if part.startswith('[') and part.endswith(']'):
                index = int(part[1:-1])
                if i == len(parts) - 1:  # 最后一部分
                    current[index] = new_value
                else:
                    current = current[index]
            else:
                # 普通键
                if i == len(parts) - 1:  # 最后一部分
                    current[part] = new_value
                else:
                    current = current[part]
    
    def show_context_menu(self, event):
        # 创建右键菜单
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="编辑", command=lambda: self.edit_selected_item(event.widget))
        context_menu.add_command(label="删除", command=lambda: self.delete_selected_item(event.widget))
        context_menu.add_command(label="复制", command=lambda: self.copy_selected_item(event.widget))
        context_menu.add_command(label="粘贴", command=lambda: self.paste_item_to_selected(event.widget))
        
        # 显示菜单
        context_menu.post(event.x_root, event.y_root)
    
    def edit_selected_item(self, tree):
        # 获取选中的项
        selected = tree.selection()
        if selected:
            # 创建一个模拟的事件对象
            class MockEvent:
                def __init__(self, widget, y=0):
                    self.widget = widget
                    self.y = y
            
            # 模拟双击事件
            item_id = selected[0]
            values = tree.item(item_id, "values")
            if values and values[2] not in ["对象", "数组"]:
                # 获取项的y坐标（这里使用一个估计值）
                bbox = tree.bbox(item_id)
                y = bbox[1] if bbox else 0
                mock_event = MockEvent(tree, y)
                self.on_item_double_click(mock_event)
    
    def delete_selected_item(self, tree):
        # 获取选中的项
        selected = tree.selection()
        if selected:
            item_id = selected[0]
            path = tree.item(item_id, "text")
            
            # 确认删除
            if messagebox.askyesno("确认删除", f"确定要删除 {path} 吗？"):
                # 从Treeview中删除
                tree.delete(item_id)
                
                # 从数据中删除
                self._delete_data_at_path(tree.data_item, path)
                
                # 更新状态
                self.status_var.set("数据已修改（未保存）")
    
    def _delete_data_at_path(self, data, path):
        # 解析路径并删除数据
        parts = path.split('.')
        current = data
        parent = None
        last_key = None
        
        # 遍历路径，找到要删除的项的父级
        for i, part in enumerate(parts):
            parent = current
            
            if part.startswith('[') and part.endswith(']'):
                last_key = int(part[1:-1])
                if i < len(parts) - 1:  # 不是最后一部分
                    current = current[last_key]
            else:
                last_key = part
                if i < len(parts) - 1:  # 不是最后一部分
                    current = current[part]
        
        # 删除项
        if isinstance(parent, list):
            del parent[last_key]
        elif isinstance(parent, dict):
            del parent[last_key]
    
    def copy_selected_item(self, tree):
        # 此功能可以后续实现
        pass
    
    def paste_item_to_selected(self, tree):
        # 此功能可以后续实现
        pass
    
    def add_item(self):
        # 此功能可以后续实现
        pass
    
    def delete_item(self):
        # 获取当前选中的标签页
        current_tab = self.notebook.select()
        if current_tab:
            # 获取标签页中的Treeview
            tab_frame = self.notebook.nametowidget(current_tab)
            tree = tab_frame.winfo_children()[0].winfo_children()[2]  # 获取Treeview组件
            self.delete_selected_item(tree)
    
    def copy_item(self):
        # 获取当前选中的标签页
        current_tab = self.notebook.select()
        if current_tab:
            # 获取标签页中的Treeview
            tab_frame = self.notebook.nametowidget(current_tab)
            tree = tab_frame.winfo_children()[0].winfo_children()[2]  # 获取Treeview组件
            self.copy_selected_item(tree)
    
    def paste_item(self):
        # 获取当前选中的标签页
        current_tab = self.notebook.select()
        if current_tab:
            # 获取标签页中的Treeview
            tab_frame = self.notebook.nametowidget(current_tab)
            tree = tab_frame.winfo_children()[0].winfo_children()[2]  # 获取Treeview组件
            self.paste_item_to_selected(tree)
    
    def save_json(self):
        if not self.navigation_data:
            messagebox.showinfo("信息", "没有可保存的数据")
            return
        
        try:
            # 创建备份
            self.create_backup()
            
            # 保存文件
            with open(self.json_path, 'w', encoding='utf-8') as file:
                json.dump(self.navigation_data, file, ensure_ascii=False, indent=2)
            
            # 更新原始数据引用
            self.original_data = json.dumps(self.navigation_data, ensure_ascii=False)
            
            # 更新状态
            self.status_var.set(f"已保存文件: {os.path.basename(self.json_path)}")
            messagebox.showinfo("成功", "文件已成功保存")
            
        except Exception as e:
            self.show_error("保存错误", f"保存文件时出错: {str(e)}")
    
    def backup_current_file(self):
        try:
            # 创建备份
            backup_path = self.create_backup()
            messagebox.showinfo("成功", f"备份已创建: {os.path.basename(backup_path)}")
        except Exception as e:
            self.show_error("备份错误", f"创建备份时出错: {str(e)}")
    
    def create_backup(self):
        # 生成备份文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"navigation_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        # 创建备份
        shutil.copy2(self.json_path, backup_path)
        return backup_path
    
    def restore_from_backup(self):
        # 列出所有备份文件
        try:
            backups = [f for f in os.listdir(self.backup_dir) if f.startswith("navigation_") and f.endswith(".json")]
            backups.sort(reverse=True)  # 最新的备份在前
            
            if not backups:
                messagebox.showinfo("信息", "没有找到备份文件")
                return
            
            # 创建选择对话框
            backup_window = tk.Toplevel(self.root)
            backup_window.title("选择备份文件")
            backup_window.geometry("600x400")
            backup_window.transient(self.root)
            backup_window.grab_set()
            
            # 创建列表框
            listbox = tk.Listbox(backup_window, font=("SimHei", 10), width=80, height=20)
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(listbox, orient=tk.VERTICAL, command=listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.config(yscrollcommand=scrollbar.set)
            
            # 填充列表
            for backup in backups:
                listbox.insert(tk.END, backup)
            
            # 选择按钮
            def on_select():
                selection = listbox.curselection()
                if selection:
                    selected_backup = listbox.get(selection[0])
                    backup_path = os.path.join(self.backup_dir, selected_backup)
                    
                    # 确认恢复
                    if messagebox.askyesno("确认恢复", f"确定要从备份 '{selected_backup}' 恢复吗？\n这将覆盖当前文件。"):
                        # 创建当前文件的备份
                        self.create_backup()
                        
                        # 复制备份文件到原始位置
                        shutil.copy2(backup_path, self.json_path)
                        
                        # 重新加载数据
                        self.load_navigation_json()
                        
                        backup_window.destroy()
                        messagebox.showinfo("成功", "已从备份恢复")
            
            # 按钮框架
            btn_frame = ttk.Frame(backup_window)
            btn_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(btn_frame, text="选择", command=on_select).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="取消", command=backup_window.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            self.show_error("恢复错误", f"恢复备份时出错: {str(e)}")
    
    def has_unsaved_changes(self):
        if not self.navigation_data or not self.original_data:
            return False
        return json.dumps(self.navigation_data, ensure_ascii=False) != self.original_data
    
    def on_closing(self):
        # 检查是否有未保存的更改
        if self.has_unsaved_changes():
            response = messagebox.askyesnocancel("未保存的更改", 
                                               "您有未保存的更改。是否保存当前内容？")
            if response is None:  # 取消操作
                return
            if response:  # 保存更改
                self.save_json()
        
        # 关闭窗口
        self.root.destroy()
    
    def show_error(self, title, message):
        # 显示错误对话框
        messagebox.showerror(title, message)
    
    def show_about(self):
        # 显示关于对话框
        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("400x250")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        # 计算居中位置
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 125
        about_window.geometry(f"400x250+{x}+{y}")
        
        # 内容
        content_frame = ttk.Frame(about_window, padding=(20, 20, 20, 20))
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Navigation Editor", font=("SimHei", 14, "bold")).pack(pady=10)
        ttk.Label(content_frame, text="版本: 1.1", font=("SimHei", 10)).pack(pady=5)
        ttk.Label(content_frame, text="用于编辑导航JSON文件的工具", font=("SimHei", 10)).pack(pady=5)
        ttk.Label(content_frame, text="支持编辑、保存和备份功能", font=("SimHei", 10)).pack(pady=5)
        ttk.Label(content_frame, text="© 2024 NavSphere", font=("SimHei", 10)).pack(pady=15)
        
        # 确定按钮
        ttk.Button(content_frame, text="确定", command=about_window.destroy).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    # 设置中文字体支持
    root.option_add("*Font", ("SimHei", 10))
    app = NavigationEditor(root)
    root.mainloop()