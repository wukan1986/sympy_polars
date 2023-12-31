import os

import jinja2
from jinja2 import FileSystemLoader

from expr_codegen.expr import TS, CS, GP
from expr_codegen.model import ListDictList
from expr_codegen.polars.printer import PolarsStrPrinter


def get_groupby_from_tuple(tup, func_name):
    """从传入的元组中生成分组运行代码"""
    prefix2, *_ = tup

    if prefix2 == TS:
        # 组内需要按时间进行排序，需要维持顺序
        prefix2, asset = tup
        return f'df = df.group_by(by=[_ASSET_]).map_groups({func_name})'
    if prefix2 == CS:
        prefix2, date = tup
        return f'df = df.group_by(by=[_DATE_]).map_groups({func_name})'
    if prefix2 == GP:
        prefix2, date, group = tup
        return f'df = df.group_by(by=[_DATE_, "{group}"]).map_groups({func_name})'

    return f'df = {func_name}(df)'


def symbols_to_code(syms):
    a = [f"{s}" for s in syms]
    b = [f"pl.col('{s}')" for s in syms]
    return f"({','.join(a)},) = ({','.join(b)},)"


def codegen(exprs_ldl: ListDictList, exprs_src, syms_dst,
            filename='template.py.j2',
            date='date', asset='asset'):
    """基于模板的代码生成"""
    # 打印Polars风格代码
    p = PolarsStrPrinter()

    # polars风格代码
    funcs = {}
    # 分组应用代码。这里利用了字典按插入顺序排序的特点，将排序放在最前
    groupbys = {'sort': 'df = df'}
    # 处理过后的表达式
    exprs_dst = []
    syms_out = []

    for i, row in enumerate(exprs_ldl.values()):
        for k, vv in row.items():
            if len(vv) == 0:
                continue
            # 函数名
            func_name = f'func_{i}_{"__".join(k)}'
            func_code = []
            for kv in vv:
                if kv is None:
                    func_code.append(f"    )")
                    func_code.append(f"# " + '=' * 40)
                    func_code.append(f"    df = df.with_columns(")
                    exprs_dst.append(f"#" + '=' * 40 + func_name)
                else:
                    va, ex = kv
                    func_code.append(f"# {va} = {ex}\n{va}={p.doprint(ex)},")
                    exprs_dst.append(f"{va} = {ex}")
                    syms_out.append(va)
            func_code.append(f"    )")
            func_code = func_code[1:]

            if k[0] == TS:
                groupbys['sort'] = f'df = df.sort(by=[_DATE_, _ASSET_])'
                # 时序需要排序
                func_code = [f'    df = df.sort(by=[_DATE_])'] + func_code

            # polars风格代码列表
            funcs[func_name] = '\n'.join(func_code)
            # 分组应用代码
            groupbys[func_name] = get_groupby_from_tuple(k, func_name)

    syms1 = symbols_to_code(syms_dst)
    syms2 = symbols_to_code(syms_out)

    env = jinja2.Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    template = env.get_template(filename)
    return template.render(funcs=funcs, groupbys=groupbys,
                           exprs_src=exprs_src, exprs_dst=exprs_dst,
                           syms1=syms1, syms2=syms2,
                           date=date, asset=asset)
