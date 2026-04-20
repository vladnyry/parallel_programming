#!/usr/bin/env python3
"""Генерация тестовых матриц для экспериментов."""

import random
import argparse
import os
import sys

def generate_matrix(size, filename, seed=None):
    """Генерирует матрицу size×size и сохраняет в файл."""
    if seed is not None:
        random.seed(seed)
    
    # Создаём директорию, если нужно
    dir_name = os.path.dirname(filename)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
    
    try:
        with open(filename, "w") as f:
            for i in range(size):
                row = [str(round(random.uniform(0, 10), 2)) for _ in range(size)]
                f.write(" ".join(row) + "\n")
        return True
    except Exception as e:
        print(f"Ошибка записи {filename}: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Генерация матриц")
    parser.add_argument("size", type=int, help="Размер матрицы (N×N)")
    parser.add_argument("--output_a", default="matrix_A.txt", help="Файл для матрицы A")
    parser.add_argument("--output_b", default="matrix_B.txt", help="Файл для матрицы B")
    parser.add_argument("--seed_a", type=int, default=42, help="Seed для A")
    parser.add_argument("--seed_b", type=int, default=123, help="Seed для B")
    
    args = parser.parse_args()
    
    print(f"📦 Генерация матриц {args.size}×{args.size}...", file=sys.stderr)
    
    success = True
    success &= generate_matrix(args.size, args.output_a, seed=args.seed_a)
    success &= generate_matrix(args.size, args.output_b, seed=args.seed_b)
    
    if success:
        print("✅ Готово!", file=sys.stderr)
        sys.exit(0)
    else:
        print("❌ Ошибка генерации!", file=sys.stderr)
        sys.exit(1)