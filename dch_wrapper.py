#!/usr/bin/env python3
"""
dch-wrapper: 帮助非deb开发者使用dch命令的Python脚本

这个脚本自动化了dch命令的使用流程，包括：
1. 检查dch命令是否可用
2. 配置DEBEMAIL和DEBFULLNAME环境变量
3. 检查git工作目录状态，确保没有冲突的修改
4. 读取git log作为变更日志
5. 分两步执行dch命令：
   - 第一步：调用dch命令添加变更日志到changelog文件
   - 第二步：调用dch -e命令打开编辑器，让用户手动调整和编辑变更日志

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
                    ['git', 'log', f'{latest_tag}..HEAD', '--format=%s', '--no-merges'],
                    text=True,
                    stderr=subprocess.DEVNULL
                ).strip()
                print(f"📝 获取从tag {latest_tag} 到当前HEAD的变更")
            else:
                # 获取所有提交
                commits = subprocess.check_output(
                    ['git', 'log', '--format=%s', '--no-merges'],
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
                    formatted_commits.append(f"* {line.strip()}")
            
            return '\n'.join(formatted_commits)
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  警告: 无法获取git变更日志: {e}")
            return "无法获取变更记录"
    
    def check_git_status(self) -> bool:
        """
        检查git状态，确保没有未commit的修改
        
        Returns:
            bool: 是否可以继续执行
        """
        try:
            # 检查是否有未commit的修改
            status = subprocess.check_output(
                ['git', 'status', '--porcelain'], 
                text=True, 
                stderr=subprocess.DEVNULL
            ).strip()
            
            if not status:
                print("✅ Git工作目录干净，没有未commit的修改")
                return True
            
            # 检查debian/changelog是否有修改
            changelog_modified = False
            for line in status.split('\n'):
                if line.strip() and 'debian/changelog' in line:
                    changelog_modified = True
                    break
            
            if changelog_modified:
                print("❌ 错误: debian/changelog文件有未commit的修改")
                print("请先提交或丢弃对debian/changelog的修改，然后再运行此脚本")
                print("建议操作:")
                print("  git add debian/changelog && git commit -m '更新变更日志'")
                print("  或者")
                print("  git checkout -- debian/changelog")
                return False
            
            # 有其他文件的修改，给出警告
            print("⚠️  警告: 发现未commit的修改:")
            for line in status.split('\n'):
                if line.strip():
                    status_code = line[:2]
                    file_path = line[3:]
                    print(f"  {status_code} {file_path}")
            
            print("\n建议在运行dch-wrapper之前先提交这些修改")
            print("是否继续执行? (y/N): ", end="")
            
            try:
                response = input().strip().lower()
                if response in ['y', 'yes', '是']:
                    print("继续执行...")
                    return True
                else:
                    print("用户取消操作")
                    return False
            except KeyboardInterrupt:
                print("\n用户中断操作")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"⚠️  警告: 无法检查git状态: {e}")
            print("继续执行...")
            return True
    
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
            print(f"第一步命令: {' '.join(dch_cmd)}")
            print(f"变更日志内容:\n{changelog}")
            print("第二步命令: dch -e")
            return True
        
        try:
            # 第一步：运行dch命令添加变更日志
            print("🚀 第一步：启动dch命令添加变更日志...")
            
            # 设置环境变量
            env = os.environ.copy()
            
            # 运行dch命令
            result = subprocess.run(dch_cmd, env=env, check=True)
            
            print("✅ dch命令执行完成")
            
            # 第二步：运行dch -e命令打开编辑器
            print("📝 第二步：启动dch -e命令打开编辑器...")
            print("请编辑变更日志后保存并退出编辑器")
            
            dch_edit_cmd = ['dch', '-e']
            result = subprocess.run(dch_edit_cmd, env=env, check=True)
            
            print("✅ 编辑器关闭，变更日志编辑完成")
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
        
        # 3. 检查git状态
        if not self.check_git_status():
            return False
        
        # 4. 运行dch命令
        return self.run_dch(custom_message, dch_version)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="dch-wrapper: 帮助非deb开发者使用dch命令",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 dch_wrapper.py                                    # 使用git log作为变更日志，分两步执行dch
  python3 dch_wrapper.py "修复bug"                          # 使用自定义消息，分两步执行dch
  python3 dch_wrapper.py --dch-version 1.2.3 "新版本发布"   # 指定版本号和消息，分两步执行dch
  python3 dch_wrapper.py --dry-run                         # 模拟执行，显示两步命令
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