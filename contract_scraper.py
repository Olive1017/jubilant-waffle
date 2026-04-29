import time
from datetime import datetime


def close_popups(page):
    """关闭所有系统弹窗(如502错误等)"""
    try:
        # 尝试多种方式定位关闭按钮
        popup = page.locator('.el-overlay-message-box')
        if popup.count() > 0:
            print("检测到系统弹窗，正在关闭...")
            # 尝试方式1
            close_btn = page.locator('.el-message-box__headerbtn')
            if close_btn.count() > 0:
                close_btn.click()
                time.sleep(0.5)
                print("弹窗已关闭")
                return True
            # 尝试方式2
            close_btn = page.locator('button[aria-label="关闭此对话框"]')
            if close_btn.count() > 0:
                close_btn.click()
                time.sleep(0.5)
                print("弹窗已关闭")
                return True
            # 尝试方式3
            close_icon = page.locator('.el-message-box__close')
            if close_icon.count() > 0:
                close_icon.click()
                time.sleep(0.5)
                print("弹窗已关闭")
                return True
    except Exception as e:
        print(f"关闭弹窗时出错: {e}")
    return False


def scrape_approval_table(page):
    """抓取审批意见表格信息"""
    try:
        print("等待审批表格加载...")
        # 尝试等待第一种格式的容器
        try:
            page.wait_for_selector('.div-summary-of-opinions-main', timeout=15000)
            time.sleep(1)
        except:
            print("未找到第一种格式容器，可能是第二种格式，继续尝试...")

        print("开始抓取审批表格数据...")
        rows = page.locator('.lui-table-tbody tr')
        row_count = rows.count()
        print(f"找到 {row_count} 行审批记录")

        if row_count == 0:
            print("第一种格式未找到，尝试第二种格式...")
            return scrape_approval_table_alternative(page)

        approval_data = []

        for i in range(row_count):
            row = rows.nth(i)
            cells = row.locator('.lui-table-cell')

            if cells.count() >= 7:
                row_data = {
                    '处理人': cells.nth(1).inner_text().strip(),
                    '节点名称': cells.nth(2).inner_text().strip(),
                    '所在部门': cells.nth(3).inner_text().strip(),
                    '处理意见': cells.nth(4).inner_text().strip(),
                    '接收时间': cells.nth(5).inner_text().strip(),
                    '审批时间': cells.nth(6).inner_text().strip()
                }
                approval_data.append(row_data)
                print(f"  第{i + 1}条: {row_data['处理人']} - {row_data['节点名称']}")

        return approval_data

    except Exception as e:
        print(f"抓取审批表格失败: {e}")
        return []


def scrape_approval_table_alternative(page):
    """备用方案：抓取第二种格式的审批表格"""
    try:
        print("尝试等待第二种格式的表格加载...")
        # 等待序号列的1出现
        try:
            page.locator('.el-table__body tbody tr:first-child td:first-child').get_by_text('1').wait_for(timeout=15000)
            time.sleep(0.5)
        except:
            print("等待表格超时，尝试直接抓取...")

        print("开始抓取第二种格式的审批表格数据...")
        rows = page.locator('.el-table__body tbody .el-table__row')
        row_count = rows.count()
        print(f"找到 {row_count} 行审批记录")

        if row_count == 0:
            print("警告：没有找到任何审批记录！")
            return []

        approval_data = []

        for i in range(row_count):
            row = rows.nth(i)
            cells = row.locator('.el-table__cell')

            if cells.count() >= 6:
                row_data = {
                    '处理人': cells.nth(1).inner_text().strip(),
                    '节点名称': '',  # 第二种格式没有节点名称
                    '所在部门': cells.nth(2).inner_text().strip(),
                    '处理意见': cells.nth(3).inner_text().strip(),
                    '接收时间': cells.nth(4).inner_text().strip(),
                    '审批时间': cells.nth(5).inner_text().strip()
                }
                approval_data.append(row_data)
                print(f"  第{i + 1}条: {row_data['处理人']} - {row_data['所在部门']}")

        return approval_data

    except Exception as e:
        print(f"抓取第二种格式审批表格失败: {e}")
        return []


def scrape_single_contract(page):
    """抓取单个合同的所有信息"""
    try:
        # 等待页面加载
        page.wait_for_load_state('networkidle')

        # 点击合同起草
        print("点击合同起草...")
        close_popups(page)  # 关闭可能存在的弹窗
        page.get_by_text("合同起草").click()

        # 抓取基本信息
        print("抓取基本信息...")
        org_text = page.locator('text=经办机构').locator('xpath=following-sibling::div').first.inner_text()
        person_text = page.locator('text=经办人员').locator('xpath=following-sibling::div').first.inner_text()
        date_text = page.locator('text=经办时间').locator('xpath=following-sibling::div').first.inner_text()

        contract_code_text = page.locator('text=合同电子编号').locator(
            'xpath=following-sibling::span').first.inner_text()
        contract_code = contract_code_text.replace('：', '').strip()
        contract_name = page.locator('.contract-name .ellipsis').get_attribute('title')

        print(f"合同编号: {contract_code}")
        print(f"合同名称: {contract_name}")

        # 点击合同审批并抓取表格信息
        print("\n点击合同审批...")
        #page.get_by_text("合同审批").click()
        close_popups(page)  # 关闭可能存在的弹窗
        page.locator('.tab-item span:has-text("合同审批")').click()

        # 抓取审批表格
        approval_data = scrape_approval_table(page)

        # 整合所有数据
        contract_data = {
            '抓取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '经办机构': org_text,
            '经办人员': person_text,
            '经办时间': date_text,
            '合同电子编号': contract_code,
            '合同名称': contract_name,
            '审批记录': approval_data
        }

        # 保存到内存
        from data_handler import add_contract_data
        add_contract_data(contract_data)

        print(f"合同 {contract_code} 抓取完成！")

        return approval_data

    except Exception as e:
        print(f"抓取合同信息时出错: {e}")
        return []

