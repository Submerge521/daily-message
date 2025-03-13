"""
Excel与MySQL智能表名比对系统
核心功能：
1. 动态解析数据库表名前缀（如 tb_czyth_gzc_）
2. 支持带前缀的模糊匹配（ACCEPTANCE → tb_czyth_gzc_acceptance）
3. 自适应表名清洗规则
"""

import re
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill
from sqlalchemy import create_engine, exc, text
from typing import List, Dict
from collections import Counter


class EnhancedTableComparator:
    def __init__(self, excel_path: str, db_config: Dict[str, str],
                 prefix_pattern: str = r"^(.+?_)\w+$"):
        """
        初始化配置
        :param prefix_pattern: 表名前缀解析正则，默认捕获类似 tb_czyth_gzc_ 的结构
        """
        self.excel_path = excel_path
        self.db_config = db_config
        self.prefix_pattern = prefix_pattern
        self.dynamic_prefix = None
        self.green_fill = PatternFill(
            start_color='92D050',
            fill_type='solid'
        )

    def _extract_prefix(self, table_names: List[str]) -> str:
        """动态提取高频表名前缀"""
        prefix_counts = Counter()
        for name in table_names:
            match = re.match(self.prefix_pattern, name)
            if match and len(match.groups()) > 0:
                prefix = match.group(1)
                prefix_counts[prefix] += 1

        if not prefix_counts:
            raise ValueError("未检测到有效表名前缀模式")

        # 取出现频率最高的前3个前缀做二次验证
        top_prefixes = prefix_counts.most_common(3)
        for prefix, count in top_prefixes:
            if count >= len(table_names) * 0.3:  # 至少覆盖30%的表
                self.dynamic_prefix = prefix
                return prefix

        raise ValueError("未找到稳定表名前缀")

    def _transform_name(self, excel_name: str) -> str:
        """执行表名转换（核心匹配逻辑）"""
        # 清洗规则：去除非字母数字字符 → 小写化 → 拼接前缀
        clean_name = re.sub(r"[^a-zA-Z0-9]", "", excel_name).lower()
        return f"{self.dynamic_prefix}{clean_name}"

    def _get_excel_names(self) -> List[str]:
        """读取Excel目标列数据"""
        try:
            df = pd.read_excel(self.excel_path, nrows=1)
            target_col = next(
                col for col in df.columns
                if "源系统表英文名称(*)" in str(col)
            )
            full_df = pd.read_excel(self.excel_path, usecols=[target_col])
            return full_df[target_col].dropna().astype(str).unique().tolist()
        except Exception as e:
            raise RuntimeError(f"Excel读取失败: {e}")

    def _get_mysql_tables(self) -> List[str]:
        """获取MySQL表名（含动态前缀解析）"""
        try:
            engine = create_engine(
                f"mysql+pymysql://{self.db_config['user']}:{self.db_config['password']}"
                f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
                "?charset=utf8mb4"
            )
            with engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables  "
                    "WHERE table_schema = DATABASE()"
                ))
                tables = [row[0] for row in result]
                self._extract_prefix(tables)  # 动态解析前缀
                return tables
        except exc.SQLAlchemyError as e:
            raise RuntimeError(f"数据库连接失败: {e}")

    def _highlight_cells(self, matched_names: List[str]):
        """执行单元格标注"""
        wb = openpyxl.load_workbook(self.excel_path)
        ws = wb.active

        # 定位目标列
        target_col = next(
            col for col in ws[1]
            if "源系统表英文名称(*)" in str(col.value)
        ).column_letter

        updated = 0
        for row in ws.iter_rows(min_row=2):
            cell = row[ord(target_col.lower()) - 97]  # 列字母转索引
            if cell.value in matched_names:
                cell.fill = self.green_fill
                updated += 1

        output_path = self.excel_path.replace('.xlsx', '_标注结果.xlsx')
        wb.save(output_path)
        return updated, output_path

    def execute(self):
        """主执行流程"""
        print("▶ 开始智能匹配流程...")

        # 分阶段执行
        excel_names = self._get_excel_names()
        mysql_tables = self._get_mysql_tables()
        print(f"√ 检测到动态前缀：{self.dynamic_prefix}")

        # 构建匹配映射
        match_map = {
            orig: self._transform_name(orig)
            for orig in excel_names
        }
        matched = [
            orig for orig, transformed in match_map.items()
            if transformed in mysql_tables
        ]

        # 执行标注
        count, path = self._highlight_cells(matched)
        print(f"★ 成功标记 {count} 个匹配表")
        print(f"↗ 结果文件路径：{path}")


# 使用示例
if __name__ == "__main__":
    # 配置区=======================================================
    DB_CONFIG = {
        "host": "10.10.10.215",
        "user": "etladmin",
        "password": "etladmin123",
        "database": "HG_SourceDB",
        "port": 3306
    }
    EXCEL_PATH = "./1.xlsx"
    # =============================================================

    try:
        tool = EnhancedTableComparator(
            excel_path=EXCEL_PATH,
            db_config=DB_CONFIG,
            prefix_pattern=r"^(tb_czyth_gzc_)\w+"  # 可自定义正则
        )
        tool.execute()
    except Exception as e:
        print(f"! 系统异常: {str(e)}")
        print("! 建议检查：1.正则表达式 2.表名格式 3.权限配置")