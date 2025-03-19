"""
Core module for Clony.

This module contains the core functionality for the Clony Git clone tool.
"""

# Local imports
from clony.core.diff import (
    diff_blobs,
    generate_unified_diff,
    myers_diff,
    print_diff,
    read_git_object,
)
from clony.core.objects import (
    calculate_sha1_hash,
    compress_content,
    create_blob_object,
    create_commit_object,
    create_tree_object,
    write_object_file,
)
from clony.core.refs import (
    get_current_branch,
    get_head_commit,
    get_head_ref,
    get_ref_hash,
    update_ref,
)
from clony.core.repository import Repository

# Export the core functionality
__all__ = [
    "calculate_sha1_hash",
    "compress_content",
    "create_blob_object",
    "create_commit_object",
    "create_tree_object",
    "write_object_file",
    "get_current_branch",
    "get_head_commit",
    "get_head_ref",
    "get_ref_hash",
    "update_ref",
    "Repository",
    "diff_blobs",
    "generate_unified_diff",
    "myers_diff",
    "print_diff",
    "read_git_object",
]
