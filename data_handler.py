import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from pathlib import Path
import tempfile

# 数据文件存储路径（使用系统临时目录）
DATA_DIR = Path(tempfile.gettempdir()) / "contract_scraper"
DATA_FILE = DATA_DIR / "contract_data.json"


def _ensure_data_dir():
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def add_contract_data(contract_data):
    """追加合同数据到文件中"""
    _ensure_data_dir()

    # 读取现有数据
    existing_data = []
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)

    # 追加新数据
    existing_data.append(contract_data)

    # 写回文件
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)




def get_contract_data():
    """从文件中获取所有合同数据"""
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def export_to_excel(file_path):
    """导出文件中的数据到指定路径的Excel文件"""
    contract_data_list = get_contract_data()

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
    for contract_data in contract_data_list:
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
    return len(contract_data_list)
