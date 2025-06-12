#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 修复llm_client.py的缩进问题

def fix_indentation():
    filename = 'rs/llm_agent/llm_client.py'
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复第363行的缩进问题
    # 该行当前有错误的缩进，应该与elif子句保持一致
    if len(lines) > 362:
        line_363 = lines[362]  # 第363行 (0-indexed)
        print(f"Original line 363: {repr(line_363)}")
        
        # 替换为正确的缩进（8个空格而不是12个）
        if line_363.strip().startswith('if "移除卡牌"'):
            lines[362] = '            if "移除卡牌" in context and "deck" in gs:\n'
            print("Fixed line 363 indentation")
    
    # 写回文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Indentation fix completed!")

if __name__ == "__main__":
    fix_indentation() 