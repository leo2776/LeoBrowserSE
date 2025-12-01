import sys, os, json, threading
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

# ==========================================================
#  設定
# ==========================================================

APP_NAME = "LeoBrowserSE"
APP_VERSION = "1.0"
PROFILE_DIR = "LeoProfile"
BOOKMARK_FILE = os.path.join(PROFILE_DIR, "bookmarks.json")

if not os.path.exists(PROFILE_DIR):
    os.makedirs(PROFILE_DIR)


# ==========================================================
# 書籤系統
# ==========================================================

def load_bookmarks():
    if not os.path.exists(BOOKMARK_FILE):
        return []
    try:
        with open(BOOKMARK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_bookmarks(data):
    with open(BOOKMARK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

bookmarks = load_bookmarks()


# ==========================================================
# 分頁
# ==========================================================

class BrowserTab(QWidget):
    def __init__(self, profile):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.view = QWebEngineView()
        self.layout.addWidget(self.view)

        # User-Agent - Google 會提供最新 UI
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            f"LeoBrowserSE/{APP_VERSION} Chrome/124.0.0.0 Safari/537.36"
        )
        profile.setHttpUserAgent(ua)

        self.view.setPage(QWebEnginePage(profile, self))

    def load(self, url):
        if not url.startswith("http"):
            url = "https://" + url
        self.view.load(QUrl(url))


# ==========================================================
# 主視窗
# ==========================================================

class LeoBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1280, 830)

        # Profile 隔離
        self.profile = QWebEngineProfile(PROFILE_DIR, self)

        # Tab 控制
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        # 工具列
        toolbar = QToolBar("toolbar")
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)

        # URL 欄
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.load_url)
        toolbar.addWidget(self.urlbar)

        # 🔒 安全鎖圖標
        self.lock_icon = QLabel()
        toolbar.addWidget(self.lock_icon)

        # 三點選單（B 進階版）
        menu_btn = QPushButton("⋮")
        menu_btn.setFixedWidth(30)
        menu_btn.clicked.connect(self.open_menu)
        toolbar.addWidget(menu_btn)

        # 新增初始分頁
        self.new_tab("https://www.google.com")

        # F12 打開 DevTools
        QShortcut(QKeySequence("F12"), self, activated=self.open_devtools)

    # ======================================================
    # 分頁功能
    # ======================================================

    def new_tab(self, url):
        tab = BrowserTab(self.profile)
        idx = self.tabs.addTab(tab, "新分頁")
        self.tabs.setCurrentIndex(idx)

        tab.view.titleChanged.connect(lambda t: self.update_title(idx, t))
        tab.view.urlChanged.connect(self.update_urlbar)
        tab.view.loadFinished.connect(self.update_lock)

        tab.load(url)

    def update_title(self, index, title):
        self.tabs.setTabText(index, title)

    def update_urlbar(self, url):
        self.urlbar.setText(url.toString())
        self.update_lock()

    def load_url(self):
        tab = self.current_tab()
        if tab:
            tab.load(self.urlbar.text())

    def current_tab(self):
        return self.tabs.currentWidget()

    def close_tab(self, index):
        if self.tabs.count() == 1:
            return
        self.tabs.removeTab(index)

    # ======================================================
    # 🔒 HTTPS / 不安全提示
    # ======================================================

    def update_lock(self):
        url = self.urlbar.text()
        if url.startswith("https://"):
            self.lock_icon.setText("🔒")
        else:
            self.lock_icon.setText("⚠ 不安全")

    # ======================================================
    # 三點選單（進階版 B）
    # ======================================================

    def open_menu(self):
        menu = QMenu()

        menu.addAction("新增分頁", lambda: self.new_tab("https://google.com"))
        menu.addAction("關閉目前分頁", lambda: self.close_tab(self.tabs.currentIndex()))
        menu.addSeparator()

        menu.addAction("書籤管理", self.manage_bookmarks)
        menu.addAction("加入書籤", self.add_bookmark)
        menu.addSeparator()

        menu.addAction("開發者工具 (F12)", self.open_devtools)
        menu.addSeparator()

        menu.addAction("關於 LeoBrowserSE", self.show_about)

        menu.exec(QCursor.pos())

    # ======================================================
    # 書籤管理器
    # ======================================================

    def add_bookmark(self):
        tab = self.current_tab()
        if not tab:
            return
        url = tab.view.url().toString()
        title = tab.view.title()

        bookmarks.append({"title": title, "url": url})
        save_bookmarks(bookmarks)
        QMessageBox.information(self, "完成", "書籤已加入！")

    def manage_bookmarks(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("書籤管理")
        dlg.resize(400, 400)

        layout = QVBoxLayout(dlg)
        listbox = QListWidget()
        layout.addWidget(listbox)

        for bm in bookmarks:
            listbox.addItem(f"{bm['title']} — {bm['url']}")

        dlg.exec()

    # ======================================================
    # About（B 版本）
    # ======================================================

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            (
                f"LeoBrowserSE 1.0 (Debug Build github test)\n"
                f"Build Number: 104.6.2201\n"
                "Engine: Qt WebEngine (Chromium 最新)\n"
                "Profile: LeoProfile（完全隔離）\n"
                "UI Framework: Fluent Widgets\n\n"
                "此版本為test，不代表最終產品。"
            )
        )

    # ======================================================
    # DevTools（不會崩潰的最新版）
    # ======================================================

    def open_devtools(self):
        tab = self.current_tab()
        if not tab:
            return

        dev_page = QWebEnginePage(self.profile)
        dev_window = QWebEngineView()
        dev_window.setPage(dev_page)
        tab.view.page().setDevToolsPage(dev_page)
        dev_window.resize(900, 700)
        dev_window.setWindowTitle("Developer Tools")
        dev_window.show()


# ==========================================================
# Q 退出監聽
# ==========================================================

def safe_exit(app):
    print("\n== 安全退出模式：按 Q 退出 LeoBrowserSE ==")
    while True:
        if input().strip().lower() == "q":
            print("正在退出...")
            app.quit()
            break


# ==========================================================
# 主程式
# ==========================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    w = LeoBrowser()
    w.show()

    threading.Thread(target=safe_exit, args=(app,), daemon=True).start()

    sys.exit(app.exec())

