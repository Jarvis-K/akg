#!/usr/bin/env python3
# Copyright 2025 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
迁移脚本：将langchain代码替换为OpenAI接口
"""

import os
import re
import argparse
from pathlib import Path


def replace_imports(content: str) -> str:
    """替换导入语句"""
    replacements = [
        (r'from langchain\.prompts import PromptTemplate', 
         'from ai_kernel_generator.utils.prompt_template import PromptTemplate'),
        (r'from langchain\.output_parsers import PydanticOutputParser',
         'from ai_kernel_generator.utils.output_parser import PydanticOutputParser'),
        (r'from ai_kernel_generator\.core\.llm\.model_loader import create_model',
         'from ai_kernel_generator.core.llm.openai_model_loader import create_openai_model'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    return content


def replace_function_calls(content: str) -> str:
    """替换函数调用"""
    replacements = [
        (r'create_model\(', 'create_openai_model('),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    return content


def migrate_file(file_path: Path) -> bool:
    """迁移单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 执行替换
        content = replace_imports(content)
        content = replace_function_calls(content)
        
        # 如果有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 迁移完成: {file_path}")
            return True
        else:
            print(f"- 无需迁移: {file_path}")
            return False
            
    except Exception as e:
        print(f"✗ 迁移失败: {file_path} - {str(e)}")
        return False


def find_python_files(directory: Path) -> list:
    """查找所有Python文件"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过一些目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'build', 'dist']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files


def main():
    parser = argparse.ArgumentParser(description='将langchain代码迁移到OpenAI接口')
    parser.add_argument('--directory', '-d', type=str, default='.',
                       help='要处理的目录路径 (默认: 当前目录)')
    parser.add_argument('--dry-run', action='store_true',
                       help='只显示会被修改的文件，不实际修改')
    
    args = parser.parse_args()
    
    directory = Path(args.directory).resolve()
    
    if not directory.exists():
        print(f"错误: 目录不存在: {directory}")
        return 1
    
    print(f"开始迁移目录: {directory}")
    print(f"干运行模式: {'是' if args.dry_run else '否'}")
    print("-" * 50)
    
    python_files = find_python_files(directory)
    print(f"找到 {len(python_files)} 个Python文件")
    
    migrated_count = 0
    
    for file_path in python_files:
        if args.dry_run:
            # 干运行模式：只检查不修改
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = replace_imports(content)
                new_content = replace_function_calls(new_content)
                
                if new_content != content:
                    print(f"需要迁移: {file_path}")
                    migrated_count += 1
            except Exception as e:
                print(f"检查失败: {file_path} - {str(e)}")
        else:
            # 实际迁移
            if migrate_file(file_path):
                migrated_count += 1
    
    print("-" * 50)
    if args.dry_run:
        print(f"总共有 {migrated_count} 个文件需要迁移")
    else:
        print(f"总共迁移了 {migrated_count} 个文件")
    
    return 0


if __name__ == '__main__':
    exit(main())