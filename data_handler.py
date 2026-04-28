import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment


# 全局数据存储（内存中）
_global_contract_data = []


def add_contract_data(contract_data):
    """添加合同数据到内存中"""
    global _global_contract_data
    _global_contract_data.append(contract_data)


def clear_contract_data():
    """清空内存中的合同数据"""
    global _global_contract_data
    _global_contract_data = []


def get_contract_data():
    """获取内存中的所有合同数据"""
    global _global_contract_data
    return _global_contract_data


def export_to_excel(file_path):
    """导出内存中的数据到指定路径的Excel文件"""
    global _global_contract_data

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "合同信息"

    # 添加表头
    headers = [
        '序号', '经办时间', '经办机构', '经办人员',
        '合同电子编号', '合同名称', '处理人', '节点名称',
        '所在部门', '处理意见', '接收时间', '审批时间'
    ]
    ws.append(headers)

    # 设置表头样式（加粗 + 灰色背景）
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # 调整列宽
    ws.column_dimensions['A'].width = 6
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 32
    ws.column_dimensions['F'].width = 40
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 20
    ws.column_dimensions['I'].width = 20
    ws.column_dimensions['J'].width = 60
    ws.column_dimensions['K'].width = 20
    ws.column_dimensions['L'].width = 20

    global_number = 1

    # 遍历所有合同数据
    for contract_data in _global_contract_data:
        basic_info = {
            '经办时间': contract_data.get('经办时间', ''),
            '经办机构': contract_data.get('经办机构', ''),
            '经办人员': contract_data.get('经办人员', ''),
            '合同电子编号': contract_data.get('合同电子编号', ''),
            '合同名称': contract_data.get('合同名称', '')
        }

        approval_records = contract_data.get('审批记录', [])

        if approval_records:
            for record in approval_records:
                row_data = [
                    global_number,
                    basic_info['经办时间'],
                    basic_info['经办机构'],
                    basic_info['经办人员'],
                    basic_info['合同电子编号'],
                    basic_info['合同名称'],
                    record.get('处理人', ''),
                    record.get('节点名称', ''),
                    record.get('所在部门', ''),
                    record.get('处理意见', ''),
                    record.get('接收时间', ''),
                    record.get('审批时间', '')
                ]
                ws.append(row_data)

                for idx, cell in enumerate(ws[ws.max_row], start=1):
                    if idx not in [3, 6, 10]:
                        cell.alignment = Alignment(horizontal='center', vertical='center')

                global_number += 1
        else:
            row_data = [
                global_number,
                basic_info['经办时间'],
                basic_info['经办机构'],
                basic_info['经办人员'],
                basic_info['合同电子编号'],
                basic_info['合同名称'],
                '', '', '', '', '', ''
            ]
            ws.append(row_data)

            for idx, cell in enumerate(ws[ws.max_row], start=1):
                if idx not in [3, 6, 10]:
                    cell.alignment = Alignment(horizontal='center', vertical='center')

            global_number += 1

    wb.save(file_path)
    return len(_global_contract_data)
