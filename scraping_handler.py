import sys
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

    progress_signal = Signal(int, int)  # (当前数, 总数)
    finished = Signal(bool, str)  # (是否成功, 消息)
    need_continue = Signal()  # 需要用户继续

    def run(self):
        """执行抓取流程"""
        try:
            from contract_scraper import scrape_single_contract

            print("正在启动浏览器...")

            # 检查是否有保存的登录状态
            auth_dir = Path(tempfile.gettempdir()) / "contract_scraper"
            auth_dir.mkdir(parents=True, exist_ok=True)
            auth_file = auth_dir / "auth.json"

            with sync_playwright() as playwright:
                # 尝试依次启动 Chrome 和 Edge
                browser = None
                try:
                    browser = playwright.chromium.launch(channel="msedge", headless=False, slow_mo=1000)
                    print("使用 Edge 浏览器")
                except:
                    try:
                        browser = playwright.chromium.launch(channel="chrome", headless=False, slow_mo=1000)
                        print("使用 Chrome 浏览器")
                    except Exception as e:
                        print(f"Chrome 和 Edge 都无法启动: {e}")
                        raise

                # 如果有保存的登录状态，尝试加载
                if auth_file.exists():
                    print(f"发现已保存的登录状态，正在加载...")
                    context = browser.new_context(storage_state=str(auth_file))
                    page = context.new_page()

                    print("正在访问目标页面...")
                    page.goto("https://cmhklams.cmhk.com/lams-contract/frontend/contractManagement/workPlatform")
                    page.wait_for_load_state("networkidle")

                    # 检测是否还在登录页面
                    time.sleep(2)
                    current_url = page.url
                    print(f"当前页面: {current_url}")

                    # 如果URL包含登录相关关键词，说明需要重新登录
                    if "login" in current_url.lower() or "sso" in current_url.lower():
                        print("登录状态已过期，需要重新登录")
                        need_login = True
                    else:
                        # 尝试检查页面元素，判断是否已登录
                        try:
                            # 检查是否有登录框或其他登录相关元素
                            login_elements = page.locator('input[type="password"], .login, .sign-in').count()
                            if login_elements > 0:
                                need_login = True
                                print("检测到需要重新登录")
                            else:
                                need_login = False
                                print("登录状态有效，已自动登录")
                        except:
                            need_login = True
                            print("无法验证登录状态，请手动确认")
                else:
                    print("未找到已保存的登录状态")
                    context = browser.new_context()
                    page = context.new_page()
                    need_login = True

                    print("正在访问目标页面...")
                    page.goto("https://cmhklams.cmhk.com/lams-contract/frontend/contractManagement/workPlatform")
                    page.wait_for_load_state("networkidle")

                print("\n========== 请手动完成操作 ==========")
                print("请在登陆后按顺序完成以下操作：")
                print("1. 点击【合同台账查询】菜单")
                print("2. 点击【高级查询】按钮")
                print("3. 设置筛选条件")
                print("4. 点击【查询】按钮显示结果")
                print("\n全部完成后请点击【继续】按钮")
                print("=====================================\n")

                self.should_continue = False  # 重置标志
                self.need_continue.emit()  # 发送信号，让UI显示"继续"按钮

                # 等待用户完成所有操作后点击继续
                while not self.should_continue:
                    time.sleep(0.1)


                print("操作确认完成，正在保存登录状态...")

                # 保存登录状态
                context.storage_state(path=str(auth_file))
                print(f"登录状态已保存到 {auth_file}")

                print("开始抓取流程...")
                page.wait_for_load_state("networkidle")


                # 自动设置每页显示50条
                try:
                    page.locator('.el-select__wrapper:has-text("10条/页")').click()
                    page.get_by_text("50条/页").click()
                    time.sleep(2)

                    # 等待第11个序号出现，代表表格数据加载成功
                    try:
                        page.locator('td.el-table-fixed-column--left div').get_by_text('11').wait_for(timeout=15000)
                        print("50条/页设置成功，表格已加载")
                    except:
                        print("等待表格加载超时，但继续执行...")
                except Exception as e:
                    print(f"设置每页显示数量失败（不影响抓取）: {str(e)}")

                print("开始抓取...")
                print("\n===== 开始批量抓取合同信息 =====")

                page_number = 1
                total_contracts = 0

                while True:
                    print(f"\n===== 当前第 {page_number} 页 =====")

                    # 获取当前页面的所有合同链接
                    contract_links = page.locator("td.el-table_2_column_6.el-table__cell a.dao-link")
                    contract_count = contract_links.count()

                    print(f"当前页面有 {contract_count} 个合同")

                    if contract_count == 0:
                        print("当前页面没有合同，抓取结束")
                        break

                    # 遍历当前页面的所有合同
                    for i in range(contract_count):
                        print(f"\n----- 开始抓取第 {i + 1}/{contract_count} 个合同 -----")

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
                        try:
                            page.wait_for_load_state('networkidle',timeout=2000)
                        except:
                            print("等待超时，继续执行...")

                        # 重新获取合同链接
                        contract_links = page.locator("td.el-table_2_column_6.el-table__cell a.dao-link")

                        print(f"已抓取 {total_contracts} 个合同")

                    # 当前页面的所有合同抓取完成，判断是否需要翻页
                    print(f"\n第 {page_number} 页的 {contract_count} 个合同已全部抓取完成")

                    if contract_count < 50:
                        print(f"当前页面只有 {contract_count} 个合同，已到最后一页")
                        break
                    else:
                        # 尝试翻页
                        print(f"当前页面有 {contract_count} 个合同，尝试翻页...")
                        try:
                            page.locator('.btn-next').click()
                            time.sleep(2)  # 短暂等待点击生效

                            # 等待表格数据出现
                            try:
                                page.locator("td.el-table_2_column_6.el-table__cell a.dao-link").first.wait_for(timeout=10000)
                                print("翻页后表格已加载")
                            except:
                                print("等待表格超时，尝试继续...")

                            # 检查翻页是否成功
                            new_contract_links = page.locator("td.el-table_2_column_6.el-table__cell a.dao-link")
                            new_count = new_contract_links.count()

                            if new_count == 0:
                                print("翻页后没有合同，已到最后一页")
                                break
                            else:
                                print(f"翻页成功，第 {page_number + 1} 页有 {new_count} 个合同")
                                page_number += 1

                        except Exception as e:
                            print(f"翻页失败: {e}，已到最后一页")
                            break


                print(f"\n===== 抓取完成 =====")
                print(f"总共抓取了 {page_number} 页")
                print(f"总共抓取了 {total_contracts} 个合同")

                self.finished.emit(True, "抓取完成！")

                context.close()
                browser.close()

        except Exception as e:
            print(f"抓取失败: {str(e)}")
            self.finished.emit(False, f"抓取失败: {str(e)}")
