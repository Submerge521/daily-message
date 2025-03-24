import re
import pymysql
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple


class OptimizedTableDiffAnalyzer:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        self.prefix = "tb_xg_xggl_"
        self.report_time = datetime(2025, 3, 13, 15, 54)  # 固定报告时间为当前时刻

    def _extract_comment_en(self, comment: str) -> str:
        """增强型注释处理：去除ST_前缀和中文描述，标准化格式"""
        if not isinstance(comment, str):
            return ""

        # 提取并清理英文部分
        en_part = comment.split('--')[0].strip()

        # 去除ST_前缀（兼容大小写和带空格情况）
        if re.match(r'^\s*ST_', en_part, re.IGNORECASE):
            en_part = re.sub(r'^\s*ST_', '', en_part, flags=re.IGNORECASE)

        # 统一格式处理
        return (
            en_part.replace('  ', '_')  # 空格转下划线
            .lower()  # 全小写
            .replace('__', '_')  # 处理双下划线
            .strip('_')  # 去除首尾下划线
        )

    def fetch_tables(self) -> List[Dict]:
        """安全获取目标数据表（增加连接检测）"""
        try:
            self.conn.ping(reconnect=True)  # 检测连接有效性
            with self.conn.cursor() as cursor:
                sql = """
                    SELECT TABLE_NAME, TABLE_COMMENT 
                    FROM information_schema.TABLES 
                    WHERE TABLE_NAME LIKE %s 
                    AND TABLE_SCHEMA = %s 
                """
                cursor.execute(sql, (f"{self.prefix}%", self.conn.db))
                return cursor.fetchall()
        except pymysql.Error as e:
            print(f"数据库操作失败: {str(e)}")
            return []

    def analyze_differences(self) -> Tuple[int, List[Dict]]:
        """精准差异分析逻辑"""
        diff_details = []

        for table in self.fetch_tables():
            raw_name = table['TABLE_NAME']
            # 处理表名（精确前缀截取）
            short_name = (
                raw_name[len(self.prefix):].lower()
                if raw_name.startswith(self.prefix)
                else raw_name.lower()
            )

            # 处理注释（调用标准化方法）
            comment_en = self._extract_comment_en(table.get('TABLE_COMMENT', ''))

            # 有效性检查
            if not short_name or not comment_en:
                continue

                # 智能对比
            if short_name != comment_en:
                diff_details.append({
                    "原始表名": raw_name,
                    "处理后表名": short_name,
                    "注释英文名": comment_en,
                    "差异类型": self._classify_diff(short_name, comment_en)
                })

        return len(diff_details), diff_details

    def _classify_diff(self, name1: str, name2: str) -> str:
        """差异类型智能判断"""
        clean_name1 = name1.replace('_', '')
        clean_name2 = name2.replace('_', '')

        if clean_name1 == clean_name2:
            return "命名风格差异" if (len(name1) != len(name2)) else "分隔符差异"
        elif clean_name1.startswith(clean_name2) or clean_name2.startswith(clean_name1):
            return "缩写差异"
        return "内容差异"

    def generate_report(self, count: int, details: List[Dict]):
        """生成双模式报告"""
        # 控制台输出
        print(f"\n🔍 [{self.prefix}]  表名注释一致性审计报告")
        print(f"📅 报告时间：{self.report_time.strftime('%Y-%m-%d  %H:%M:%S')}")
        print("▔" * 65)
        print(f"▶ 检测到差异表数量：{count}\n")

        if count > 0:
            print("📋 典型差异案例（抽样显示）：")
            for idx, item in enumerate(details[:10], 1):
                print(f"{idx:0>2}. {item['原始表名']}")
                print(f"   ├─ 表名解析：{item['处理后表名']}")
                print(f"   ├─ 注释解析：{item['注释英文名']}")
                print(f"   └─ 差异归类：{item['差异类型']}\n")

        # Excel导出
        self._export_excel(details)

    def _export_excel(self, data: List[Dict]):
        """专业Excel报告生成"""
        try:
            df = pd.DataFrame(data)
            # 添加辅助分析列
            df.insert(0, "数据源", "HG_SourceDB")
            df['匹配状态'] = df.apply(lambda x: "异常" if x['处理后表名'] != x['注释英文名'] else "正常", axis=1)

            # 生成带时间戳的文件名
            filename = f"Table_Consistency_Report_{self.report_time.strftime('%Y%m%d_%H%M')}.xlsx"

            # 使用OpenPyXL引擎导出
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(
                    writer,
                    index=False,
                    sheet_name='审计结果',
                    header=[  # 自定义中文表头
                        '数据源',
                        '原始表名',
                        '标准化表名',
                        '注释英文名',
                        '差异类型',
                        '匹配状态'
                    ]
                )

                # 获取工作表进行样式优化
                ws = writer.sheets[' 审计结果']
                # 设置专业列宽
                column_widths = {
                    'A': 12,  # 数据源
                    'B': 38,  # 原始表名
                    'C': 24,  # 标准化表名
                    'D': 24,  # 注释英文名
                    'E': 18,  # 差异类型
                    'F': 10  # 匹配状态
                }
                for col, width in column_widths.items():
                    ws.column_dimensions[col].width = width

                    # 设置首行样式
                for cell in ws[1]:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center')

            print(f"\n✅ 审计报告已生成：{filename}")
        except PermissionError:
            print("\n❌ 文件被占用，请关闭Excel后重试")
        except Exception as e:
            print(f"\n❗ 导出时发生意外错误：{str(e)}")


if __name__ == "__main__":
    # 初始化分析器（参数已配置）
    analyzer = OptimizedTableDiffAnalyzer(
        host="10.10.10.215",
        port=3306,
        user="etladmin",
        password="etladmin123",
        database="HG_SourceDB"
    )

    try:
        total, details = analyzer.analyze_differences()
        analyzer.generate_report(total, details)
    finally:
        analyzer.conn.close()