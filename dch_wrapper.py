#!/usr/bin/env python3
"""
dch-wrapper: 帮助非deb开发者使用dch命令的Python脚本

这个脚本自动化了dch命令的使用流程，包括：
1. 检查dch命令是否可用
2. 配置DEBEMAIL和DEBFULLNAME环境变量
3. 读取git log作为变更日志
4. 调用dch命令

使用方法:
    python3 dch_wrapper.py [选项] [消息]

选项:
    --help, -h          显示帮助信息
    --version, -v       显示版本信息
    --dry-run          只显示将要执行的操作，不实际执行
    --dch-version      指定dch版本号参数
    消息               自定义提交消息（可选）
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from typing import Optional, Tuple, List


class DchWrapper:
    """dch命令包装器类"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.project_root = Path.cwd()
        
    def check_dch_available(self) -> bool:
        """
        检查dch命令是否可用
        
        Returns:
            bool: dch命令是否可用
        """
        if shutil.which('dch') is None:
            print("❌ 错误: dch命令未找到")
            print("请安装devscripts包:")
            print("  Ubuntu/Debian: sudo apt-get install devscripts")
            print("  CentOS/RHEL: sudo yum install devscripts")
            print("  Fedora: sudo dnf install devscripts")
            return False
        return True
    
    def get_git_author_info(self) -> Tuple[str, str]:
        """
        从git配置中获取作者信息
        
        Returns:
            Tuple[str, str]: (作者名, 邮箱)
        """
        try:
            # 获取git用户名
            name = subprocess.check_output(
                ['git', 'config', 'user.name'], 
                text=True, 
                stderr=subprocess.DEVNULL
            ).strip()
        except subprocess.CalledProcessError:
            name = "Unknown"
            
        try:
            # 获取git邮箱
            email = subprocess.check_output(
                ['git', 'config', 'user.email'], 
                text=True, 
                stderr=subprocess.DEVNULL
            ).strip()
        except subprocess.CalledProcessError:
            email = "unknown@example.com"
            
        return name, email
    
    def setup_environment_variables(self) -> None:
        """
        设置DEBEMAIL和DEBFULLNAME环境变量
        """
        # 检查环境变量是否已设置
        debemail = os.environ.get('DEBEMAIL')
        debfullname = os.environ.get('DEBFULLNAME')
        
        if not debemail or not debfullname:
            name, email_addr = self.get_git_author_info()
            
            if not debemail:
                os.environ['DEBEMAIL'] = email_addr
                print(f"✅ 设置 DEBEMAIL={email_addr}")
                
            if not debfullname:
                os.environ['DEBFULLNAME'] = name
                print(f"✅ 设置 DEBFULLNAME={name}")
        else:
            print(f"✅ 环境变量已设置: DEBEMAIL={debemail}, DEBFULLNAME={debfullname}")
    
    def get_git_changes_since_last_tag(self) -> str:
        """
        获取从上次tag到当前commit的git变更日志
        
        Returns:
            str: 变更日志内容
        """
        try:
            # 获取最新的tag
            latest_tag = subprocess.check_output(
                ['git', 'describe', '--tags', '--abbrev=0'], 
                text=True, 
                stderr=subprocess.DEVNULL
            ).strip()
        except subprocess.CalledProcessError:
            # 如果没有tag，获取所有提交
            latest_tag = None
        
        try:
            if latest_tag:
                # 获取从最新tag到HEAD的提交
                commits = subprocess.check_output(
                    ['git', 'log', f'{latest_tag}..HEAD', '--oneline', '--no-merges'],
                    text=True,
                    stderr=subprocess.DEVNULL
                ).strip()
                print(f"📝 获取从tag {latest_tag} 到当前HEAD的变更")
            else:
                # 获取所有提交
                commits = subprocess.check_output(
                    ['git', 'log', '--oneline', '--no-merges'],
                    text=True,
                    stderr=subprocess.DEVNULL
                ).strip()
                print("📝 获取所有提交记录")
                
            if not commits:
                return "无变更记录"
                
            # 格式化提交信息
            lines = commits.split('\n')
            formatted_commits = []
            for line in lines:
                if line.strip():
                    # 移除commit hash，只保留提交信息
                    commit_msg = line.split(' ', 1)[1] if ' ' in line else line
                    formatted_commits.append(f"* {commit_msg}")
            
            return '\n'.join(formatted_commits)
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  警告: 无法获取git变更日志: {e}")
            return "无法获取变更记录"
    
    def run_dch(self, custom_message: Optional[str] = None, dch_version: Optional[str] = None) -> bool:
        """
        运行dch命令
        
        Args:
            custom_message: 自定义提交消息
            dch_version: dch版本号参数
            
        Returns:
            bool: 是否成功
        """
        # 检查是否在debian目录中
        debian_dir = self.project_root / 'debian'
        if not debian_dir.exists():
            print("❌ 错误: 未找到debian目录")
            print("请确保当前目录包含debian/目录，或者切换到正确的项目目录")
            return False
        
        # 获取变更日志
        if custom_message:
            changelog = custom_message
        else:
            changelog = self.get_git_changes_since_last_tag()
        
        # 构建dch命令
        dch_cmd = ['dch']
        
        # 添加版本号参数
        if dch_version:
            dch_cmd.extend(['-v', dch_version])
        
        # 添加变更日志
        dch_cmd.append(changelog)
        
        if self.dry_run:
            print("🔍 模拟执行 (dry-run模式)")
            print(f"命令: {' '.join(dch_cmd)}")
            print(f"变更日志内容:\n{changelog}")
            return True
        
        try:
            # 运行dch命令
            print("🚀 启动dch命令...")
            print("dch将打开编辑器，请编辑变更日志后保存并退出")
            
            # 设置环境变量
            env = os.environ.copy()
            
            # 运行dch命令
            result = subprocess.run(dch_cmd, env=env, check=True)
            
            print("✅ dch命令执行完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ dch命令执行失败: {e}")
            return False
        except KeyboardInterrupt:
            print("\n⚠️  用户中断操作")
            return False
    
    def run(self, custom_message: Optional[str] = None, dch_version: Optional[str] = None) -> bool:
        """
        运行完整的dch包装流程
        
        Args:
            custom_message: 自定义提交消息
            dch_version: dch版本号参数
            
        Returns:
            bool: 是否成功
        """
        print("🔧 dch-wrapper 开始执行...")
        print(f"📁 项目目录: {self.project_root}")
        
        # 1. 检查dch命令是否可用
        if not self.check_dch_available():
            return False
        
        # 2. 设置环境变量
        self.setup_environment_variables()
        
        # 3. 运行dch命令
        return self.run_dch(custom_message, dch_version)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="dch-wrapper: 帮助非deb开发者使用dch命令",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 dch_wrapper.py                                    # 使用git log作为变更日志
  python3 dch_wrapper.py "修复bug"                          # 使用自定义消息
  python3 dch_wrapper.py --dch-version 1.2.3 "新版本发布"   # 指定版本号和消息
  python3 dch_wrapper.py --dry-run                         # 模拟执行
        """
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='只显示将要执行的操作，不实际执行'
    )
    
    parser.add_argument(
        '--dch-version',
        type=str,
        help='指定dch版本号参数'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='dch-wrapper 1.0.0'
    )
    
    parser.add_argument(
        'message',
        nargs='?',
        type=str,
        help='自定义提交消息（可选）'
    )
    
    args = parser.parse_args()
    
    # 创建dch包装器实例
    wrapper = DchWrapper(dry_run=args.dry_run)
    
    # 运行包装器
    success = wrapper.run(custom_message=args.message, dch_version=args.dch_version)
    
    if success:
        print("\n🎉 dch-wrapper 执行完成!")
    else:
        print("\n💥 dch-wrapper 执行失败!")
        sys.exit(1)


if __name__ == '__main__':
    main() 