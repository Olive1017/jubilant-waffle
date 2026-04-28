import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment



def save_to_excel(contract_data, filename, global_number):
    """保存数据到Excel，追加到现有文件"""
    # 检查文件是否存在
    if os.path.exists(filename):
        # 读取现有文件
        wb = openpyxl.load_workbook(filename)
        ws = wb.active
    else:
        # 创建新文件
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

    # 基本信息字段
    basic_info = {
        '经办时间': contract_data.get('经办时间', ''),
        '经办机构': contract_data.get('经办机构', ''),
        '经办人员': contract_data.get('经办人员', ''),
        '合同电子编号': contract_data.get('合同电子编号', ''),
        '合同名称': contract_data.get('合同名称', '')
    }

    # 审批记录
    approval_records = contract_data.get('审批记录', [])

    if approval_records:
        # 为每条审批记录创建一行数据
        for record in approval_records:
            row_data = [
                global_number,  # 使用全局序号
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

            # 设置数据行文本居中（跳过经办机构、合同名称、处理意见列）
            for idx, cell in enumerate(ws[ws.max_row], start=1):
                if idx not in [3, 6, 10]:  # C列、F列、J列不居中
                    cell.alignment = Alignment(horizontal='center', vertical='center')

            global_number += 1  # 序号递增
    else:
        # 如果没有审批记录，至少保存基本信息
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

        # 设置数据行文本居中（跳过经办机构、合同名称、处理意见列）
        for idx, cell in enumerate(ws[ws.max_row], start=1):
            if idx not in [3, 6, 10]:  # C列、F列、J列不居中
                cell.alignment = Alignment(horizontal='center', vertical='center')

        global_number += 1

    wb.save(filename)
    print(f"数据已追加到 {filename}，当前序号：{global_number - 1}")
    return global_number
