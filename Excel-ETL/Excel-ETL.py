import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill
from sqlalchemy import create_engine, exc
from typing import List, Dict


class TableComparatorPro:
    def __init__(self, excel_path: str, db_config: Dict[str, str]):
        """
        初始化比对工具
        :param excel_path: Excel文件路径
        :param db_config: 数据库配置字典，需包含host/user/password/database/port
        """
        self.excel_path = excel_path
        self.db_config = db_config
        self.target_column = None
        self.green_fill = PatternFill(
            start_color='92D050',  # 更柔和的绿色
            end_color='92D050',
            fill_type='solid'
        )

    def _find_target_column(self, df: pd.DataFrame) -> str:
        """智能定位目标列(支持模糊匹配)"""
        for col in df.columns:
            if "源系统表英文名称" in str(col) and "(*)" in str(col):
                return col
        raise ValueError("未找到包含'源系统表英文名称(*)'的列头")

    def get_excel_tables(self) -> List[str]:
        """获取Excel目标列去重表名清单"""
        try:
            # 双重读取确保列定位准确
            header_df = pd.read_excel(self.excel_path, nrows=2)
            self.target_column = self._find_target_column(header_df)

            full_df = pd.read_excel(self.excel_path, usecols=[self.target_column])
            return full_df[self.target_column].astype(str).str.strip().dropna().unique().tolist()
        except Exception as e:
            raise RuntimeError(f"Excel文件读取失败: {str(e)}")

    def get_mysql_tables(self) -> List[str]:
        try:
            engine = create_engine(
                f"mysql+pymysql://{self.db_config['user']}:{self.db_config['password']}"
                f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
                "?charset=utf8mb4"
            )
            with engine.connect() as conn:
                # 使用text()包装并简化查询
                from sqlalchemy import text
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables  "
                    "WHERE table_schema = :db"
                ), {'db': self.db_config['database']})
                return [row[0] for row in result]
        except exc.SQLAlchemyError as e:
            raise RuntimeError(f"数据库连接失败: {str(e)}")

    def _locate_excel_column(self, ws) -> int:
        """精确定位目标列索引"""
        for cell in ws[1]:  # 首行为列头
            if cell.value == self.target_column:
                return cell.column
        raise ValueError("目标列在Excel中定位失败")

    def highlight_matches(self, matches: List[str]):
        """执行高亮标注"""
        try:
            # 保留原文件并创建副本
            marked_path = self.excel_path.replace('.xlsx', '_标注结果.xlsx')

            wb = openpyxl.load_workbook(self.excel_path)
            ws = wb.active

            col_idx = self._locate_excel_column(ws)

            updated_count = 0
            for row in ws.iter_rows(min_row=2):  # 跳过标题行
                cell = row[col_idx - 1]
                if cell.value in matches:
                    cell.fill = self.green_fill
                    updated_count += 1

            wb.save(marked_path)
            return updated_count, marked_path
        except Exception as e:
            raise RuntimeError(f"Excel标注失败: {str(e)}")

    def execute(self):
        """执行完整流程"""
        print("▶ 开始处理...")

        # 分步骤执行
        excel_tables = self.get_excel_tables()
        print(f"√ 从Excel读取到 {len(excel_tables)} 个待校验表名")

        mysql_tables = self.get_mysql_tables()
        print(f"√ 从MySQL获取到 {len(mysql_tables)} 个数据库表")

        matches = list(set(excel_tables) & set(mysql_tables))
        print(f"！发现 {len(matches)} 个匹配表名")

        updated_count, output_path = self.highlight_matches(matches)
        print(f"★ 标注完成，共标记 {updated_count} 个单元格")
        print(f"↗ 结果文件已保存至：{output_path}")


if __name__ == "__main__":
    # 配置区=======================================================
    DB_CONFIG = {
        "host": "10.10.10.215",
        "user": "etladmin",
        "password": "etladmin123",
        "database": "HG_SourceDB",
        "port": 3306
    }

    EXCEL_FILE = "./1.xlsx"
    # =============================================================

    try:
        tool = TableComparatorPro(EXCEL_FILE, DB_CONFIG)
        tool.execute()
    except Exception as e:
        print(f"! 处理异常: {str(e)}")
        print("! 请检查：1.Excel路径 2.数据库配置 3.网络连接")