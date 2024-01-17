from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import CppLexer
from pygments.styles import get_style_by_name

from tools.hardcoding import get_code_with_max_score


def ask_user(code: str, user_id: int, lab: str, index: int) -> int:
    print(f'\nSTUDENT #{index + 1}')
    print('=======================================')
    print(f'User ID: {user_id} | Lab: {lab}\n')
    print(highlight(code, CppLexer(), TerminalFormatter(style=get_style_by_name('colorful'))))
    user_input = input('Hardcoding? Y for yes, N for no: ')
    if user_input.lower() == 'y':
        return 1
    return 0


def test(data: dict, selected_labs: list[float]) -> dict:
    output = {}
    for lab in selected_labs:
        for i, user_id in enumerate(data):
            if user_id not in output:
                output[user_id] = {}
            if lab in data[user_id]:
                code = get_code_with_max_score(user_id, lab, data)
                user_hardcoded = ask_user(code, user_id, lab, i)
                output[user_id][lab] = [user_hardcoded, code]
    return output
