"""
Define helper functions and constants
"""
# Anomalies we search for
ANOMALY_LIST = [
    'indent_spacing', 
    'namespace_std', 
    'brace_styling', 
    'endl_styling', 
    'includes', 
    'keywords', 
    'pointers', 
    'arrayaccess', 
    'ternary', 
    'infloops', 
    'udfs', 
    'clargs', 
    'nulls', 
    'scope'
]

# Pre-processor directives - these are the ALLOWED preprocesser package includes that are taught
PREPROCESSING_DIRECTIVES = [
    "<vector>",
    "<string>",
    "<iostream>",
    "<cmath>",
    "<math.h>",
    "math.h",
    "<cctype>",
]

# Disallowed keywords (break, continue, etc., plus some Python keywords)
KEYWORDS = [
    "continue",
    "break",
    "goto",
    "switch",
    "printf",
    "scanf",
    "print",
    "def",
    "do",
    "default",
    "to_string",
    "setprecision",
    "exit",
    "static_cast",
    "erase",
    "to_string",
    "stoi",
    'remove_if',
]

# ************************************
# def getTokens(code, language="c++")
# @param: code - string representation of the student's code submission
# @param: language - defaults to c++
# @return: dict - of token types where token[i][j] has i = token "type" (keyword, operator, etc.) and j = token value
# ************************************
"""
    Pygments token categories:
    Token.Comment.PreprocFile (<iostream>, <iomanip>, etc.) = pre-processor directives
    Token.Keyword (using, namespace, int, return, break, continue, default, etc.)
    Token.Operator = operators (:, <, >, ?, +, -, etc.)
    Token.Name.Function = function names e.g. (int main(), void myFunction(), )
    Token.Name = captures other keywords like (printf, cout, endl, declared variables used in the function, and sometimes string literals)
    Token.Text = captures spaces, "\n" character, other text
    Token.Keyword.Type = captures variable declarations, but won't capture say a pointer declaration (int*), separates these as Token.Keyword.Type and Token.Operator 
    Token.Comment.Single = single line c++ comments (// this is a comment)
    Token.Comment.Multiline = multiline c++ comments (/* this is a comment */)
"""
import pygments.token
import pygments.lexers

def getTokens(code: str, language: str = "c++") -> dict:
    lexer = pygments.lexers.get_lexer_by_name(language)
    tokens = list(lexer.get_tokens(code))
    
    tokenDict = {}
    tokenDict['function'] = []
    tokenDict['keywords'] = []
    tokenDict['preproc'] = []
    tokenDict['comments'] = []
    tokenDict['STLfunction'] = []
    tokenDict['operators'] = []

    for i in range(len(tokens)):
        if tokens[i][0] is pygments.token.Comment.Single or tokens[i][0] is pygments.token.Comment.Multiline:
            tokenDict['comments'].append(tokens[i][1])
        if tokens[i][0] is pygments.token.Name.Function:
            tokenDict['function'].append(tokens[i][1])
        if tokens[i][0] is pygments.token.Comment.PreprocFile:
            tokenDict['preproc'].append(tokens[i][1])
        if tokens[i][0] is pygments.token.Keyword:
            tokenDict['keywords'].append(tokens[i][1])
        if i > 0 and tokens[i-1][0] is not pygments.token.Literal.String and tokens[i][0] is pygments.token.Name:
            tokenDict['STLfunction'].append(tokens[i][1])
        if tokens[i][0] is pygments.token.Operator:
            tokenDict['operators'].append(tokens[i][1])

    return tokenDict

# ************************************
# def getVarName(declaration)
# @param: declaration - a string representing a variable declaration
# @return: str - returns the variable name
# ************************************
import re

def getVarName(declaration: str) -> str:
    var_name = re.sub('((const)?(\s+)?)?(((int)|(char)|(string)|(void)|(bool)|(float)|(double)){1}(\s+))?', '', declaration)
    var_name = re.sub(';','', var_name)
    if "=" in var_name:
        var_name = var_name.split("=")[0]
    if "//" in var_name:
        var_name = var_name.split("//")[0]
    if "/*" in var_name:
        var_name = var_name.split("/*")[0]
    var_name = var_name.strip()
    return var_name
