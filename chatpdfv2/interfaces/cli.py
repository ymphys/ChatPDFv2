from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional, Sequence

from ..config import get_settings
from ..core import deepseek_interpretation
from ..logging import configure_logging
from ..services import process_pdf_via_mineru, process_local_files_via_mineru, process_urls_via_mineru, get_batch_results
from ..utils import read_md_content

QUESTIONS = [
    (
        "请用以下模板概括该文档，并将其中的占位符填入具体信息；若文中未提及某项，请写‘未说明’；"
        "若涉及到专业词汇，请在结尾处统一进行解释：[xxxx年]，[xx大学/研究机构]的[xx作者等]"
        "针对[研究问题]，采用[研究手段/方法]，对[研究对象或范围]进行了研究，并发现/得出[主要结论]。"
    )
]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process markdown documents or remote PDF files."
    )
    
    # Input source group
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--pdf-url",
        help="URL of the PDF to process with MinerU before analysis.",
    )
    input_group.add_argument(
        "--md-path",
        help="Path to an existing markdown file to process directly.",
    )
    input_group.add_argument(
        "--batch-dir",
        help="Directory containing PDF files to process in batch with MinerU.",
    )
    input_group.add_argument(
        "--batch-id",
        help="Batch ID to check status of previously submitted batch processing.",
    )
    input_group.add_argument(
        "--batch-urls-file",
        nargs="?",
        const="files/batch_urls.txt",
        help="Path to a text file containing URLs of PDF files to process in batch with MinerU (default: files/batch_urls.txt).",
    )
    
    parser.add_argument(
        "--mineru-timeout",
        type=int,
        default=600,
        help="Maximum seconds to wait for MinerU extraction to finish.",
    )
    parser.add_argument(
        "--model-version",
        default="vlm",
        help="MinerU model version to use (default: vlm).",
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="Temperature for DeepSeek model (default: 1.0).",
    )
    
    return parser.parse_args(args=argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_logging()
    logger = logging.getLogger("chatpdf")
    logger.info("Starting ChatPDFv2 CLI process")

    args = parse_args(argv)
    settings = get_settings()
    files_root = settings.files_root

    files_root.mkdir(parents=True, exist_ok=True)

    # Handle batch ID query
    if args.batch_id:
        if not settings.mineru_api_key:
            raise ValueError("MINERU_API_KEY environment variable is not set")
        logger.info("Querying batch results for batch_id: %s", args.batch_id)
        batch_results = get_batch_results(
            batch_id=args.batch_id,
            api_key=settings.mineru_api_key,
        )
        logger.info("Batch results: %s", batch_results)
        print(f"Batch {args.batch_id} status: {batch_results.get('status')}")
        print(f"Tasks: {len(batch_results.get('tasks', []))}")
        for task in batch_results.get('tasks', []):
            print(f"  - {task.get('file_name')}: {task.get('state')}")
        return 0

    # Handle batch file processing
    file_paths = []
    urls = []
    if args.batch_dir:
        if not settings.mineru_api_key:
            raise ValueError("MINERU_API_KEY environment variable is not set")
        batch_dir = Path(args.batch_dir)
        if not batch_dir.exists():
            raise FileNotFoundError(f"Batch directory not found: {batch_dir}")
        file_paths = list(batch_dir.glob("*.pdf"))
        if not file_paths:
            raise FileNotFoundError(f"No PDF files found in directory: {batch_dir}")
        logger.info("Processing %d PDF files from directory: %s", len(file_paths), batch_dir)
    
    elif args.batch_urls_file is not None:
        if not settings.mineru_api_key:
            raise ValueError("MINERU_API_KEY environment variable is not set")
        
        # Use the provided file path or default
        urls_file = Path(args.batch_urls_file)
        
        if not urls_file.exists():
            raise FileNotFoundError(f"URLs file not found: {urls_file}")
        
        # Read URLs from file
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not urls:
            raise ValueError(f"No valid URLs found in file: {urls_file}")
        
        logger.info("Processing %d URLs from file: %s", len(urls), urls_file)
    
    if file_paths:
        md_paths = process_local_files_via_mineru(
            file_paths=file_paths,
            output_root=files_root,
            api_key=settings.mineru_api_key,
            timeout_seconds=args.mineru_timeout,
            model_version=args.model_version,
        )
        logger.info("Batch processing completed. Generated %d markdown files", len(md_paths))
        for md_path in md_paths:
            logger.info("Processed: %s", md_path)
        
        # Process all markdown files for interpretation
        for md_path in md_paths:
            md_content = read_md_content(md_path)
            interpretation_output = md_path.parent / "interpretation_results.md"
            
            logger.info("Using DeepSeek for interpretation of %s", md_path.name)
            deepseek_interpretation(
                md_content,
                QUESTIONS,
                interpretation_output,
                temperature=args.temperature,
            )
        
        logger.info("ChatPDFv2 CLI process finished")
        return 0
    
    elif urls:
        md_paths = process_urls_via_mineru(
            urls=urls,
            output_root=files_root,
            api_key=settings.mineru_api_key,
            timeout_seconds=args.mineru_timeout,
            model_version=args.model_version,
        )
        logger.info("URL batch processing completed. Generated %d markdown files", len(md_paths))
        for md_path in md_paths:
            logger.info("Processed: %s", md_path)
        
        # Process all markdown files for interpretation
        for md_path in md_paths:
            md_content = read_md_content(md_path)
            interpretation_output = md_path.parent / "interpretation_results.md"
            
            logger.info("Using DeepSeek for interpretation of %s", md_path.name)
            deepseek_interpretation(
                md_content,
                QUESTIONS,
                interpretation_output,
                temperature=args.temperature,
            )
        
        logger.info("ChatPDFv2 CLI process finished")
        return 0
    
    # Handle single file processing
    elif args.pdf_url:
        if not settings.mineru_api_key:
            raise ValueError("MINERU_API_KEY environment variable is not set")
        md_path = process_pdf_via_mineru(
            args.pdf_url,
            output_root=files_root,
            api_key=settings.mineru_api_key,
            timeout_seconds=args.mineru_timeout,
        )
    elif args.md_path:
        md_path = Path(args.md_path)
    else:
        md_path = settings.default_md_path

    # Process markdown content with DeepSeek interpretation
    md_content = read_md_content(md_path)
    interpretation_output = md_path.parent / "interpretation_results.md"

    logger.info("Using DeepSeek for interpretation")
    deepseek_interpretation(
        md_content,
        QUESTIONS,
        interpretation_output,
        temperature=args.temperature,
    )
    logger.info("ChatPDFv2 CLI process finished")
    return 0


__all__ = ["main", "parse_args"]
