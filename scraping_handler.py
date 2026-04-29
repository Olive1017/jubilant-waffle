import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QThread, Signal
from playwright.sync_api import sync_playwright

from contract_scraper import close_popups


class ScrapingThread(QThread):
    """自动化抓取线程 - 处理合同数据抓取"""

    log_signal = Signal(str)  # 日志消息
    progress_signal = Signal(int, int)  # (当前数, 总数)
    finished = Signal(bool, str)  # (是否成功, 消息)
    need_continue = Signal()  # 需要用户继续

    def __init__(self):
        super().__init__()
        self.is_running = True

    def stop(self):
        """停止抓取"""
        self.is_running = False

    def run(self):
        """执行抓取流程"""
        try:
            from contract_scraper import scrape_single_contract


            self.log_signal.emit("正在启动浏览器...")

            # 检查是否有保存的登录状态
            auth_dir = Path(tempfile.gettempdir()) / "contract_scraper"
            auth_dir.mkdir(parents=True, exist_ok=True)
            auth_file = auth_dir / "auth.json"

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="msedge", headless=False, slow_mo=1000)

                # 如果有保存的登录状态，尝试加载
                if auth_file.exists():
                    self.log_signal.emit(f"发现已保存的登录状态，正在加载...")
                    context = browser.new_context(storage_state=str(auth_file))
                    page = context.new_page()

                    self.log_signal.emit("正在访问目标页面...")
                    page.goto("https://cmhklams.cmhk.com/lams-contract/frontend/contractManagement/workPlatform")
                    page.wait_for_load_state("networkidle")

                    # 检测是否还在登录页面
                    time.sleep(2)
                    current_url = page.url
                    self.log_signal.emit(f"当前页面: {current_url}")

                    # 如果URL包含登录相关关键词，说明需要重新登录
                    if "login" in current_url.lower() or "sso" in current_url.lower():
                        self.log_signal.emit("登录状态已过期，需要重新登录")
                        need_login = True
                    else:
                        # 尝试检查页面元素，判断是否已登录
                        try:
                            # 检查是否有登录框或其他登录相关元素
                            login_elements = page.locator('input[type="password"], .login, .sign-in').count()
                            if login_elements > 0:
                                need_login = True
                                self.log_signal.emit("检测到需要重新登录")
                            else:
                                need_login = False
                                self.log_signal.emit("登录状态有效，已自动登录")
                        except:
                            need_login = True
                            self.log_signal.emit("无法验证登录状态，请手动确认")
                else:
                    self.log_signal.emit("未找到已保存的登录状态")
                    context = browser.new_context()
                    page = context.new_page()
                    need_login = True

                    self.log_signal.emit("正在访问目标页面...")
                    page.goto("https://cmhklams.cmhk.com/lams-contract/frontend/contractManagement/workPlatform")
                    page.wait_for_load_state("networkidle")

                self.log_signal.emit("\n========== 请手动完成操作 ==========")
                self.log_signal.emit("请在登陆后按顺序完成以下操作：")
                self.log_signal.emit("1. 点击【合同台账查询】菜单")
                self.log_signal.emit("2. 点击【高级查询】按钮")
                self.log_signal.emit("3. 设置筛选条件")
                self.log_signal.emit("4. 点击【查询】按钮显示结果")
                self.log_signal.emit("\n全部完成后请点击【继续】按钮")
                self.log_signal.emit("=====================================\n")

                self.should_continue = False  # 重置标志
                self.need_continue.emit()  # 发送信号，让UI显示"继续"按钮

                # 等待用户完成所有操作后点击继续
                while not self.should_continue:
                    if not self.is_running:
                        self.log_signal.emit("用户停止了抓取")
                        context.close()
                        browser.close()
                        return
                    time.sleep(0.1)


                self.log_signal.emit("操作确认完成，正在保存登录状态...")
                from data_handler import clear_contract_data
                clear_contract_data()

                # 保存登录状态
                context.storage_state(path=str(auth_file))
                self.log_signal.emit(f"登录状态已保存到 {auth_file}")

                self.log_signal.emit("开始抓取流程...")
                page.wait_for_load_state("networkidle")

                # 自动设置每页显示50条
                try:
                    page.locator('.el-select__wrapper:has-text("10条/页")').click()
                    page.get_by_text("50条/页").click()
                    time.sleep(10)
                except Exception as e:
                    self.log_signal.emit(f"设置每页显示数量失败（不影响抓取）: {str(e)}")

                self.log_signal.emit("开始抓取...")
                self.log_signal.emit("\n===== 开始批量抓取合同信息 =====")

                page_number = 1
                total_contracts = 0

                while self.is_running:
                    self.log_signal.emit(f"\n===== 当前第 {page_number} 页 =====")

                    # 获取当前页面的所有合同链接
                    contract_links = page.locator("td.el-table_2_column_6.el-table__cell a.dao-link")
                    contract_count = contract_links.count()

                    self.log_signal.emit(f"当前页面有 {contract_count} 个合同")

                    if contract_count == 0:
                        self.log_signal.emit("当前页面没有合同，抓取结束")
                        break

                    # 遍历当前页面的所有合同
                    for i in range(contract_count):
                        if not self.is_running:
                            self.log_signal.emit("用户停止了抓取")
                            break

                        self.log_signal.emit(f"\n----- 开始抓取第 {i + 1}/{contract_count} 个合同 -----")

                        # 点击合同链接
                        contract_links.nth(i).click()

                        # 抓取合同信息
                        approval_data = scrape_single_contract(page)
                        total_contracts += 1

                        # 发送进度信号
                        self.progress_signal.emit(total_contracts, 0)

                        # 关闭合同详情标签页
                        close_popups(page)
                        tab_with_close = page.locator('.tab-item').filter(has_text="合同详情").locator('.el-icon svg')
                        tab_with_close.click()

                        # 等待返回列表页面
                        time.sleep(1)
                        page.wait_for_load_state('networkidle')

                        # 重新获取合同链接
                        contract_links = page.locator("td.el-table_2_column_6.el-table__cell a.dao-link")

                        self.log_signal.emit(f"已抓取 {total_contracts} 个合同")

                    if not self.is_running:
                        break

                    # 当前页面的所有合同抓取完成，判断是否需要翻页
                    self.log_signal.emit(f"\\n第 {page_number} 页的 {contract_count} 个合同已全部抓取完成")

                    if contract_count < 50:
                        self.log_signal.emit(f"当前页面只有 {contract_count} 个合同，已到最后一页")
                        break
                    else:
                        # 尝试翻页
                        self.log_signal.emit(f"当前页面有 {contract_count} 个合同，尝试翻页...")
                        try:
                            page.locator('.btn-next').click()
                            time.sleep(8)
                            page.wait_for_load_state('networkidle')

                            # 检查翻页是否成功
                            new_contract_links = page.locator("td.el-table_2_column_6.el-table__cell a.dao-link")
                            new_count = new_contract_links.count()

                            if new_count == 0:
                                self.log_signal.emit("翻页后没有合同，已到最后一页")
                                break
                            else:
                                self.log_signal.emit(f"翻页成功，第 {page_number + 1} 页有 {new_count} 个合同")
                                page_number += 1

                        except Exception as e:
                            self.log_signal.emit(f"翻页失败: {e}，已到最后一页")
                            break


                self.log_signal.emit(f"\n===== 抓取完成 =====")
                self.log_signal.emit(f"总共抓取了 {page_number} 页")
                self.log_signal.emit(f"总共抓取了 {total_contracts} 个合同")

                self.finished.emit(True, "抓取完成！")

                context.close()
                browser.close()

        except Exception as e:
            self.log_signal.emit(f"抓取失败: {str(e)}")
            self.finished.emit(False, f"抓取失败: {str(e)}")
