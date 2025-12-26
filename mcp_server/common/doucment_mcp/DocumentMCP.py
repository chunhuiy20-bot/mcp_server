from fastmcp import FastMCP

mcp = FastMCP(name="DocumentMCP", instructions="文档工具[注意：调用其他方法前，请先调用search_files查询文件是否存在]")


@mcp.tool
async def search_files(directory: str = ".", pattern: str = "*", recursive: bool = True):
    """
    搜索当前目录下的文件
    Args:
        directory: 搜索目录，默认为当前目录
        pattern: 文件匹配模式，支持通配符，默认为所有文件
        recursive: 是否递归搜索子目录，默认为True
    """
    from pathlib import Path

    try:
        search_path = Path(directory)

        # 检查目录是否存在
        if not search_path.exists():
            return {
                "success": False,
                "message": f"目录 {directory} 不存在",
                "directory": directory,
                "error": "DirectoryNotFoundError"
            }

        # 检查是否是目录
        if not search_path.is_dir():
            return {
                "success": False,
                "message": f"{directory} 不是一个目录",
                "directory": directory,
                "error": "NotADirectoryError"
            }

        files = []
        directories = []

        # 根据是否递归选择搜索方法
        if recursive:
            # 递归搜索
            for item in search_path.rglob(pattern):
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "relative_path": str(item.relative_to(search_path)),
                        "size": item.stat().st_size,
                        "extension": item.suffix,
                        "parent": str(item.parent)
                    })
                elif item.is_dir():
                    directories.append({
                        "name": item.name,
                        "path": str(item),
                        "relative_path": str(item.relative_to(search_path))
                    })
        else:
            # 只搜索当前目录
            for item in search_path.glob(pattern):
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "relative_path": item.name,
                        "size": item.stat().st_size,
                        "extension": item.suffix,
                        "parent": str(item.parent)
                    })
                elif item.is_dir():
                    directories.append({
                        "name": item.name,
                        "path": str(item),
                        "relative_path": item.name
                    })

        return {
            "success": True,
            "message": f"搜索完成，找到 {len(files)} 个文件，{len(directories)} 个目录",
            "directory": str(search_path.absolute()),
            "pattern": pattern,
            "recursive": recursive,
            "files": files,
            "directories": directories,
            "total_files": len(files),
            "total_directories": len(directories)
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"搜索文件失败: {str(e)}",
            "directory": directory,
            "error": str(e)
        }


@mcp.tool
async def read_file(file_name: str):
    """
    读取文件内容工具
    Args:
        file_name: 文件名
    """
    import aiofiles
    from pathlib import Path

    try:
        file_path = Path(file_name)

        # 检查文件是否存在
        if not file_path.exists():
            return {
                "success": False,
                "message": f"文件 {file_name} 不存在",
                "file_name": file_name,
                "error": "FileNotFoundError"
            }

        # 检查是否是文件
        if not file_path.is_file():
            return {
                "success": False,
                "message": f"{file_name} 不是一个文件",
                "file_name": file_name,
                "error": "NotAFileError"
            }

        # 尝试判断文件类型（根据扩展名）
        file_extension = file_path.suffix.lower()
        binary_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp',
                             '.zip', '.tar', '.gz', '.exe', '.bin']

        # 根据文件类型选择读取模式
        if file_extension in binary_extensions:
            # 二进制模式读取
            async with aiofiles.open(file_path, mode='rb') as f:  # type: ignore
                content = await f.read()

            return {
                "success": True,
                "message": f"文件 {file_name} 读取成功（二进制）",
                "file_path": str(file_path.absolute()),
                "file_type": "binary",
                "content": content,
                "size": len(content)
            }
        else:
            # 文本模式读取
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:  # type: ignore
                content = await f.read()

            return {
                "success": True,
                "message": f"文件 {file_name} 读取成功",
                "file_path": str(file_path.absolute()),
                "file_type": "text",
                "content": content,
                "size": len(content),
                "lines": content.count('\n') + 1
            }

    except UnicodeDecodeError:
        # 如果文本解码失败，尝试二进制读取
        try:
            async with aiofiles.open(file_path, mode='rb') as f:  # type: ignore
                content = await f.read()

            return {
                "success": True,
                "message": f"文件 {file_name} 以二进制模式读取成功",
                "file_path": str(file_path.absolute()),
                "file_type": "binary",
                "content": content,
                "size": len(content),
                "warning": "文件包含非UTF-8字符，已使用二进制模式读取"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"读取文件失败: {str(e)}",
                "file_name": file_name,
                "error": str(e)
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"读取文件失败: {str(e)}",
            "file_name": file_name,
            "error": str(e)
        }


@mcp.tool
async def write_file(file_name: str, content: str, file_type: str):
    """
    写文件工具
    Args:
        file_name: 文件名
        content: 文件内容
        file_type: 文件类型
    """
    import aiofiles
    import os
    from pathlib import Path

    try:
        # 确保文件路径存在
        file_path = Path(file_name)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 根据文件类型选择写入模式
        mode = 'w'
        encoding = 'utf-8'

        # 如果是二进制文件类型，使用二进制模式
        if file_type in ['binary', 'image', 'pdf']:
            mode = 'wb'
            encoding = None

        # 异步写入文件
        if encoding:
            async with aiofiles.open(file_path, mode=mode, encoding=encoding) as f:  # type: ignore
                await f.write(content)
        else:
            async with aiofiles.open(file_path, mode=mode) as f:  # type: ignore
                await f.write(content)

        return {
            "success": True,
            "message": f"文件 {file_name} 写入成功",
            "file_path": str(file_path.absolute()),
            "file_type": file_type
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"写入文件失败: {str(e)}",
            "file_name": file_name,
            "error": str(e)
        }



@mcp.tool
async def delete_file(file_name: str):
    """
    删除文件工具
    Args:
        file_name: 文件名
    """
    pass


@mcp.tool
async def alter_file(
        file_name: str,
        content: str = None,
        line_number: int = None,
        line_range: list = None,
        line_replacements: list = None,  # 批量替换多行 [{"line": 1, "text": "..."}, {"line": 3, "text": "..."}]
        new_text: str = None,
        old_text: str = None,
        mode: str = "replace_line"
):
    """
    修改文件内容工具
    Args:
        file_name: 文件名
        content: 完整替换的文件内容（mode="full"时使用）
        line_number: 要修改的行号（从1开始，mode="replace_line"时使用）
        line_range: 要修改的行范围 [start, end]（mode="replace_lines"时使用）
        line_replacements: 批量替换多行，格式：[{"line": 1, "text": "新内容"}, {"line": 3, "text": "新内容"}]
        new_text: 替换后的新文本
        old_text: 要替换的旧文本（mode="replace_text"时使用）
        mode: 修改模式
            - "full": 完整替换文件内容
            - "replace_line": 替换指定单行
            - "replace_lines": 替换指定行范围（多行）
            - "replace_multiple": 批量替换多个指定行
            - "replace_text": 替换所有匹配的文本
            - "append": 追加内容到文件末尾
            - "insert_line": 在指定行号插入新行
            - "delete_line": 删除指定行
            - "delete_lines": 删除指定行范围
    """
    import aiofiles
    from pathlib import Path

    try:
        file_path = Path(file_name)

        if not file_path.exists():
            return {
                "success": False,
                "message": f"文件 {file_name} 不存在",
                "error": "FileNotFoundError"
            }

        # 读取原文件内容
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:  # type: ignore
            original_content = await f.read()
            lines = original_content.splitlines(keepends=True)

        modified_content = None

        if mode == "full":
            if content is None:
                return {"success": False, "message": "mode='full' 需要提供 content 参数"}
            modified_content = content

        elif mode == "replace_line":
            if line_number is None or new_text is None:
                return {"success": False, "message": "mode='replace_line' 需要提供 line_number 和 new_text"}

            if line_number < 1 or line_number > len(lines):
                return {"success": False, "message": f"行号 {line_number} 超出范围（共 {len(lines)} 行）"}

            lines[line_number - 1] = new_text if new_text.endswith('\n') else new_text + '\n'
            modified_content = ''.join(lines)

        elif mode == "replace_lines":
            if line_range is None or new_text is None:
                return {"success": False, "message": "mode='replace_lines' 需要提供 line_range 和 new_text"}

            if len(line_range) != 2:
                return {"success": False, "message": "line_range 必须是 [start, end]"}

            start_line, end_line = line_range

            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                return {"success": False, "message": f"行范围 [{start_line}, {end_line}] 无效"}

            replacement_text = new_text if new_text.endswith('\n') else new_text + '\n'
            new_lines = lines[:start_line - 1]
            new_lines.append(replacement_text)
            new_lines.extend(lines[end_line:])
            modified_content = ''.join(new_lines)

        elif mode == "replace_multiple":
            # 批量替换多个指定行
            if line_replacements is None:
                return {"success": False, "message": "mode='replace_multiple' 需要提供 line_replacements"}

            if not isinstance(line_replacements, list):
                return {"success": False, "message": "line_replacements 必须是列表"}

            # 验证所有行号
            for item in line_replacements:
                if not isinstance(item, dict) or "line" not in item or "text" not in item:
                    return {"success": False, "message": "line_replacements 格式错误，需要 [{'line': 1, 'text': '...'}]"}

                line_num = item["line"]
                if line_num < 1 or line_num > len(lines):
                    return {"success": False, "message": f"行号 {line_num} 超出范围（共 {len(lines)} 行）"}

            # 执行批量替换
            for item in line_replacements:
                line_num = item["line"]
                text = item["text"]
                lines[line_num - 1] = text if text.endswith('\n') else text + '\n'

            modified_content = ''.join(lines)

        elif mode == "replace_text":
            if old_text is None or new_text is None:
                return {"success": False, "message": "mode='replace_text' 需要提供 old_text 和 new_text"}

            modified_content = original_content.replace(old_text, new_text)

            if modified_content == original_content:
                return {"success": False, "message": f"未找到要替换的文本: {old_text}"}

        elif mode == "append":
            if content is None:
                return {"success": False, "message": "mode='append' 需要提供 content"}
            modified_content = original_content + content

        elif mode == "insert_line":
            if line_number is None or new_text is None:
                return {"success": False, "message": "mode='insert_line' 需要提供 line_number 和 new_text"}

            if line_number < 1 or line_number > len(lines) + 1:
                return {"success": False, "message": f"行号 {line_number} 超出范围"}

            insert_text = new_text if new_text.endswith('\n') else new_text + '\n'
            lines.insert(line_number - 1, insert_text)
            modified_content = ''.join(lines)

        elif mode == "delete_line":
            if line_number is None:
                return {"success": False, "message": "mode='delete_line' 需要提供 line_number"}

            if line_number < 1 or line_number > len(lines):
                return {"success": False, "message": f"行号 {line_number} 超出范围"}

            del lines[line_number - 1]
            modified_content = ''.join(lines)

        elif mode == "delete_lines":
            if line_range is None:
                return {"success": False, "message": "mode='delete_lines' 需要提供 line_range"}

            if len(line_range) != 2:
                return {"success": False, "message": "line_range 必须是 [start, end]"}

            start_line, end_line = line_range

            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                return {"success": False, "message": f"行范围 [{start_line}, {end_line}] 无效"}

            del lines[start_line - 1:end_line]
            modified_content = ''.join(lines)

        else:
            return {"success": False, "message": f"不支持的模式: {mode}"}

        # 写入修改后的内容
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:  # type: ignore
            await f.write(modified_content)

        return {
            "success": True,
            "message": f"文件 {file_name} 修改成功",
            "file_path": str(file_path.absolute()),
            "mode": mode,
            "original_lines": len(original_content.splitlines()),
            "modified_lines": len(modified_content.splitlines())
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"修改文件失败: {str(e)}",
            "error": str(e)
        }


if __name__ == "__main__":
    print(mcp)
    mcp.run(transport="http", host="0.0.0.0", port=8003)
