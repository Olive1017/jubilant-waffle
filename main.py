import json
import time
from playwright.sync_api import Playwright, sync_playwright
from datetime import datetime
from contract_scraper import scrape_single_contract
from data_handler import save_to_excel

# 全局变量：用于记录序号
global_row_number = 1


def run(playwright: Playwright) -> None:
    global global_row_number

    browser = playwright.chromium.launch(channel="msedge", headless=False, slow_mo=1000)
    context = browser.new_context(storage_state="auth.json")
    page = context.new_page()

    print("使用auth.json登录中...")
    page.goto("https://cmhklams.cmhk.com/lams-contract/frontend/contractManagement/workPlatform")
    page.wait_for_load_state("networkidle")
    page.get_by_role("menuitem", name="合同台账查询").click()
    page.locator('.el-select__wrapper:has-text("10条/页")').click()
    page.get_by_text("20条/页").click()
    time.sleep(3)
    page.get_by_role("button", name="高级查询").click()
    input("按Enter键继续抓取所有合同...")

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
            global_row_number, approval_data = scrape_single_contract(page, global_row_number)
            total_contracts += 1

            # 关闭合同详情标签页
            tab_with_close = page.locator('.tab-item').filter(has_text="合同详情").locator('.el-icon svg')
            tab_with_close.click()

            # 等待返回列表页面
            time.sleep(1)
            page.wait_for_load_state('networkidle')

            # 重新获取合同链接（因为页面可能刷新）
            contract_links = page.locator("td.el-table_2_column_6.el-table__cell a.dao-link")

            print(f"已抓取 {total_contracts} 个合同")

        # 当前页面的所有合同抓取完成，尝试翻页
        print(f"\n第 {page_number} 页的 {contract_count} 个合同已全部抓取完成")

        # 点击下一页
        page.locator('.btn-next').click()
        print("翻页成功")
        # 等待页面加载
        time.sleep(8)
        page.wait_for_load_state('networkidle')

        page_number += 1

    print(f"\n===== 抓取完成 =====")
    print(f"总共抓取了 {page_number} 页")
    print(f"总共抓取了 {total_contracts} 个合同")
    print(f"总共保存了 {global_row_number - 1} 条记录")
    print(f"数据已保存到 contract_data.xlsx")

    # 同时保存到JSON作为备份
    with open('batch_contract_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            '抓取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '总页数': page_number,
            '总合同数': total_contracts,
            '总记录数': global_row_number - 1
        }, f, ensure_ascii=False, indent=2)
    print("统计数据已备份到 batch_contract_data.json")

    input("\n按Enter键继续关闭浏览器...")

    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
