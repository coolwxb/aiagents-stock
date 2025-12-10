# 股票代码转换工具
def add_market_suffix(code: str) -> str:
    """
    根据6位数字证券代码自动添加 .SH 或 .SZ 后缀。
    
    支持类型：
      - 沪市：60/68/51/58/50 开头 → .SH
      - 深市：00/30/15/16 开头 → .SZ
    
    参数:
        code (str): 6位纯数字字符串，如 "510300", "300750"
    
    返回:
        str: 带后缀的完整代码，如 "510300.SH"
    
    异常:
        ValueError: 输入格式错误或无法识别市场
    """
    if not isinstance(code, str):
        raise TypeError("代码必须是字符串")
    
    # 去除空格并转为大写（防御性处理）
    code = code.strip()
    
    # 如果已带后缀，直接返回（避免重复添加）
    if code.endswith(('.SH', '.SZ', '.BJ')):
        return code.upper()
    
    # 必须是6位纯数字
    if len(code) != 6 or not code.isdigit():
        raise ValueError(f"无效代码格式（需6位数字）: '{code}'")

    # 沪市规则（SH）—— 上交所
    if code.startswith(('60', '68', '51', '58', '50')):
        return code + ".SH"
    
    # 深市规则（SZ）—— 深交所
    elif code.startswith(('00', '30', '15', '16')):
        return code + ".SZ"
    
    # 北交所（虽无ETF，但为完整性保留）
    elif code.startswith('8'):
        return code + ".BJ"
    
    else:
        raise ValueError(f"无法识别交易所的代码: {code}")

def remove_market_suffix(code: str) -> str:
    """
    从带市场后缀的证券代码中移除后缀，返回6位纯数字代码。
    
    支持的后缀：.SH, .SZ, .BJ（不区分大小写）
    
    参数:
        code (str): 带或不带后缀的代码，如 "510300.SH", "159915.sz", "830000.BJ"
    
    返回:
        str: 6位纯数字代码，如 "510300"
    
    异常:
        ValueError: 输入格式无效
    """
    if not isinstance(code, str):
        raise TypeError("输入必须是字符串")
    
    code = code.strip()
    
    # 如果已经不含点号，直接验证是否为6位数字
    if '.' not in code:
        if len(code) == 6 and code.isdigit():
            return code
        else:
            raise ValueError(f"不带后缀的代码必须是6位数字: '{code}'")
    
    # 分割主代码和后缀
    parts = code.split('.')
    if len(parts) != 2:
        raise ValueError(f"代码格式错误（最多一个点）: '{code}'")
    
    main_code, suffix = parts[0], parts[1].upper()
    
    # 验证后缀是否合法（可扩展）
    valid_suffixes = {'SH', 'SZ', 'BJ'}
    if suffix not in valid_suffixes:
        raise ValueError(f"不支持的市场后缀: '{suffix}'，仅支持 {valid_suffixes}")
    
    # 验证主代码是否为6位数字
    if len(main_code) != 6 or not main_code.isdigit():
        raise ValueError(f"主代码部分必须是6位数字: '{main_code}'")
    
    return main_code