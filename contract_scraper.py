import time
import asyncio
from datetime import datetime


async def close_popups(page):
    """关闭所有系统弹窗(如502错误等)"""
    try:
        # 获取所有弹窗
        popups = page.locator('.el-overlay-message-box')
        popup_count = await popups.count()

        if popup_count > 0:
            print(f"检测到 {popup_count} 个系统弹窗，正在关闭...")

            # 关闭所有弹窗
            closed_count = 0
            for i in range(popup_count):
                try:
                    close_btn = popups.nth(i).locator('.el-message-box__headerbtn').first
                    if await close_btn.count() > 0:
                        await close_btn.click()
                        await asyncio.sleep(0.3)
                        closed_count += 1
                        print(f"第 {i+1} 个弹窗已关闭")
                except Exception as e:
                    print(f"关闭第 {i+1} 个弹窗时出错: {e}")

            print(f"成功关闭 {closed_count}/{popup_count} 个弹窗")
            return closed_count > 0
    except Exception as e:
        print(f"关闭弹窗时出错: {e}")
    return False


async def scrape_approval_table(page):
    """抓取审批意见表格信息"""
    try:
        print("等待审批表格加载...")

        # 快速检测表格类型（表格框架无需等待内容加载）
        if await page.locator('.form-card__body').count() > 0 and await page.locator('.el-table__body').count() > 0:
            print("检测到第二种格式")
            # 等待序号1出现，代表内容已加载
            try:
                await page.locator('.el-table__body tbody tr:first-child td.el-table__cell').get_by_text('1').wait_for(timeout=15000)
                await asyncio.sleep(0.5)
            except:
                print("等待第二种格式序号超时，直接抓取...")

            print("开始抓取第二种格式的审批表格数据...")
            rows = page.locator('.el-table__body tbody tr')
            row_count = await rows.count()
            print(f"找到 {row_count} 行审批记录")

            if row_count == 0:
                print("警告：没有找到任何审批记录！")
                return []

            approval_data = []

            for i in range(row_count):
                row = rows.nth(i)
                cells = row.locator('td.el-table__cell')

                if await cells.count() >= 6:
                    row_data = {
                        '处理人': (await cells.nth(1).inner_text()).strip(),
                        '节点名称': '',  # 第二种格式没有节点名称
                        '所在部门': (await cells.nth(2).inner_text()).strip(),
                        '处理意见': (await cells.nth(3).inner_text()).strip(),
                        '接收时间': (await cells.nth(4).inner_text()).strip(),
                        '审批时间': (await cells.nth(5).inner_text()).strip()
                    }
                    approval_data.append(row_data)
                    print(f"  第{i + 1}条: {row_data['处理人']} - {row_data['所在部门']}")

            return approval_data
        else:
            print("检测到第一种格式")
            # 等待序号1出现，代表内容已加载
            try:
                await page.locator('.lui-table-tbody tr:first-child .lui-table-cell').get_by_text('1').wait_for(timeout=15000)
                await asyncio.sleep(0.5)
            except:
                print("等待第一种格式序号超时，直接抓取...")

            print("开始抓取审批表格数据...")
            rows = page.locator('.lui-table-tbody tr')
            row_count = await rows.count()
            print(f"找到 {row_count} 行审批记录")

            if row_count == 0:
                print("警告：没有找到任何审批记录！")
                return []

            approval_data = []

            for i in range(row_count):
                row = rows.nth(i)
                cells = row.locator('.lui-table-cell')

                if await cells.count() >= 7:
                    row_data = {
                        '处理人': (await cells.nth(1).inner_text()).strip(),
                        '节点名称': (await cells.nth(2).inner_text()).strip(),
                        '所在部门': (await cells.nth(3).inner_text()).strip(),
                        '处理意见': (await cells.nth(4).inner_text()).strip(),
                        '接收时间': (await cells.nth(5).inner_text()).strip(),
                        '审批时间': (await cells.nth(6).inner_text()).strip()
                    }
                    approval_data.append(row_data)
                    print(f"  第{i + 1}条: {row_data['处理人']} - {row_data['节点名称']}")

            return approval_data

    except Exception as e:
        print(f"抓取审批表格失败: {e}")
        return []


async def scrape_approval_table_alternative(page):
    """备用方案：抓取第二种格式的审批表格"""
    try:
        print("尝试等待第二种格式的表格加载...")
        # 等待序号列的1出现
        try:
            await page.locator('.el-table__body tbody tr:first-child td.el-table__cell').get_by_text('1').wait_for(timeout=15000)
            await asyncio.sleep(0.5)
        except:
            print("等待表格超时，尝试直接抓取...")

        print("开始抓取第二种格式的审批表格数据...")
        rows = page.locator('.el-table__body tbody tr')
        row_count = await rows.count()
        print(f"找到 {row_count} 行审批记录")

        if row_count == 0:
            print("警告：没有找到任何审批记录！")
            return []

        approval_data = []

        for i in range(row_count):
            row = rows.nth(i)
            cells = row.locator('td.el-table__cell')

            if await cells.count() >= 6:
                row_data = {
                    '处理人': (await cells.nth(1).inner_text()).strip(),
                    '节点名称': '',  # 第二种格式没有节点名称
                    '所在部门': (await cells.nth(2).inner_text()).strip(),
                    '处理意见': (await cells.nth(3).inner_text()).strip(),
                    '接收时间': (await cells.nth(4).inner_text()).strip(),
                    '审批时间': (await cells.nth(5).inner_text()).strip()
                }
                approval_data.append(row_data)
                print(f"  第{i + 1}条: {row_data['处理人']} - {row_data['所在部门']}")

        return approval_data

    except Exception as e:
        print(f"抓取第二种格式审批表格失败: {e}")
        return []


async def scrape_single_contract(page):
    """抓取单个合同的所有信息"""
    try:
        # 等待页面加载
        await page.wait_for_load_state('networkidle')

        # 点击合同起草
        print("点击合同起草...")
        await close_popups(page)  # 关闭可能存在的弹窗
        await page.get_by_text("合同起草").click()

        # 抓取基本信息
        print("抓取基本信息...")
        org_text = (await page.locator('text=经办机构').locator('xpath=following-sibling::div').first.inner_text()).strip()
        person_text = (await page.locator('text=经办人员').locator('xpath=following-sibling::div').first.inner_text()).strip()
        date_text = (await page.locator('text=经办时间').locator('xpath=following-sibling::div').first.inner_text()).strip()

        contract_code_text = (await page.locator('text=合同电子编号').locator(
            'xpath=following-sibling::span').first.inner_text()).strip()
        contract_code = contract_code_text.replace('：', '').strip()
        contract_name = await page.locator('.contract-name .ellipsis').get_attribute('title')

        print(f"合同编号: {contract_code}")
        print(f"合同名称: {contract_name}")

        # 点击合同审批并抓取表格信息
        print("\n点击合同审批...")
        await close_popups(page)  # 关闭可能存在的弹窗
        await page.locator('.tab-item span:has-text("合同审批")').click()

        # 抓取审批表格
        approval_data = await scrape_approval_table(page)

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
