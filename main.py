import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import re
import time

class YoutubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("700x150")
        self.root.resizable(False, False)
        self.center_window(self.root)

        self.url_label = tk.Label(root, text="Ссылка на видео YouTube:")
        self.url_label.pack(pady=5)

        self.url_entry = tk.Entry(root, width=90)
        self.url_entry.pack()

        self.fetch_btn = tk.Button(root, text="Получить форматы", command=self.fetch_formats_thread)
        self.fetch_btn.pack(pady=10)

        self.selected_formats = []

    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def fetch_formats_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Ошибка", "Введите ссылку на видео")
            return
        threading.Thread(target=self.fetch_formats, args=(url,), daemon=True).start()

    def fetch_formats(self, url):
        self.fetch_btn.config(state="disabled")
        cmd = ["yt-dlp", "-F", url]
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить yt-dlp:\n{e}")
            self.fetch_btn.config(state="normal")
            return

        formats = []
        for line in process.stdout:
            line = line.strip()
            if re.match(r"^\d+", line):
                parts = re.split(r"\s{2,}", line)
                if len(parts) >= 4:
                    format_id = parts[0]
                    ext = parts[1]
                    resolution = parts[2]
                    size = ""
                    note = ""
                    if len(parts) == 4:
                        note = parts[3]
                        m_size = re.search(r"(\d+(\.\d+)?\s?[KMG]iB)", note)
                        if m_size:
                            size = m_size.group(1)
                    elif len(parts) >= 5:
                        size_candidate = parts[3]
                        if re.match(r"\d+(\.\d+)?\s?[KMG]iB", size_candidate):
                            size = size_candidate
                            note = parts[4]
                        else:
                            note = " ".join(parts[3:])
                    formats.append((format_id, ext, resolution, size, note))

        self.fetch_btn.config(state="normal")

        if not formats:
            messagebox.showinfo("Информация", "Форматы не найдены или ошибка при получении")
            return

        self.show_formats_window(formats, url)

    def show_formats_window(self, formats, url):
        self.formats_window = tk.Toplevel(self.root)
        self.formats_window.title("Доступные форматы")
        self.formats_window.geometry("700x400")
        self.center_window(self.formats_window)

        label = tk.Label(self.formats_window, text="Выберите форматы для скачивания (Ctrl+клик для множественного выбора):")
        label.pack(pady=5)

        columns = ("format_id", "ext", "resolution", "size", "note")
        self.formats_tree = ttk.Treeview(self.formats_window, columns=columns, show="headings", selectmode="extended")
        self.formats_tree.heading("format_id", text="ID")
        self.formats_tree.heading("ext", text="Расширение")
        self.formats_tree.heading("resolution", text="Разрешение")
        self.formats_tree.heading("size", text="Размер")
        self.formats_tree.heading("note", text="Примечание")

        self.formats_tree.column("format_id", width=50, anchor="center")
        self.formats_tree.column("ext", width=80, anchor="center")
        self.formats_tree.column("resolution", width=100, anchor="center")
        self.formats_tree.column("size", width=80, anchor="center")
        self.formats_tree.column("note", width=320, anchor="w")

        scrollbar = ttk.Scrollbar(self.formats_window, orient=tk.VERTICAL, command=self.formats_tree.yview)
        self.formats_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.formats_tree.pack(expand=True, fill=tk.BOTH)

        for fmt in formats:
            self.formats_tree.insert("", tk.END, values=fmt)

        btn_download = tk.Button(self.formats_window, text="Начать скачивание", command=self.select_formats_and_download)
        btn_download.pack(pady=10)

        self.formats_window.transient(self.root)
        self.formats_window.grab_set()
        self.formats_window.focus_set()

    def select_formats_and_download(self):
        selected_items = self.formats_tree.selection()
        if not selected_items:
            messagebox.showwarning("Ошибка", "Выберите хотя бы один формат")
            return
        self.selected_formats = [str(self.formats_tree.item(i)["values"][0]) for i in selected_items]

        self.formats_window.destroy()
        self.start_download()

    def start_download(self):
        self.root.withdraw()

        self.download_window = tk.Toplevel()
        self.download_window.title("Скачивание видео")
        self.download_window.geometry("600x150")
        self.center_window(self.download_window)

        self.filename_label = tk.Label(self.download_window, text="Имя файла:")
        self.filename_label.pack(pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.download_window, length=550, variable=self.progress_var)
        self.progress_bar.pack(pady=10)

        self.status_label = tk.Label(self.download_window, text="Статус: Ожидание...")
        self.status_label.pack()

        threading.Thread(target=self.download_video_thread, daemon=True).start()

    def download_video_thread(self):
        url = self.url_entry.get().strip()
        formats_str = "+".join(map(str, self.selected_formats))
        cmd = [
            "yt-dlp",
            "-f", formats_str,
            "-o", "%(title)s [%(id)s].%(ext)s",
            url,
            "--newline",
            "--no-cache-dir",
            "--restrict-filenames"
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)

        filename = ""
        for line in process.stdout:
            line = line.strip()
            m_filename = re.search(r"Destination: (.+)$", line)
            if m_filename:
                filename = m_filename.group(1)
                self.download_window.after(0, lambda: self.filename_label.config(text=f"Имя файла: {filename}"))

            m_progress = re.search(r"\[download\]\s+(\d{1,3}\.\d)%", line)
            m_speed = re.search(r"at\s+([\d\.]+\w+/s)", line)
            if m_progress:
                perc = float(m_progress.group(1))
                speed = m_speed.group(1) if m_speed else "..."
                status_text = f"Загрузка... {perc:.2f}% Скорость: {speed}"
                self.download_window.after(0, lambda st=status_text, p=perc: self.update_progress(st, p))

        process.wait()

        if process.returncode == 0:
            self.download_window.after(0, lambda: self.status_label.config(text="Скачивание завершено!"))
        else:
            self.download_window.after(0, lambda: self.status_label.config(text=f"Ошибка при скачивании. Код: {process.returncode}"))

        self.download_window.after(5000, self.close_download_window)

    def update_progress(self, status_text, percent):
        self.status_label.config(text=status_text)
        self.progress_var.set(percent)

    def close_download_window(self):
        self.download_window.destroy()
        self.root.deiconify()

def main():
    root = tk.Tk()
    app = YoutubeDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
