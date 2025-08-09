#!/usr/bin/env python3
"""
Patch Application System following PROTOCOL.md
Processes 6 action types: System, DeleteFile, CreateFile, DeleteText, InsertText, ModifyText
"""

import argparse
import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import re

# TOO/APL/APLAA - Global variables and constants
BACKUP_ROOT = ".backups"
SUPPORTED_ACTIONS = ["System", "DeleteFile", "CreateFile", "DeleteText", "InsertText", "ModifyText"]

def create_backup(filepath, backup_session_dir):
    """
    TOO/APL/APLBB - Create backup of file before modification
    Args:
        filepath (Path): File to backup
        backup_session_dir (Path): Session backup directory
    Returns:
        bool: Success status
    """
    try:
        if not filepath.exists():
            return True  # No need to backup non-existent file
        
        # TOO/APL/APLBC - Calculate relative backup path
        backup_file = backup_session_dir / filepath
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        
        # TOO/APL/APLBD - Copy file preserving metadata
        shutil.copy2(filepath, backup_file)
        print(f">> Backup: {filepath} -> {backup_file}")
        return True
        
    except Exception as e:
        print(f"ERROR: Backup failed for {filepath}: {e}")
        return False

def normalize_context_lines(lines):
    """
    TOO/APL/APLCC - Normalize context lines by removing blank lines
    Args:
        lines (list): List of context lines
    Returns:
        list: Filtered lines without blanks
    """
    return [line for line in lines if line.strip()]

def parse_patch_content(content):
    """
    TOO/APL/APLDD - Parse patch content into action blocks
    Args:
        content (str): Raw patch content
    Returns:
        list: List of action dictionaries
    """
    actions = []
    lines = content.strip().split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # TOO/APL/APLDE - Look for action start markers
        if line.startswith('#Action '):
            action_type = line.split(' ', 2)[1]  # Extract action type
            
            if action_type not in SUPPORTED_ACTIONS:
                print(f"WARNING: Unknown action type: {action_type} at line {i+1}")
                i += 1
                continue
            
            # TOO/APL/APLDF - Create action object
            action = {
                'type': action_type,
                'start_line': i + 1,
                'local_paths': [],
                'content': []
            }
            
            i += 1
            
            # TOO/APL/APLDG - Parse action content until end marker
            while i < len(lines):
                current_line = lines[i].strip()
                
                # TOO/APL/APLDH - Check for action end
                if current_line.startswith(f'#END Action {action_type}'):
                    break
                    
                # TOO/APL/APLDI - Check for next action start (implicit end)
                if current_line.startswith('#Action '):
                    i -= 1  # Step back to process this action
                    break
                
                # TOO/APL/APLDJ - Parse Local paths
                if current_line.startswith('Local: '):
                    local_path = current_line.split('Local: ', 1)[1]
                    action['local_paths'].append(local_path)
                else:
                    # TOO/APL/APLDK - Collect all other content
                    action['content'].append(lines[i])
                
                i += 1
            
            actions.append(action)
        
        i += 1
    
    return actions

def parse_context_sections(content_lines):
    """
    TOO/APL/APLLL - Parse context sections with new delimited format
    Args:
        content_lines (list): Content lines from action
    Returns:
        tuple: (before_contexts, after_contexts, text_insertions) lists
    """
    before_contexts = []
    after_contexts = []
    text_insertions = []
    
    i = 0
    while i < len(content_lines):
        line = content_lines[i].strip()
        
        # TOO/APL/APLMM - Parse BeforeToKeep sections
        if line == '#BeforeToKeep':
            before_lines = []
            i += 1
            while i < len(content_lines) and content_lines[i].strip() != '#EndBeforeToKeep':
                before_lines.append(content_lines[i])
                i += 1
            # TOO/APL/APLMN - Filter out blank lines from context
            before_contexts.append(normalize_context_lines(before_lines))
        
        # TOO/APL/APLMO - Parse AfterToKeep sections
        elif line == '#AfterToKeep':
            after_lines = []
            i += 1
            while i < len(content_lines) and content_lines[i].strip() != '#EndAfterToKeep':
                after_lines.append(content_lines[i])
                i += 1
            # TOO/APL/APLMP - Filter out blank lines from context
            after_contexts.append(normalize_context_lines(after_lines))
        
        # TOO/APL/APLMQ - Parse TextToInsert sections
        elif line == '#TextToInsert':
            insert_lines = []
            i += 1
            while i < len(content_lines) and content_lines[i].strip() != '#EndTextToInsert':
                insert_lines.append(content_lines[i])
                i += 1
            text_insertions.append(insert_lines)
        
        i += 1
    
    return before_contexts, after_contexts, text_insertions

def find_context_in_file(file_content, before_context, after_context):
    """
    TOO/APL/APLNN - Find context markers in file content (ignoring blank lines)
    Args:
        file_content (str): Full file content
        before_context (list): Lines that should appear before target
        after_context (list): Lines that should appear after target
    Returns:
        tuple: (start_pos, end_pos) or (None, None) if not found
    """
    if not before_context or not after_context:
        return None, None
    
    # TOO/APL/APLOO - Normalize file content by removing blank lines for matching
    file_lines = file_content.split('\n')
    normalized_file_lines = normalize_context_lines(file_lines)
    
    # TOO/APL/APLPP - Convert contexts to normalized strings
    before_text_lines = normalize_context_lines(before_context)
    after_text_lines = normalize_context_lines(after_context)
    
    # TOO/APL/APLQQ - Find before context in normalized content
    before_found = False
    after_found = False
    before_original_start = -1
    after_original_end = -1
    
    # TOO/APL/APLRR - Search for before context
    for i in range(len(normalized_file_lines) - len(before_text_lines) + 1):
        match = True
        for j, line in enumerate(before_text_lines):
            if normalized_file_lines[i + j] != line:
                match = False
                break
        
        if match:
            # TOO/APL/APLSS - Find original position in file with blank lines
            before_original_start = 0
            normalized_count = 0
            for orig_line in file_lines:
                if orig_line.strip():  # Non-blank line
                    if normalized_count == i + len(before_text_lines):
                        break
                    normalized_count += 1
                before_original_start += len(orig_line) + 1  # +1 for newline
            before_found = True
            break
    
    if not before_found:
        return None, None
    
    # TOO/APL/APLTT - Search for after context starting from after before context
    search_start = i + len(before_text_lines)
    for i in range(search_start, len(normalized_file_lines) - len(after_text_lines) + 1):
        match = True
        for j, line in enumerate(after_text_lines):
            if normalized_file_lines[i + j] != line:
                match = False
                break
        
        if match:
            # TOO/APL/APLUU - Find original position for after context
            after_original_end = 0
            normalized_count = 0
            for orig_line in file_lines:
                if orig_line.strip():  # Non-blank line
                    if normalized_count == i:
                        break
                    normalized_count += 1
                after_original_end += len(orig_line) + 1  # +1 for newline
            after_found = True
            break
    
    if not after_found:
        return None, None
    
    return before_original_start, after_original_end

def execute_system_action(action):
    """
    TOO/APL/APLVV - Execute system commands
    Args:
        action (dict): Action configuration
    Returns:
        bool: Success status
    """
    try:
        # TOO/APL/APLWW - Get working directory
        work_dir = action['local_paths'][0] if action['local_paths'] else '.'
        work_path = Path(work_dir).resolve()
        
        print(f">> System commands in: {work_path}")
        
        # TOO/APL/APLXX - Execute each command
        for command_line in action['content']:
            command = command_line.strip()
            if not command:
                continue
                
            print(f"   Executing: {command}")
            
            # TOO/APL/APLYY - Run command with proper error handling
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=work_path,
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                print(f"   ERROR: Command failed (exit {result.returncode}): {command}")
                print(f"   STDERR: {result.stderr}")
                return False
            else:
                print(f"   SUCCESS: Command succeeded: {command}")
                if result.stdout.strip():
                    print(f"   Output: {result.stdout.strip()}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: System action failed: {e}")
        return False

def execute_delete_file_action(action):
    """
    TOO/APL/APLZZ - Delete files and directories
    Args:
        action (dict): Action configuration
    Returns:
        bool: Success status (warnings don't count as failures)
    """
    success = True
    
    # TOO/APL/APLAAA - Process each file/directory
    for file_path_str in action['local_paths']:
        try:
            file_path = Path(file_path_str)
            
            if not file_path.exists():
                print(f"WARNING: File not found (skipping): {file_path}")
                continue
            
            # TOO/APL/APLBBB - Delete file or directory
            if file_path.is_file():
                file_path.unlink()
                print(f">> Deleted file: {file_path}")
            elif file_path.is_dir():
                shutil.rmtree(file_path)
                print(f">> Deleted directory: {file_path}")
            else:
                print(f"WARNING: Unknown file type: {file_path}")
                
        except Exception as e:
            print(f"ERROR: Failed to delete {file_path_str}: {e}")
            success = False
    
    return success

def execute_create_file_action(action, backup_session_dir, backed_up_files):
    """
    TOO/APL/APLCCC - Create complete files
    Args:
        action (dict): Action configuration
        backup_session_dir (Path): Backup directory for session
        backed_up_files (set): Set of already backed up files
    Returns:
        bool: Success status
    """
    try:
        if not action['local_paths']:
            print("ERROR: CreateFile: No Local path specified")
            return False
        
        file_path = Path(action['local_paths'][0])
        
        # TOO/APL/APLDDD - Create backup if file exists and not already backed up
        if file_path.exists() and str(file_path) not in backed_up_files:
            if not create_backup(file_path, backup_session_dir):
                return False
            backed_up_files.add(str(file_path))
        
        # TOO/APL/APLEEE - Create directory structure
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # TOO/APL/APLFFF - Write file content
        content = '\n'.join(action['content'])
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        
        print(f">> Created file: {file_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: CreateFile failed: {e}")
        return False

def execute_delete_text_action(action, backup_session_dir, backed_up_files):
    """
    TOO/APL/APLGGG - Delete text between context markers
    Args:
        action (dict): Action configuration
        backup_session_dir (Path): Backup directory for session
        backed_up_files (set): Set of already backed up files
    Returns:
        bool: Success status
    """
    try:
        if not action['local_paths']:
            print("ERROR: DeleteText: No Local path specified")
            return False
        
        file_path = Path(action['local_paths'][0])
        
        if not file_path.exists():
            print(f"ERROR: DeleteText: File not found: {file_path}")
            return False
        
        # TOO/APL/APLHHH - Create backup if not already done
        if str(file_path) not in backed_up_files:
            if not create_backup(file_path, backup_session_dir):
                return False
            backed_up_files.add(str(file_path))
        
        # TOO/APL/APLIII - Read current file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                file_content = f.read()
        
        # TOO/APL/APLJJJ - Parse contexts using new format
        before_contexts, after_contexts, _ = parse_context_sections(action['content'])
        
        if not before_contexts or not after_contexts:
            print("ERROR: DeleteText: No valid context sections found")
            return False
        
        # TOO/APL/APLKKK - Find context positions
        start_pos, end_pos = find_context_in_file(
            file_content, 
            before_contexts[0], 
            after_contexts[0]
        )
        
        if start_pos is None or end_pos is None:
            print("ERROR: DeleteText: Context markers not found in file")
            print(f"   Before context: {before_contexts[0][:2] if before_contexts[0] else 'None'}...")
            print(f"   After context: {after_contexts[0][:2] if after_contexts[0] else 'None'}...")
            return False
        
        # TOO/APL/APLMMM - Remove content between contexts
        new_content = file_content[:start_pos] + file_content[end_pos:]
        
        # TOO/APL/APLNNN - Write modified file
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        
        print(f">> Deleted text from: {file_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: DeleteText failed: {e}")
        return False

def execute_insert_text_action(action, backup_session_dir, backed_up_files):
    """
    TOO/APL/APLOOO - Insert text between context markers
    Args:
        action (dict): Action configuration
        backup_session_dir (Path): Backup directory for session
        backed_up_files (set): Set of already backed up files
    Returns:
        bool: Success status
    """
    try:
        if not action['local_paths']:
            print("ERROR: InsertText: No Local path specified")
            return False
        
        file_path = Path(action['local_paths'][0])
        
        if not file_path.exists():
            print(f"ERROR: InsertText: File not found: {file_path}")
            return False
        
        # TOO/APL/APLPPP - Create backup if not already done
        if str(file_path) not in backed_up_files:
            if not create_backup(file_path, backup_session_dir):
                return False
            backed_up_files.add(str(file_path))
        
        # TOO/APL/APLQQQ - Read current file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                file_content = f.read()
        
        # TOO/APL/APLRRR - Parse contexts using new format
        before_contexts, after_contexts, text_insertions = parse_context_sections(action['content'])
        
        if not before_contexts or not after_contexts or not text_insertions:
            print("ERROR: InsertText: Missing required sections (BeforeToKeep, AfterToKeep, TextToInsert)")
            return False
        
        # TOO/APL/APLSSS - Find insertion point
        start_pos, end_pos = find_context_in_file(
            file_content, 
            before_contexts[0], 
            after_contexts[0]
        )
        
        if start_pos is None or end_pos is None:
            print("ERROR: InsertText: Context markers not found in file")
            print(f"   Before context: {before_contexts[0][:2] if before_contexts[0] else 'None'}...")
            print(f"   After context: {after_contexts[0][:2] if after_contexts[0] else 'None'}...")
            return False
        
        # TOO/APL/APLTTT - Insert new content between contexts
        text_to_insert = '\n'.join(text_insertions[0])
        new_content = file_content[:start_pos] + text_to_insert + file_content[end_pos:]
        
        # TOO/APL/APLUUU - Write modified file
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        
        print(f">> Inserted text into: {file_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: InsertText failed: {e}")
        return False

def execute_modify_text_action(action, backup_session_dir, backed_up_files):
    """
    TOO/APL/APLVVV - Replace text between context markers (supports multiple modifications)
    Args:
        action (dict): Action configuration
        backup_session_dir (Path): Backup directory for session
        backed_up_files (set): Set of already backed up files
    Returns:
        bool: Success status
    """
    try:
        if not action['local_paths']:
            print("ERROR: ModifyText: No Local path specified")
            return False
        
        file_path = Path(action['local_paths'][0])
        
        if not file_path.exists():
            print(f"ERROR: ModifyText: File not found: {file_path}")
            return False
        
        # TOO/APL/APLWWW - Create backup if not already done
        if str(file_path) not in backed_up_files:
            if not create_backup(file_path, backup_session_dir):
                return False
            backed_up_files.add(str(file_path))
        
        # TOO/APL/APLXXX - Read current file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                file_content = f.read()
        
        # TOO/APL/APLYYY - Parse multiple modifications from new format
        before_contexts, after_contexts, text_insertions = parse_context_sections(action['content'])
        
        if not before_contexts or not after_contexts or not text_insertions:
            print("ERROR: ModifyText: No valid modification sections found")
            return False
        
        if len(before_contexts) != len(after_contexts) or len(before_contexts) != len(text_insertions):
            print("ERROR: ModifyText: Mismatched number of context and insertion sections")
            return False
        
        print(f">> Processing {len(before_contexts)} modification(s) in: {file_path}")
        
        # TOO/APL/APLZZZ - Apply modifications in reverse order to preserve positions
        modified_content = file_content
        successful_modifications = 0
        modifications = list(zip(before_contexts, after_contexts, text_insertions))
        
        # TOO/APL/APLAAAA - Process modifications from end to start of file
        for i, (before_context, after_context, text_to_insert) in enumerate(reversed(modifications)):
            start_pos, end_pos = find_context_in_file(
                modified_content, 
                before_context, 
                after_context
            )
            
            if start_pos is None or end_pos is None:
                print(f"ERROR: ModifyText: Context markers not found for modification {len(modifications)-i}")
                print(f"   Before context: {before_context[:2] if before_context else 'None'}...")
                print(f"   After context: {after_context[:2] if after_context else 'None'}...")
                continue
            
            # TOO/APL/APLBBBB - Replace content between contexts
            replacement_text = '\n'.join(text_to_insert)
            modified_content = modified_content[:start_pos] + replacement_text + modified_content[end_pos:]
            successful_modifications += 1
            print(f"   SUCCESS: Applied modification {len(modifications)-i}/{len(modifications)}")
        
        if successful_modifications == 0:
            print("ERROR: ModifyText: No modifications could be applied")
            return False
        
        # TOO/APL/APLCCCC - Write modified file
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(modified_content)
        
        print(f">> Modified text in: {file_path} ({successful_modifications}/{len(modifications)} successful)")
        return successful_modifications == len(modifications)
        
    except Exception as e:
        print(f"ERROR: ModifyText failed: {e}")
        return False

def execute_action(action, backup_session_dir, backed_up_files):
    """
    TOO/APL/APLDDDD - Execute single action based on type
    Args:
        action (dict): Action configuration
        backup_session_dir (Path): Backup directory for session
        backed_up_files (set): Set of already backed up files
    Returns:
        bool: Success status
    """
    action_type = action['type']
    
    print(f"\n[Action {action_type}] Line {action['start_line']}")
    
    # TOO/APL/APLEEEE - Route to appropriate handler
    if action_type == 'System':
        return execute_system_action(action)
    elif action_type == 'DeleteFile':
        return execute_delete_file_action(action)
    elif action_type == 'CreateFile':
        return execute_create_file_action(action, backup_session_dir, backed_up_files)
    elif action_type == 'DeleteText':
        return execute_delete_text_action(action, backup_session_dir, backed_up_files)
    elif action_type == 'InsertText':
        return execute_insert_text_action(action, backup_session_dir, backed_up_files)
    elif action_type == 'ModifyText':
        return execute_modify_text_action(action, backup_session_dir, backed_up_files)
    else:
        print(f"ERROR: Unknown action type: {action_type}")
        return False

def main():
    """
    TOO/APL/APLFFFF - Main application entry point
    """
    # TOO/APL/APLGGGG - Parse command line arguments
    parser = argparse.ArgumentParser(description='Apply patches following PROTOCOL.md')
    parser.add_argument('--input', '-i', required=True, help='Patch file path')
    
    args = parser.parse_args()
    
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"ERROR: Patch file not found: {input_file}")
        sys.exit(1)
    
    # TOO/APL/APLHHHH - Read patch content with encoding fallback
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            patch_content = f.read()
    except UnicodeDecodeError:
        try:
            with open(input_file, 'r', encoding='latin-1') as f:
                patch_content = f.read()
        except Exception as e:
            print(f"ERROR: Cannot read patch file: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Error reading patch file: {e}")
        sys.exit(1)
    
    if not patch_content.strip():
        print("ERROR: Patch file is empty")
        sys.exit(1)
    
    # TOO/APL/APLIII - Setup session
    print(">> Starting patch application (PROTOCOL.md v2)")
    print(f">> Patch file: {input_file}")
    print("=" * 60)
    
    # TOO/APL/APLJJJJ - Create backup session directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_session_dir = Path(BACKUP_ROOT) / timestamp
    backup_session_dir.mkdir(parents=True, exist_ok=True)
    backed_up_files = set()  # Track files already backed up this session
    
    print(f">> Backup session: {backup_session_dir}")
    
    # TOO/APL/APLKKKK - Parse patch into actions
    actions = parse_patch_content(patch_content)
    
    if not actions:
        print("ERROR: No valid actions found in patch")
        print("INFO: Check PROTOCOL.md format:")
        print("   #Action [ActionType]")
        print("   [action content]")
        print("   #END Action [ActionType]")
        sys.exit(1)
    
    print(f">> Found {len(actions)} action(s)")
    
    # TOO/APL/APLLLLL - Execute all actions
    success_count = 0
    for i, action in enumerate(actions, 1):
        print(f"\n{'='*20} Action {i}/{len(actions)} {'='*20}")
        
        if execute_action(action, backup_session_dir, backed_up_files):
            success_count += 1
        else:
            print(f"ERROR: Action {i} failed - stopping execution")
            break
    
    # TOO/APL/APLMMMM - Final report
    print("\n" + "=" * 60)
    print(f">> Results: {success_count}/{len(actions)} actions successful")
    
    if success_count == len(actions):
        print("SUCCESS: All actions completed successfully!")
        print(f">> Backups available in: {backup_session_dir}")
        print("\n>> Recommended next steps:")
        print("   git add .")
        print("   git commit -m '[apply_changes] Applied patches via PROTOCOL.md'")
        print("   git push")
        
        return 0
    else:
        print("WARNING: Some actions failed - check errors above")
        print(f">> Partial backups available in: {backup_session_dir}")
        return 1

if __name__ == "__main__":
    # TOO/APL/APLNNNN - Application entry point
    sys.exit(main())