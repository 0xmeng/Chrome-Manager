import tkinter as tk
from tkinter import ttk

class FolderFileTable(ttk.Frame):
    def __init__(self, master, folder_options, file_options, row_datas, selected_dict, **kwargs):
        super().__init__(master, **kwargs)
        print("selected -------- ")
        print(selected_dict)
        self.folder_options = folder_options
        self.file_options = file_options
        self.columns = ("编号", "配置名称", "线路名称")

        # ➤ 样式设置
        style = ttk.Style()
        style.configure("Custom.Treeview", rowheight=32)
        style.configure("Custom.Treeview.Heading")

        # ➤ Treeview + Scrollbar 容器
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=self.columns,
            show="headings",
            height=len(row_datas),
            yscrollcommand=vsb.set,
            style="Custom.Treeview"
        )
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
        vsb.config(command=self.tree.yview)

        for col in self.columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, anchor="center")

        # ➤ 初始数据填充
        for i in range(len(row_datas)):

            k = row_datas[i]
            selected_row = selected_dict.get(str(k))
            if selected_row:
                column1 = selected_row.get("proxy_group")
                column2 = selected_row.get("proxy_name")
            else:
                column1 = folder_options[0]
                column2 = file_options[column1][0] if file_options.get(column1) else ""
            self.tree.insert("", "end", values=(f"{row_datas[i]}", column1, column2))

        # ➤ 下拉选择控件
        self.folder_combo = ttk.Combobox(self, values=self.folder_options, state="readonly")
        self.file_combo = ttk.Combobox(self, state="readonly")
        self.editing_info = {"item": None, "column": None}

        self.tree.bind("<Button-1>", self._on_tree_click)
        self.folder_combo.bind("<<ComboboxSelected>>", self._on_folder_selected)
        self.file_combo.bind("<<ComboboxSelected>>", self._on_file_selected)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        col_index = int(col_id[1:]) - 1
        if col_index not in [1, 2]:
            return

        bbox = self.tree.bbox(row_id, col_id)
        if not bbox:
            return

        x, y, width, height = bbox
        value = self.tree.set(row_id, self.columns[col_index])
        self.editing_info.update(item=row_id, column=self.columns[col_index])

        if col_index == 1:  # Folder
            self.folder_combo.place(x=x, y=y + self.tree.winfo_y(), width=width, height=height)
            self.folder_combo.set(value)
            self.folder_combo.focus()
        elif col_index == 2:  # File
            folder = self.tree.set(row_id,  self.columns[1])
            self.file_combo["values"] = self.file_options.get(folder, [])
            self.file_combo.place(x=x, y=y + self.tree.winfo_y(), width=width, height=height)
            self.file_combo.set(value)
            self.file_combo.focus()

    def _on_folder_selected(self, event):
        item = self.editing_info["item"]
        new_folder = self.folder_combo.get()
        self.tree.set(item,  self.columns[1], new_folder)
        default_file = self.file_options.get(new_folder, [""])[0]
        self.tree.set(item,  self.columns[2], default_file)
        self.folder_combo.place_forget()

    def _on_file_selected(self, event):
        item = self.editing_info["item"]
        new_file = self.file_combo.get()
        self.tree.set(item,  self.columns[2], new_file)
        self.file_combo.place_forget()

    def get_data(self):
        rst = [
            dict(zip(self.columns, self.tree.item(item)["values"]))
            for item in self.tree.get_children()
        ]
        rst_dict = {}
        for item in rst:
            row0 = item.get(self.columns[0])
            row1 = item.get(self.columns[1])
            row2 = item.get(self.columns[2])
            rst_dict[str(row0)] = {"proxy_group": row1, "proxy_name": row2}
        return rst_dict

# --------------------------
# ✅ 主界面布局：表格+按钮
# --------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.title("FolderFile 表格组件示例")
    root.geometry("800x600")

    # ➤ 外层 Frame 使用 grid，避免按钮被表格覆盖
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)
    main_frame.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=1)

    # ➤ 示例数据
    folders = ["FolderA", "FolderB", "FolderC"]
    files = {
        "FolderA": ["file1.txt", "file2.txt"],
        "FolderB": ["file3.txt", "file4.txt"],
        "FolderC": ["file5.txt", "file6.txt"],
    }

    # ➤ 插入表格
    table = FolderFileTable(main_frame, folders, files, rows=30)
    table.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # ➤ 底部按钮（不会被挤掉）
    def show_data():
        print("📦 当前表格内容：")
        for row in table.get_data():
            print(row)

    ttk.Button(main_frame, text="打印表格数据", command=show_data).grid(row=1, column=0, pady=10)

    root.mainloop()
