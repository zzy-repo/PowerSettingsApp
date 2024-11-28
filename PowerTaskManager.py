import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import subprocess
import re


class AddTask:
    def __init__(self, root, task_manager):
        self.top = tk.Toplevel(root)
        self.top.title("电源任务设置")

        self.task_manager = task_manager  # 引用任务管理器

        irow = 0
        self.task_name_label = ttk.Label(self.top, text="任务名称：")
        self.task_name_label.grid(row=irow, column=0, padx=10, pady=5)
        self.task_name = ttk.Entry(self.top)
        self.task_name.grid(row=irow, column=1, padx=10, pady=5)
        self.task_name.insert(0, "白天")

        irow += 1
        self.start_label = ttk.Label(self.top, text="开始时间（HH:MM）：")
        self.start_label.grid(row=irow, column=0, padx=10, pady=5)
        self.start_time = ttk.Entry(self.top)
        self.start_time.grid(row=irow, column=1, padx=10, pady=5)
        self.start_time.insert(0, "07:00")

        irow += 1
        self.sleep_label = ttk.Label(self.top, text="电脑休眠时间（分钟）：")
        self.sleep_label.grid(row=irow, column=0, padx=10, pady=5)
        self.sleep_time = ttk.Entry(self.top)
        self.sleep_time.grid(row=irow, column=1, padx=10, pady=5)
        self.sleep_time.insert(0, "3")  # 默认设置3分钟

        irow += 1
        self.screen_off_label = ttk.Label(self.top, text="屏幕关闭时间（分钟）：")
        self.screen_off_label.grid(row=irow, column=0, padx=10, pady=5)
        self.screen_off_time = ttk.Entry(self.top)
        self.screen_off_time.grid(row=irow, column=1, padx=10, pady=5)
        self.screen_off_time.insert(0, "3")  # 默认设置3分钟

        irow += 1
        self.save_button = ttk.Button(self.top, text="保存设置", command=self.save_settings)
        self.save_button.grid(row=irow, column=0, columnspan=2, pady=20)

    def save_settings(self):
        # 获取用户输入的时间设置
        task_name = self.task_name.get()
        start_time = self.start_time.get()
        screen_off_time = self.screen_off_time.get()
        sleep_time = self.sleep_time.get()

        if not self.validate_time_input(start_time):
            messagebox.showerror("不正确的时间格式", "请以 HH:MM 格式输入有效时间。")
            return

        # 设置电源策略
        if self.create_task(task_name, start_time, screen_off_time, sleep_time):
            self.top.destroy()  # 关闭子窗口

    def validate_time_input(self, new_value):
        # 使用正则表达式验证时间格式
        if new_value == "" or new_value.count(":") == 1:
            hours_minutes = new_value.split(":")
            if len(hours_minutes) == 2:
                hours, minutes = hours_minutes
                if len(hours) == 2 and hours.isdigit() and 0 <= int(hours) <= 23:
                    if len(minutes) == 2 and minutes.isdigit() and 0 <= int(minutes) <= 59:
                        return True
        return False

    def create_task(self, task_name, start_time, screen_off_minutes, sleep_minutes):
        """
        创建定时任务，用于设置屏幕关闭时间和休眠时间
        """
        # 生成任务调度命令
        task_name = f"PowerSettingsApp - {task_name}"
        powercfg_command = f"powercfg -change monitor-timeout-ac {screen_off_minutes}"
        sleep_command = f"powercfg -change standby-timeout-ac {sleep_minutes}"

        # 构建创建任务的命令
        command = f"""
        schtasks /create /tn "{task_name}" /tr "{powercfg_command} && {sleep_command}" /sc daily /st {start_time} /f
        """
        command = command.strip()

        res = subprocess.run(command, capture_output=True, text=True, shell=True)

        # 输出
        if res.returncode == 0:
            print(f"STDOUT: {res.stdout}")
            messagebox.showinfo("运行成功", res.stdout)

            # 任务创建成功后更新任务管理器的任务列表
            self.task_manager.refresh_tasks()
            return True
        else:
            print("Error!")
            print(command)
            print(f"STDERR: {res.stderr}")
            messagebox.showerror("错误", res.stderr)
            return False


class PowerTaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("睡眠任务管理器")

        # 创建任务表格（Treeview）
        self.tree = ttk.Treeview(root, columns=("Task Name", "Start Time", "Screen Off", "Sleep Time"), show="headings")
        self.tree.heading("Task Name", text="任务名称")
        self.tree.heading("Start Time", text="开始时间")
        self.tree.heading("Screen Off", text="屏幕关闭时间（分钟）")
        self.tree.heading("Sleep Time", text="休眠时间（分钟）")
        self.tree.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

        # 添加按钮
        self.add_button = ttk.Button(root, text="添加任务", width=15, command=self.add_task)
        self.add_button.grid(row=1, column=0, padx=10, pady=5)

        # 删除按钮
        self.delete_button = ttk.Button(root, text="删除任务", width=15, command=self.delete_task)
        self.delete_button.grid(row=1, column=1, padx=10, pady=5)

        # 刷新按钮
        self.refresh_button = ttk.Button(root, text="刷新任务", width=15, command=self.refresh_tasks)
        self.refresh_button.grid(row=1, column=2, padx=10, pady=5)

        # 初始化任务列表
        self.refresh_tasks()

    def refresh_tasks(self):
        """
        刷新任务表格，显示当前所有的计划任务。
        """
        # 清空表格
        for row in self.tree.get_children():
            self.tree.delete(row)

        command = 'schtasks /query /fo LIST /v'

        # 执行命令并捕获输出
        res = subprocess.run(command, capture_output=True, text=True, shell=True)

        if res.returncode != 0:
            print("Error querying tasks.")
            print(f"STDERR: {res.stderr}")
            return []

        # 分割输出并提取任务名称及相关信息
        task_info = [t for t in res.stdout.split('\n\n') if "PowerSettingsApp" in t]

        for task in task_info:
            task_name = re.search(r"任务名:\s*\\PowerSettingsApp\s*-\s*(\S+)", task).group(1)
            start_time = re.search(r"开始时间:\s*(\S*\s*\S*)", task).group(1)
            screen_off = re.search(r"monitor-timeout-ac\s*(\S*)", task).group(1)
            sleep_time = re.search(r"standby-timeout-ac\s*(\S*)", task).group(1)

            self.tree.insert("", "end", values=(task_name, start_time, screen_off, sleep_time))

    def add_task(self):
        """
        添加一个新的任务
        """
        AddTask(self.root, self)

    def delete_task(self):
        """
        删除选中的任务
        """
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("选择错误", "请先选择一个任务")
            return
        task_name = f"""PowerSettingsApp - {self.tree.item(selected_item[0], "values")[0]}"""
        command = f'schtasks /delete /tn "{task_name}" /f'
        subprocess.run(command, shell=True)

        # 刷新任务列表
        self.refresh_tasks()

        messagebox.showinfo("成功", f"任务 '{task_name}' 已删除")


if __name__ == "__main__":
    root = tk.Tk()
    app = PowerTaskManager(root)
    root.mainloop()
