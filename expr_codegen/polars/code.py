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
        prefix2, asset, date = tup
        return f'df = df.sort(by={[asset, date]}).groupby(by={[asset]}, maintain_order=True).apply({func_name})'
    if prefix2 == CS:
        prefix2, date = tup
        # TODO: 这里是否需要sort, 哪种速度更快
        return f'df = df.sort(by={[date]}).groupby(by={[date]}, maintain_order=False).apply({func_name})'
    if prefix2 == GP:
        prefix2, date, group = tup
        # TODO: 这里是否需要sort, 哪种速度更快
        return f'df = df.sort(by={[date, group]}).groupby(by={[date, group]}, maintain_order=False).apply({func_name})'

    return f'df = {func_name}(df)'


def codegen(exprs_ldl: ListDictList, exprs_src, filename='template.py.j2'):
    """基于模板的代码生成"""
    # 打印Polars风格代码
    p = PolarsStrPrinter()

    # polars风格代码
    funcs = {}
    # 分组应用代码
    groupbys = {}
    # 处理过后的表达式
    exprs_dst = []

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
                    exprs_dst.append(f"# #" + '=' * 40 + func_name)
                else:
                    va, ex = kv
                    func_code.append(f"# {va} = {ex}\n{va}=({p.doprint(ex)}),")
                    exprs_dst.append(f"# {va} = {ex}")
            func_code.append(f"    )")

            # polars风格代码列表
            funcs[func_name] = '\n'.join(func_code[1:])
            # 分组应用代码
            groupbys[func_name] = get_groupby_from_tuple(k, func_name)

    env = jinja2.Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    template = env.get_template(filename)
    return template.render(funcs=funcs, groupbys=groupbys,
                           exprs_src=exprs_src, exprs_dst=exprs_dst)